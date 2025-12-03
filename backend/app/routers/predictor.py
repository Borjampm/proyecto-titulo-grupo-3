from datetime import datetime
from pathlib import Path
from typing import List
import re

import pandas as pd
from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import SessionLocal
from app.models.clinical_episode import ClinicalEpisode, EpisodeStatus
from app.models.patient import Patient
from app.models.alert import Alert, AlertType, AlertSeverity

router = APIRouter()


def extract_complication_from_text(text: str) -> str:
    if text is None:
        return 0
    s = str(text).upper()
    if re.search(r"W\/MCC", s):
        return 1
    if re.search(r"W\/CC", s):
        return 1
    return 0

def parse_grd_code(code):
    """
    Recibe código (p. ej. '084212' o 8412), devuelve (cdm, tipo_digit, grd_num, sev_digit)
    Devuelve None si no puede parsear.
    """
    if code is None:
        return (None, None, None, None)
    s = str(code).strip()
    # Mantener solo dígitos
    s_digits = "".join(ch for ch in s if ch.isdigit())
    if len(s_digits) < 5:
        s_digits = s_digits.zfill(6)  # pad left if shorter
    # Ahora:
    cdm = s_digits[0:2]
    tipo_digit = s_digits[2:3]
    grd_num = s_digits[3:5]
    sev_digit = s_digits[5:6] if len(s_digits) >= 6 else None
    return (cdm, tipo_digit, grd_num, sev_digit)


def _compute_age_years(birth_date: datetime, ref_dt: datetime) -> float:
	if not birth_date:
		return None
	try:
		delta_days = (ref_dt.date() - birth_date).days
		return round(delta_days / 365.25, 2)
	except Exception:
		return None
	
def parse_type(type: str):
	if type == "Urgencias":
		return "Urgente"
	else:
		return "Programado"
	



@router.post("/predict-overstay")
async def predict_overstay() -> dict:
	"""Run CatBoost model and store overstay probability for active episodes missing it.

	Skips episodes missing required features for the model.
	"""
	# Load model
	try:
		from catboost import CatBoostClassifier, Pool
	except Exception as e:
		return {"error": f"CatBoost not available: {e}"}

	model_path = Path(__file__).resolve().parents[2] / "catboost_grd.cbm"
	if not model_path.exists():
		return {"error": f"Model file not found at {model_path}"}

	model = CatBoostClassifier()
	try:
		model.load_model(str(model_path))
	except Exception as e:
		return {"error": f"Failed to load model: {e}"}

	# Fetch episodes
	async with SessionLocal() as session:  # type: AsyncSession
		stmt = (
			select(ClinicalEpisode, Patient)
			.join(Patient, ClinicalEpisode.patient_id == Patient.id)
			.where(
				ClinicalEpisode.status == EpisodeStatus.ACTIVE,
				ClinicalEpisode.overstay_probability.is_(None),
			)
		)
		res = await session.execute(stmt)
		rows: List[tuple[ClinicalEpisode, Patient]] = res.all()

		prepared = []
		targets = []

		for episode, patient in rows:
			# Required fields: GRD name/id, expected days, age
			grd_name = episode.grd_name
			grd_id = episode.grd_id
			grd_expected_days = episode.grd_expected_days
			age_years = _compute_age_years(patient.birth_date, episode.admission_at or datetime.utcnow())
			(cdm, tipo_digit, grd_num, sev_digit) = parse_grd_code(grd_id)

			# Also require core categorical descriptors to be present
			if grd_expected_days is None or age_years is None or (grd_name is None and grd_id is None):
				# skip missing required
				continue
			if episode.prevision_desc is None or episode.tipo_ingreso_desc is None or episode.servicio_ingreso_desc is None:
				continue
	

			prepared.append({
				"complication":str(extract_complication_from_text(grd_name)),
				"Prevision (Desc)": str(episode.prevision_desc),
				"Estancia Norma GRD ": int(grd_expected_days),
				"IR GRD (Código)": str(grd_id),
				"Edad en años": float(age_years),
				"Tipo Ingreso (Descripción)": parse_type(episode.tipo_ingreso_desc),
				"Servicio Ingreso (Descripción)": str(episode.servicio_ingreso_desc),
				'CDM_derived': str(cdm),
                'GRD_num_derived':  str(grd_num),
                'sev_digit': str(sev_digit),
                'tipo_from_code': str(tipo_digit),
			})
			targets.append(episode)

		if not prepared:
			return {"predicted": 0, "skipped": len(rows), "updated": 0}

		# Ensure categorical features are strings and numeric are floats
		df = pd.DataFrame(prepared)
		cat_cols = [
			"IR GRD",
			"Prevision (Desc)",
			"IR GRD (Código)",
			"Tipo Ingreso (Descripción)",
			"Servicio Ingreso (Descripción)",
			"complication",
			"CDM_derived",
			"GRD_num_derived",
			"sev_digit",
			"tipo_from_code",
		]
		num_cols = [
			"Estancia Norma GRD ",
			"Edad en años",
		]
		for c in cat_cols:
			if c in df.columns:
				df[c] = df[c].apply(lambda v: "" if v is None else str(v))
		for c in num_cols:
			if c in df.columns:
				df[c] = pd.to_numeric(df[c], errors="coerce")

		try:
			# Declare categorical feature indices for CatBoost
			cat_feature_indices = [df.columns.get_loc(c) for c in cat_cols if c in df.columns]
			pool = Pool(df, cat_features=cat_feature_indices)
			probs = model.predict_proba(pool)
		except Exception:
			# Try direct dataframe if Pool fails
			probs = model.predict_proba(df)

		# CatBoost returns [p0, p1]; overstay probability assumed class 1
		# Persist via bulk UPDATE to avoid any ORM tracking edge-cases
		from sqlalchemy import update
		import numpy as np
		
		updated = 0
		updates = []
		for i, ep in enumerate(targets):
			try:
				pr = probs[i]
				# Handle various predict_proba output formats
				if isinstance(pr, (list, tuple)):
					if len(pr) >= 2:
						p1 = float(pr[1])
					else:
						p1 = float(pr[0])
				elif isinstance(pr, np.ndarray):
					if pr.ndim == 0:
						p1 = float(pr)
					elif pr.ndim == 1:
						p1 = float(pr[1] if pr.shape[0] >= 2 else pr[0])
					else:
						flat = pr.flatten()
						p1 = float(flat[1] if flat.size >= 2 else flat[0])
				else:
					p1 = float(pr)
				updates.append((ep.id, p1))
			except Exception as e:
				continue
		
		if updates:
			for ep_id, pval in updates:
				stmt_upd = (
					update(ClinicalEpisode)
					.where(ClinicalEpisode.id == ep_id)
					.values(overstay_probability=pval)
				)
				await session.execute(stmt_upd)
				updated += 1
				
				# Create predicted-overstay alert if probability >= 0.5
				if pval >= 0.5:
					# Determine severity based on probability
					if pval >= 0.7:
						severity = AlertSeverity.HIGH
					else:  # 0.5 <= pval < 0.7
						severity = AlertSeverity.MEDIUM
					
					# Format probability as percentage
					prob_percent = int(pval * 100)
					
					alert = Alert(
						episode_id=ep_id,
						alert_type=AlertType.PREDICTED_OVERSTAY,
						severity=severity,
						message=f"Predicción de sobrestadía: {prob_percent}% probabilidad",
						is_active=True,
						created_by="Sistema (modelo predictivo)"
					)
					session.add(alert)
			await session.commit()

		# Verify the update worked
		stmt_check = select(ClinicalEpisode).where(ClinicalEpisode.overstay_probability.is_not(None))
		res_check = await session.execute(stmt_check)
		check_count = len(res_check.scalars().all())

		return {
			"predicted": len(prepared),
			"skipped": len(rows) - len(prepared),
			"updated": updated,
			"db_rows_with_probability": check_count,
		}
