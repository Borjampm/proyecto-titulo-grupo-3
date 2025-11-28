"""
Excel data uploader for populating the database with patient and bed information.

This module handles uploading data from Excel files:
- "Camas NWP1 24-09-2025 1235.xlsx" -> beds table
- "Score Social.xlsx" -> patients, patient_information, clinical_episodes, and clinical_episode_information tables
"""

import asyncio
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import unicodedata
import re

from app.db import SessionLocal
from app.models.bed import Bed
from app.models.patient import Patient
from app.models.patient_information import PatientInformation
from app.models.clinical_episode import ClinicalEpisode, EpisodeStatus
from app.models.clinical_episode_information import (
    ClinicalEpisodeInformation,
    EpisodeInfoType,
)
from app.models.social_score_history import SocialScoreHistory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Names for realistic placeholder data
FIRST_NAMES = [
    "María", "José", "Carlos", "Juan", "Pedro", "Luis", "Francisco", "Jorge", 
    "Manuel", "Antonio", "Alejandro", "Roberto", "Miguel", "Ricardo", "Andrés",
    "Pablo", "Sergio", "Fernando", "Diego", "Gabriel", "Cristián", "Rodrigo",
    "Marcelo", "Daniel", "Felipe", "Jaime", "Claudio", "Eduardo", "Mauricio",
    "Raúl", "Carmen", "Ana", "Rosa", "Isabel", "Patricia", "Gloria", "Lucía",
    "Teresa", "Marta", "Silvia", "Elena", "Verónica", "Claudia", "Carolina",
    "Francisca", "Javiera", "Camila", "Daniela", "Valentina", "Constanza"
]

LAST_NAMES = [
    "González", "Muñoz", "Rodríguez", "García", "Martínez", "López", "Hernández",
    "Pérez", "Fernández", "Sánchez", "Ramírez", "Torres", "Flores", "Rivera",
    "Gómez", "Díaz", "Contreras", "Rojas", "Silva", "Sepúlveda", "Morales",
    "Vargas", "Castillo", "Núñez", "Guzmán", "Vega", "Reyes", "Espinoza",
    "Jara", "Figueroa", "Álvarez", "Poblete", "Valdés", "Navarro", "Campos"
]


def calculate_rut_verifier(rut_number: int) -> str:
    """
    Calculate the verification digit for a RUT.
    
    Args:
        rut_number: The RUT number without verification digit
        
    Returns:
        The verification digit (0-9 or K)
    """
    multiplier = 2
    sum_value = 0
    
    while rut_number > 0:
        sum_value += (rut_number % 10) * multiplier
        rut_number //= 10
        multiplier += 1
        if multiplier > 7:
            multiplier = 2
    
    remainder = sum_value % 11
    verifier = 11 - remainder
    
    if verifier == 11:
        return "0"
    elif verifier == 10:
        return "K"
    else:
        return str(verifier)


def generate_rut(seed: str) -> str:
    """
    Generate a valid RUT based on a seed string.
    
    Args:
        seed: A string to generate consistent RUT (e.g., episode ID)
        
    Returns:
        A valid RUT in format "XX.XXX.XXX-X"
    """
    # Generate a number from seed (between 5,000,000 and 25,000,000 for realistic RUTs)
    seed_hash = hash(seed)
    rut_number = 5000000 + (abs(seed_hash) % 20000000)
    
    # Calculate verification digit
    verifier = calculate_rut_verifier(rut_number)
    
    # Format with dots and dash
    rut_str = f"{rut_number:,}".replace(",", ".")
    return f"{rut_str}-{verifier}"


def get_name(seed: str) -> tuple[str, str]:
    """
    Get a consistent name based on a seed string.
    
    Args:
        seed: A string to generate consistent name (e.g., episode ID)
        
    Returns:
        Tuple of (first_name, last_name)
    """
    seed_hash = abs(hash(seed))
    first_name_idx = seed_hash % len(FIRST_NAMES)
    last_name_idx = (seed_hash // len(FIRST_NAMES)) % len(LAST_NAMES)
    
    first_name = FIRST_NAMES[first_name_idx]
    last_name = LAST_NAMES[last_name_idx]
    
    return first_name, last_name


class ExcelUploader:
    """Handles uploading data from Excel files to the database."""

    def __init__(self, db_session: AsyncSession):
        self.db = db_session

    def _normalize_col_name(self, col_name: str) -> str:
        """Normalize a column name for matching: remove accents/punctuation, collapse whitespace, lower-case."""
        if not isinstance(col_name, str):
            col_name = str(col_name)

        s = col_name.replace("\xa0", " ")
        s = unicodedata.normalize("NFKD", s)
        # remove diacritics
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        # keep alphanumerics and spaces
        s = re.sub(r"[^0-9A-Za-z\s]", " ", s)
        s = re.sub(r"\s+", " ", s).strip().lower()
        return s

    # ==================== BED DATA UPLOAD ====================

    async def upload_beds_from_excel(self, excel_path: str | Path) -> int:
        """
        Upload bed data from "Camas" sheet in the Excel file.

        Args:
            excel_path: Path to the "Camas NWP1 24-09-2025 1235.xlsx" file

        Returns:
            Number of beds uploaded
        """
        logger.info(f"Reading beds data from {excel_path}")

        try:
            df = pd.read_excel(excel_path, sheet_name="Camas")
            logger.info(f"Found {len(df)} rows in Camas sheet")

            beds_created = 0

            for idx, row in df.iterrows():
                try:
                    bed_data = self._parse_bed_row(row)
                    if bed_data:
                        await self._create_or_update_bed(bed_data)
                        beds_created += 1
                except Exception as e:
                    logger.error(f"Error processing bed row {idx}: {e}")
                    continue

            await self.db.commit()
            logger.info(f"Successfully uploaded {beds_created} beds")
            return beds_created

        except Exception as e:
            logger.error(f"Error uploading beds: {e}")
            await self.db.rollback()
            raise

    def _parse_bed_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Parse a bed row from the Excel file.

        Expected columns from "Camas NWP1 24-09-2025 1235.xlsx":
        - CAMA: Bed/room identifier
        - CAMA_BLOQUEADA: Whether bed is blocked/unavailable
        - HABITACION: Room number (used as identifier)
        
        Missing data is allowed and will use defaults.
        """
        try:
            # Use CAMA as the room identifier, fallback to HABITACION if not available
            room_raw = row.get("CAMA")
            if pd.isna(room_raw) or str(room_raw).strip() == "":
                # Try CAMA as fallback
                room_raw = row.get("HABITACION")
            
            room = str(room_raw).strip() if not pd.isna(room_raw) else ""
            
            # Only skip if room is completely empty or 'nan'
            if not room or room == "" or room.lower() == "nan":
                logger.warning(f"Skipping row with missing room/bed information")
                return None

            # Parse blocked status - if CAMA_BLOQUEADA exists, use it
            # Blocked bed = not available
            blocked_raw = row.get("CAMA_BLOQUEADA")
            if pd.isna(blocked_raw):
                # Default: bed is not blocked (is available)
                available = True
            else:
                # If CAMA_BLOQUEADA has any value, bed is blocked (not available)
                blocked_str = str(blocked_raw).strip().upper()
                # Check if it's actually blocked (not empty, not "NO", etc.)
                available = blocked_str in ["", "NO", "N", "FALSE", "0"]

            # Active status - default to True
            # You can add logic here if there's a field indicating inactive beds
            active = True

            return {
                "room": room,
                "active": active,
                "available": available,
            }

        except Exception as e:
            logger.error(f"Error parsing bed row: {e}")
            return None

    async def _create_or_update_bed(self, bed_data: Dict[str, Any]) -> Bed:
        """Create or update a bed in the database."""
        # Check if bed with this room already exists
        stmt = select(Bed).where(Bed.room == bed_data["room"])
        result = await self.db.execute(stmt)
        existing_bed = result.scalar_one_or_none()

        if existing_bed:
            # Update existing bed
            existing_bed.active = bed_data["active"]
            existing_bed.available = bed_data["available"]
            logger.info(f"Updated bed: {bed_data['room']}")
            return existing_bed
        else:
            # Create new bed
            bed = Bed(**bed_data)
            self.db.add(bed)
            logger.info(f"Created bed: {bed_data['room']}")
            return bed

    # ==================== PATIENT DATA UPLOAD ====================

    async def upload_patients_from_excel(self, excel_path: str | Path) -> int:
        """
        Upload patient data from "Data Casos" sheet in the Score Social Excel file.

        This method creates:
        - Patients
        - Patient Information
        - Clinical Episodes
        - Clinical Episode Information

        Args:
            excel_path: Path to the "Score Social.xlsx" file

        Returns:
            Number of patients uploaded
        """
        logger.info(f"Reading patient data from {excel_path}")

        try:
            df = pd.read_excel(excel_path, sheet_name="Data Casos")
            logger.info(f"Found {len(df)} rows in Data Casos sheet")

            patients_created = 0

            for idx, row in df.iterrows():
                try:
                    await self._process_patient_row(row, idx)
                    patients_created += 1
                except Exception as e:
                    logger.error(f"Error processing patient row {idx}: {e}")
                    continue

            await self.db.commit()
            logger.info(f"Successfully uploaded {patients_created} patients")
            return patients_created

        except Exception as e:
            logger.error(f"Error uploading patients: {e}")
            await self.db.rollback()
            raise

    # ==================== GESTION ESTADÍA (UCCC) UPLOAD ====================

    async def upload_gestion_estadia_from_excel(self, excel_path: str | Path) -> int:
        """
        Upload patient and episode data from the "UCCC" sheet in the Gestion Estadía Excel file.

        Args:
            excel_path: Path to the Gestion Estadía file

        Returns:
            Number of rows processed (patients/episodes)
        """
        logger.info(f"Reading Gestion Estadía data from {excel_path}")

        try:
            # Read the sheet and detect the true header row (some files have title rows above header)
            raw = pd.read_excel(excel_path, sheet_name="UCCC", header=None)

            def _detect_header_row(df_raw, max_scan=20, min_tokens=3):
                tokens = ["rut", "nombre", "episodio", "cama", "fecha", "sexo", "inicio", "nacimiento", "hora"]
                scan_rows = min(max_scan, len(df_raw))
                for i in range(scan_rows):
                    row = df_raw.iloc[i].fillna("").astype(str).str.lower().tolist()
                    found = set()
                    for cell in row:
                        for t in tokens:
                            if t in cell:
                                found.add(t)
                    if len(found) >= min_tokens:
                        return i
                return None

            header_idx = _detect_header_row(raw)
            if header_idx is None:
                logger.info("Could not detect header row automatically; using pandas default header (row 0).")
                df = pd.read_excel(excel_path, sheet_name="UCCC")
            else:
                logger.info(f"Detected header row at index: {header_idx}. Re-reading UCCC sheet using that header.")
                df = pd.read_excel(excel_path, sheet_name="UCCC", header=header_idx)

            # Trim whitespace in original column names
            df.columns = df.columns.map(lambda c: c if not isinstance(c, str) else c.strip())

            # Build normalized->original map for flexible lookup
            col_map = {}
            for col in df.columns:
                if isinstance(col, str):
                    norm = self._normalize_col_name(col) if hasattr(self, '_normalize_col_name') else col.strip().lower()
                    col_map[norm] = col

            # Try to map common UCCC column variants to canonical names used by the importer
            canonical_candidates = {
                "RUT": ["RUT", "rut"],
                "Nombre": ["Nombre", "nombre"],
                "Episodio:": ["Episodio:", "Episodio", "Episodio / Estadía", "episodio"],
                "CAMA": ["CAMA", "Cama"],
                "Fecha de Nacimiento": ["Fecha de Nacimiento", "Fecha de nacimiento", "fecha de nacimiento"],
                "Sexo": ["Sexo", "sexo"],
                "Fecha Inicio:": ["Fecha Inicio:", "Fecha Inicio", "Fecha de Inicio", "fecha inicio"],
                "Hora Inicio:": ["Hora Inicio:", "Hora Inicio", "Hora de Inicio", "hora inicio"],
                "Texto libre diagnóstico admisión": ["Texto libre diagnóstico admisión", "Texto libre diagnostico admision"],
                "OTROS DIAGNOSTICOS": ["OTROS DIAGNOSTICOS", "Otros Diagnosticos"],
                "TRATAMIENTO": ["TRATAMIENTO", "Tratamiento"],
                "FRECUENCIA": ["FRECUENCIA", "Frecuencia"],
                "ACCESO VASCULAR": ["ACCESO VASCULAR", "Acceso Vascular"],
                "CAUSA RECHAZO": ["CAUSA RECHAZO", "Causa Rechazo"],
                "TEXTO LIBRE CAUSA": ["TEXTO LIBRE CAUSA", "Texto libre causa"],
                "Motivos Rechazo": ["Motivos Rechazo", "Motivos rechazo"],
                "Motivos Devolución": ["Motivos Devolución", "Motivos Devolucion"],
                # metadata
                "Control": ["Control"],
                "Marco Temporal": ["Marco Temporal"],
                "Modificación": ["Modificación", "Modificacion"],
                "Informe": ["Informe"],
                "Gestionado en UCCC?": ["Gestionado en UCCC?", "Gestionado en UCCC"],
                "EDAD": ["EDAD", "Edad"],
                "Nombre de la aseguradora": ["Nombre de la aseguradora", "Nombre de la aseguradora"],
                "Convenio": ["Convenio"],
                "DIRECCIÓN": ["DIRECCIÓN", "DIRECCION", "Direccion"],
                "TELÉFONO": ["TELÉFONO", "TELEFONO", "Telefono"],
            }

            def find_orig(col_map, candidates):
                for c in candidates:
                    norm = self._normalize_col_name(c) if hasattr(self, '_normalize_col_name') else c.strip().lower()
                    if norm in col_map:
                        return col_map[norm]
                # try startswith match
                for c in candidates:
                    norm = self._normalize_col_name(c) if hasattr(self, '_normalize_col_name') else c.strip().lower()
                    for k, v in col_map.items():
                        if k.startswith(norm) or norm.startswith(k):
                            return v
                return None

            rename_map = {}
            for canonical, candidates in canonical_candidates.items():
                orig = find_orig(col_map, candidates)
                if orig:
                    # only rename if original column exists
                    rename_map[orig] = canonical

            if rename_map:
                df = df.rename(columns=rename_map)

            # expose the normalized map for downstream helpers
            self._gestion_col_map = col_map

            logger.info(f"Found {len(df)} rows in UCCC sheet; columns: {list(df.columns)}")

            processed = 0

            for idx, row in df.iterrows():
                try:
                    await self._process_gestion_row(row, idx)
                    processed += 1
                except Exception as e:
                    logger.error(f"Error processing UCCC row {idx}: {e}")
                    continue

            # After processing the UCCC sheet, also try to process discharge records
            # from the ALTAS sheet in the same file so episodes get their discharge timestamps.
            try:
                await self._process_altas_sheet(excel_path)
            except Exception as e:
                logger.warning(f"Processing ALTAS sheet failed or not present: {e}")

            await self.db.commit()
            logger.info(f"Successfully processed {processed} UCCC rows (and applied ALTAS updates)")
            return processed

        except Exception as e:
            logger.error(f"Error uploading Gestion Estadía: {e}")
            await self.db.rollback()
            raise

    async def _process_gestion_row(self, row: pd.Series, row_idx: int) -> None:
        """Process a single row from the Gestion Estadía (UCCC) sheet."""
        # Parse patient data (RUT is used as medical_identifier)
        patient_data = self._parse_gestion_patient_data(row)
        if not patient_data:
            return

        patient = await self._create_or_get_patient(patient_data)

        # Patient information: include address, phone, insurer, convenio, etc.
        patient_info = self._parse_patient_information(row)
        if patient_info:
            await self._create_or_update_patient_information(patient.id, patient_info)

        # Parse episode data (admission, discharge, bed)
        episode_data = self._parse_gestion_episode_data(row)
        episode = await self._create_clinical_episode(patient.id, episode_data)

        # Episode information: diagnosis, treatment, rejections, motives, etc.
        episode_info_records = []

        # Texto libre diagnóstico admisión
        diag = row.get("Texto libre diagnóstico admisión")
        if not pd.isna(diag) and str(diag).strip().lower() != 'nan':
            episode_info_records.append({
                "info_type": EpisodeInfoType.DIAGNOSIS,
                "title": "Diagnóstico de Admisión",
                "value": {"diagnosis": str(diag).strip()},
            })

        # Otros diagnósticos
        otros = row.get("OTROS DIAGNOSTICOS")
        if not pd.isna(otros) and str(otros).strip().lower() != 'nan':
            episode_info_records.append({
                "info_type": EpisodeInfoType.OTHER,
                "title": "Otros Diagnósticos",
                "value": {"otros_diagnosticos": str(otros).strip()},
            })

        # Tratamiento / Frecuencia / Acceso vascular
        tratamiento = row.get("TRATAMIENTO")
        frecuencia = row.get("FRECUENCIA")
        acceso = row.get("ACCESO VASCULAR")
        if (not pd.isna(tratamiento) and str(tratamiento).strip().lower() != 'nan') or \
           (not pd.isna(frecuencia) and str(frecuencia).strip().lower() != 'nan') or \
           (not pd.isna(acceso) and str(acceso).strip().lower() != 'nan'):
            episode_info_records.append({
                "info_type": EpisodeInfoType.OTHER,
                "title": "Tratamiento y Acceso",
                "value": {
                    "tratamiento": str(tratamiento).strip() if not pd.isna(tratamiento) else None,
                    "frecuencia": str(frecuencia).strip() if not pd.isna(frecuencia) else None,
                    "acceso_vascular": str(acceso).strip() if not pd.isna(acceso) else None,
                },
            })

        # Rejection reasons / Motivos
        causa_rechazo = row.get("CAUSA RECHAZO") or row.get("TEXTO LIBRE CAUSA")
        motivos_rechazo = row.get("Motivos Rechazo")
        motivos_devolucion = row.get("Motivos Devolución")
        if (not pd.isna(causa_rechazo) and str(causa_rechazo).strip().lower() != 'nan') or \
           (not pd.isna(motivos_rechazo) and str(motivos_rechazo).strip().lower() != 'nan') or \
           (not pd.isna(motivos_devolucion) and str(motivos_devolucion).strip().lower() != 'nan'):
            episode_info_records.append({
                "info_type": EpisodeInfoType.OTHER,
                "title": "Rechazos y Devoluciones",
                "value": {
                    "causa_rechazo": str(causa_rechazo).strip() if not pd.isna(causa_rechazo) else None,
                    "motivos_rechazo": str(motivos_rechazo).strip() if not pd.isna(motivos_rechazo) else None,
                    "motivos_devolucion": str(motivos_devolucion).strip() if not pd.isna(motivos_devolucion) else None,
                },
            })

        # Add any additional useful columns as OTHER records
        extras = [
            "Control", "Marco Temporal", "Modificación", "Informe", "Gestionado en UCCC?",
            "EDAD", "Nombre de la aseguradora", "Convenio", "DIRECCIÓN", "TELÉFONO"
        ]
        extra_values = {}
        for col in extras:
            if col in row.index:
                val = row.get(col)
                if not pd.isna(val) and str(val).strip().lower() != 'nan':
                    extra_values[col] = str(val).strip()

        if extra_values:
            episode_info_records.append({
                "info_type": EpisodeInfoType.OTHER,
                "title": "Metadatos UCCC",
                "value": extra_values,
            })

        # Persist episode info records
        for info in episode_info_records:
            await self._create_clinical_episode_information(episode.id, info)

        logger.info(f"Processed UCCC patient {patient.medical_identifier} row {row_idx}")

    def _parse_gestion_patient_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """Parse patient basic data from Gestion Estadía (UCCC) row.

        Uses RUT column as `medical_identifier`. If RUT missing, generate a placeholder RUT
        using the episode column as seed so data remains consistent across runs.
        """
        try:
            # Ensure column names trimmed
            # Use RUT as medical identifier
            rut_raw = row.get("RUT")

            episodio_raw = row.get("Episodio:") or row.get("Episodio") or row.get("Episodio / Estadía")
            episodio_str = str(episodio_raw).strip() if not pd.isna(episodio_raw) else None

            if pd.isna(rut_raw) or str(rut_raw).strip() == "" or str(rut_raw).strip().lower() == "nan":
                # Generate rut if missing, using episodio as seed if available
                seed = episodio_str or str(uuid4())
                rut = generate_rut(seed)
                medical_identifier = rut
            else:
                rut = str(rut_raw).strip()
                medical_identifier = rut

            # Nombre
            nombre_raw = row.get("Nombre")
            if pd.isna(nombre_raw) or str(nombre_raw).strip() == "" or str(nombre_raw).strip().lower() == "nan":
                # Use episode seed for consistent placeholder name
                seed = episodio_str or medical_identifier
                first_name, last_name = get_name(seed)
            else:
                nombre = str(nombre_raw).strip()
                name_parts = nombre.split(None, 1)
                if len(name_parts) >= 2:
                    first_name, last_name = name_parts[0], name_parts[1]
                else:
                    first_name, last_name = nombre, ""

            # Birth date - normalize and try explicit formats (DD-MM-YYYY, DD-MM-YY) then day-first autodetect
            birth_date_raw = row.get("Fecha de Nacimiento") or row.get("Fecha de Nacimiento ")
            birth_date = date(1970, 1, 1)
            try:
                if pd.isna(birth_date_raw):
                    birth_date = date(1970, 1, 1)
                elif isinstance(birth_date_raw, pd.Timestamp):
                    birth_date = birth_date_raw.date()
                elif isinstance(birth_date_raw, date):
                    birth_date = birth_date_raw
                else:
                    # Clean string: remove non-breaking spaces and control chars
                    s = str(birth_date_raw).strip()
                    s = s.replace("\xa0", " ").strip()

                    # Try explicit formats
                    dt = None
                    try:
                        dt = pd.to_datetime(s, format='%d-%m-%Y', dayfirst=True, errors='coerce')
                    except:
                        dt = None

                    if dt is None or pd.isna(dt):
                        try:
                            dt = pd.to_datetime(s, format='%d-%m-%y', dayfirst=True, errors='coerce')
                        except:
                            dt = None

                    if dt is None or pd.isna(dt):
                        try:
                            dt = pd.to_datetime(s, dayfirst=True, errors='coerce')
                        except:
                            dt = None

                    if dt is not None and not pd.isna(dt):
                        birth_date = dt.date()
                    else:
                        birth_date = date(1970, 1, 1)
            except Exception:
                birth_date = date(1970, 1, 1)

            # Sex (robust mapping: accepts 'Masculino', 'Mas', 'M', 'Hombre', 'Femenino', 'Fem', 'F', 'Mujer')
            sexo_raw = row.get("Sexo")
            gender = "Desconocido"
            try:
                if not pd.isna(sexo_raw):
                    s = str(sexo_raw).strip()
                    # Normalize unicode (remove accents) and uppercase
                    s_norm = unicodedata.normalize('NFKD', s).encode('ascii', errors='ignore').decode('ascii').upper()

                    masculine_tokens = ("M", "MAS", "MASCULINO", "H", "HOM", "HOMBRE")
                    feminine_tokens = ("F", "FEM", "FEMENINO", "MUJ", "MUJER")

                    if any(s_norm == t or s_norm.startswith(t) for t in masculine_tokens):
                        gender = "Masculino"
                    elif any(s_norm == t or s_norm.startswith(t) for t in feminine_tokens):
                        gender = "Femenino"
                    else:
                        gender = s.title()
            except Exception:
                gender = "Desconocido"

            return {
                "medical_identifier": medical_identifier,
                "first_name": first_name,
                "last_name": last_name,
                "rut": rut,
                "birth_date": birth_date,
                "gender": gender,
            }

        except Exception as e:
            logger.error(f"Error parsing UCCC patient data: {e}")
            return None

    def _parse_gestion_episode_data(self, row: pd.Series) -> Dict[str, Any]:
        """Parse clinical episode data from Gestion Estadía (UCCC) row.

        - Admission: from "Fecha Inicio:" and optional "Hora Inicio:" columns
        - Discharge: attempts to find any column with keywords (alta/egreso/salida/fin)
        - Bed: from "CAMA" column
        - Status: DISCHARGED if discharge_at present
        """
        try:
            # Admission date + time
            admission_date_raw = row.get("Fecha Inicio:") or row.get("Fecha Inicio")
            admission_time_raw = row.get("Hora Inicio:") or row.get("Hora Inicio")

            # Parse admission date: common format in file is DD-MM-YY (e.g., 30-10-24)
            if pd.isna(admission_date_raw):
                admission_at = datetime.now()
            else:
                ad_dt = None
                # Normalize string if not a Timestamp
                try:
                    if isinstance(admission_date_raw, pd.Timestamp) or isinstance(admission_date_raw, date):
                        ad_candidate = admission_date_raw
                    else:
                        s = str(admission_date_raw).strip()
                        s = s.replace("\xa0", " ").strip()
                        ad_candidate = s

                    # Try DD-MM-YY first
                    try:
                        ad_dt = pd.to_datetime(ad_candidate, format='%d-%m-%y', dayfirst=True, errors='coerce')
                    except:
                        ad_dt = None

                    # Try DD-MM-YYYY
                    if ad_dt is None or pd.isna(ad_dt):
                        try:
                            ad_dt = pd.to_datetime(ad_candidate, format='%d-%m-%Y', dayfirst=True, errors='coerce')
                        except:
                            ad_dt = None

                    # Fallback to pandas auto-detection with dayfirst
                    if ad_dt is None or pd.isna(ad_dt):
                        try:
                            ad_dt = pd.to_datetime(ad_candidate, dayfirst=True, errors='coerce')
                        except:
                            ad_dt = None

                    if ad_dt is not None and not pd.isna(ad_dt):
                        admission_at = ad_dt.to_pydatetime()
                    else:
                        admission_at = datetime.now()
                except Exception:
                    admission_at = datetime.now()

            # If a time column exists, try to combine (formats like HH:MM:SS)
            if not pd.isna(admission_time_raw):
                try:
                    # Normalize time string
                    if isinstance(admission_time_raw, pd.Timestamp):
                        time_candidate = admission_time_raw
                    else:
                        ts = str(admission_time_raw).strip()
                        ts = ts.replace("\xa0", " ").strip()
                        time_candidate = ts

                    time_dt = pd.to_datetime(time_candidate, format='%H:%M:%S', errors='coerce')
                    if pd.isna(time_dt):
                        time_dt = pd.to_datetime(time_candidate, errors='coerce')

                    if not pd.isna(time_dt):
                        admission_at = admission_at.replace(
                            hour=time_dt.hour, minute=time_dt.minute, second=time_dt.second
                        )
                except Exception:
                    # ignore time parse errors and keep admission_at as-is
                    pass

            # Discharge: attempt to find a discharge-like column
            discharge_at = None
            expected_discharge = None
            discharge_candidates = [c for c in row.index if isinstance(c, str) and any(k in c.lower() for k in ["alta", "egreso", "salida", "fin", "termin"]) ]
            discharge_col = discharge_candidates[0] if discharge_candidates else None
            if discharge_col:
                discharge_raw = row.get(discharge_col)
                if not pd.isna(discharge_raw):
                    try:
                        dis_dt = pd.to_datetime(discharge_raw, errors='coerce')
                        if not pd.isna(dis_dt):
                            discharge_at = dis_dt.to_pydatetime()
                            expected_discharge = dis_dt.date()
                    except Exception as e:
                        logger.debug(f"Could not parse discharge value '{discharge_raw}': {e}")

            # Bed
            bed_raw = row.get("CAMA")
            bed_room = None
            if not pd.isna(bed_raw):
                bed_room_str = str(bed_raw).strip()
                if bed_room_str and bed_room_str.lower() != 'nan':
                    bed_room = bed_room_str

            # Status
            status = EpisodeStatus.ACTIVE
            if discharge_at is not None:
                status = EpisodeStatus.DISCHARGED

            # Episode identifier - prefer explicit Episodio column
            episode_identifier = None
            eps = row.get("Episodio:") or row.get("Episodio") or row.get("Episodio / Estadía")
            if eps is None:
                # Try to find any column containing 'episodio' in its name
                for col in row.index:
                    if isinstance(col, str) and 'episodio' in col.lower():
                        eps = row.get(col)
                        logger.debug(f"Found episode column '{col}' with value: {eps}")
                        break
            if not pd.isna(eps):
                # Convert to string, handle floats by removing .0
                eps_str = str(eps).strip()
                if eps_str.endswith('.0'):
                    eps_str = eps_str[:-2]
                episode_identifier = eps_str
                logger.debug(f"Parsed episode_identifier: {episode_identifier}")

            return {
                "admission_at": admission_at,
                "expected_discharge": expected_discharge,
                "discharge_at": discharge_at,
                "status": status,
                "bed_room": bed_room,
                "episode_identifier": episode_identifier,
            }

        except Exception as e:
            logger.error(f"Error parsing UCCC episode data: {e}")
            return {
                "admission_at": datetime.now(),
                "status": EpisodeStatus.ACTIVE,
                "bed_room": None,
                "episode_identifier": None,
            }

    async def _process_patient_row(self, row: pd.Series, row_idx: int) -> None:
        """Process a single patient row from the Excel file."""
        # Parse patient data
        patient_data = self._parse_patient_data(row)
        if not patient_data:
            return

        # Create or get patient
        patient = await self._create_or_get_patient(patient_data)

        # Create patient information
        patient_info_data = self._parse_patient_information(row)
        if patient_info_data:
            await self._create_or_update_patient_information(
                patient.id, patient_info_data
            )

        # Create clinical episode
        episode_data = self._parse_clinical_episode_data(row)
        episode = await self._create_clinical_episode(patient.id, episode_data)

        # Create clinical episode information records
        episode_info_records = self._parse_clinical_episode_information(row)
        for info_record in episode_info_records:
            await self._create_clinical_episode_information(episode.id, info_record)

        logger.info(
            f"Processed patient {patient.medical_identifier} with episode {episode.id}"
        )

    def _parse_patient_data(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Parse patient basic data from Excel row.

        Expected columns from "Score Social.xlsx":
        - RUT: Patient's RUT (may be empty for anonymous data) - Used as medical_identifier
        - Nombre: Patient's full name (may be empty for anonymous data)
        - Episodio / Estadía: Episode identifier (stored separately in episode data)
        - Fecha de nacimiento: Birth date
        
        If RUT and Nombre are present, they are used. If empty (anonymous data), 
        we generate realistic placeholder data:
        - Valid RUT with proper verification digit (used as medical_identifier)
        - Common first and last names
        - Consistent data based on episode ID (same episode always generates same name/RUT)
        
        Example with real data: RUT "12.345.678-5", Nombre "Juan Pérez" → Used as-is
        Example with anonymous: Empty fields → Generated "María González", "18.234.567-8"
        """
        try:
            # Get episode identifier to use as seed for generating consistent placeholder data
            episodio_raw = row.get("Episodio / Estadía")
            
            # Only skip if episodio is completely missing (we need it for seed generation)
            if pd.isna(episodio_raw):
                logger.warning("Skipping row with missing Episodio / Estadía")
                return None
            
            episodio_str = str(episodio_raw).strip()
            if not episodio_str or episodio_str == "" or episodio_str.lower() == "nan":
                logger.warning("Skipping row with empty Episodio / Estadía")
                return None
            
            # Check if RUT exists in the data - RUT is the medical_identifier
            rut_raw = row.get("RUT")
            if pd.isna(rut_raw) or str(rut_raw).strip() == "" or str(rut_raw).strip().lower() == "nan":
                # Generate placeholder RUT using episode as seed for consistency
                rut = generate_rut(episodio_str)
                medical_identifier = rut  # Generated RUT is the medical identifier
            else:
                # Use the real RUT from the data
                rut = str(rut_raw).strip()
                medical_identifier = rut  # Real RUT is the medical identifier
            
            # Check if Nombre exists in the data
            nombre_raw = row.get("Nombre")
            if pd.isna(nombre_raw) or str(nombre_raw).strip() == "" or str(nombre_raw).strip().lower() == "nan":
                # Generate placeholder name using episode as seed
                first_name, last_name = get_name(episodio_str)
            else:
                # Use the real name from the data
                nombre = str(nombre_raw).strip()
                # Try to split name into first and last
                name_parts = nombre.split(None, 1)  # Split on first whitespace
                if len(name_parts) >= 2:
                    first_name = name_parts[0]
                    last_name = name_parts[1]
                else:
                    first_name = nombre
                    last_name = ""
            
            # Parse birth date - "Fecha de nacimiento"
            birth_date_raw = row.get("Fecha de nacimiento")
            if pd.isna(birth_date_raw):
                # If no birth date, use a default for missing data
                birth_date = date(1970, 1, 1)
            elif isinstance(birth_date_raw, pd.Timestamp):
                birth_date = birth_date_raw.date()
            elif isinstance(birth_date_raw, date):
                birth_date = birth_date_raw
            else:
                try:
                    birth_date = pd.to_datetime(birth_date_raw).date()
                except:
                    birth_date = date(1970, 1, 1)

            # Gender not in this Excel - use default
            gender = "Desconocido"

            return {
                "medical_identifier": medical_identifier,
                "first_name": first_name,
                "last_name": last_name,
                "rut": rut,
                "birth_date": birth_date,
                "gender": gender,
            }

        except Exception as e:
            logger.error(f"Error parsing patient data: {e}")
            return None

    def _parse_patient_information(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Parse patient information (additional data stored as JSONB).

        This includes all Excel columns not used in the main patient or episode tables.
        Missing data is stored as null to preserve data completeness for analysis.
        
        From Score Social.xlsx columns:
        - Centro Atención, Nombre de la aseguradora, Previsión Homóloga, 
        - Vía de Ingreso, Encuesta, Motivo, Puntaje, Encuestadora, etc.
        """
        try:
            info = {}

            # List of columns that are used elsewhere and should be excluded
            excluded_columns = [
                # Patient basic info
                "RUT", "Nombre", "Fecha de nacimiento",
                # Episode info
                "Episodio / Estadía", "Fe.admisión", "Fecha del alta", 
                "DÍAS PACIENTES ACOSTADOS", "Estado de alta", "Cama",
                "Fecha Asignación", "Año Admisión", "Mes Admisión",
            ]

            # Add all columns as additional info, storing null for missing values
            for col in row.index:
                # Skip columns that are used in other tables
                if col in excluded_columns:
                    continue
                
                # Store all values, including missing ones as null
                value = row[col]
                
                if pd.isna(value):
                    # Store missing data as None/null for analysis
                    info[col] = None
                elif isinstance(value, (pd.Timestamp, datetime, date)):
                    info[col] = value.isoformat()
                elif isinstance(value, (int, float)):
                    # Check if it's NaN for floats
                    if pd.isna(value):
                        info[col] = None
                    else:
                        info[col] = float(value) if isinstance(value, float) else int(value)
                else:
                    # Convert to string, handle empty strings
                    str_value = str(value).strip()
                    info[col] = str_value if str_value and str_value.lower() != 'nan' else None

            # Return info even if empty, as it marks the data was processed
            return info

        except Exception as e:
            logger.error(f"Error parsing patient information: {e}")
            return {}

    def _parse_clinical_episode_data(self, row: pd.Series) -> Dict[str, Any]:
        """
        Parse clinical episode data from Excel row.
        
        Expected columns from Score Social.xlsx:
        - Episodio / Estadía: Episode identifier (stored in info records)
        - Fe.admisión: Admission date
        - Fecha del alta: Discharge date
        - Estado de alta: Discharge/episode status
        - Cama: Bed identifier for foreign key lookup
        - Fecha Asignación: Assignment date
        """
        try:
            # Get episode identifier to store in info records
            episodio_raw = row.get("Episodio / Estadía")
            episode_identifier = None
            if not pd.isna(episodio_raw):
                episode_identifier = str(episodio_raw).strip()
            
            # Parse admission date - use "Fe.admisión"
            admission_at_raw = row.get("Fe.admisión")
            if pd.isna(admission_at_raw):
                admission_at = datetime.now()
            elif isinstance(admission_at_raw, pd.Timestamp):
                admission_at = admission_at_raw.to_pydatetime()
            else:
                try:
                    admission_at = pd.to_datetime(admission_at_raw).to_pydatetime()
                except:
                    admission_at = datetime.now()

            # Parse discharge date - "Fecha del alta"
            discharge_raw = row.get("Fecha del alta")
            expected_discharge = None
            discharge_at = None
            if not pd.isna(discharge_raw):
                try:
                    # Handle string dates in DD-MM-YYYY format (e.g., "24-09-2025")
                    if isinstance(discharge_raw, str):
                        # Try parsing DD-MM-YYYY format
                        discharge_dt = pd.to_datetime(discharge_raw, format='%d-%m-%Y', errors='coerce')
                        if pd.isna(discharge_dt):
                            # Fallback to pandas auto-detection
                            discharge_dt = pd.to_datetime(discharge_raw, errors='coerce')
                        
                        if not pd.isna(discharge_dt):
                            discharge_date = discharge_dt.date()
                            discharge_at = discharge_dt.to_pydatetime()
                            expected_discharge = discharge_date
                    elif isinstance(discharge_raw, pd.Timestamp):
                        discharge_date = discharge_raw.date()
                        discharge_at = discharge_raw.to_pydatetime()
                        expected_discharge = discharge_date
                    else:
                        discharge_dt = pd.to_datetime(discharge_raw, errors='coerce')
                        if not pd.isna(discharge_dt):
                            discharge_date = discharge_dt.date()
                            discharge_at = discharge_dt.to_pydatetime()
                            expected_discharge = discharge_date
                except Exception as e:
                    logger.warning(f"Could not parse discharge date '{discharge_raw}': {e}")
                    expected_discharge = None
                    discharge_at = None

            # Parse status - use "Estado de alta"
            status_raw = row.get("Estado de alta")
            status = EpisodeStatus.ACTIVE
            if not pd.isna(status_raw):
                status_str = str(status_raw).strip()
                status_upper = status_str.upper()
                
                # Check for "Alta" or variations
                if "ALTA" in status_upper:
                    status = EpisodeStatus.DISCHARGED
                elif "TRANSFERIDO" in status_upper or "TRANSFER" in status_upper:
                    status = EpisodeStatus.TRANSFERRED
                elif "CANCELADO" in status_upper or "CANCEL" in status_upper:
                    status = EpisodeStatus.CANCELLED
                
                logger.debug(f"Estado de alta: '{status_str}' -> status: {status}")
            else:
                # If there's a discharge date but no status, assume DISCHARGED
                if discharge_at is not None:
                    status = EpisodeStatus.DISCHARGED

            # Get bed identifier for foreign key lookup - use "Cama"
            bed_identifier = row.get("Cama")
            bed_room = None
            if not pd.isna(bed_identifier):
                bed_room_str = str(bed_identifier).strip()
                if bed_room_str and bed_room_str.lower() != 'nan':
                    bed_room = bed_room_str

            return {
                "admission_at": admission_at,
                "expected_discharge": expected_discharge,
                "discharge_at": discharge_at,
                "status": status,
                "bed_room": bed_room,  # Store room name for async bed_id lookup
                "episode_identifier": episode_identifier,  # Store for info records
            }

        except Exception as e:
            logger.error(f"Error parsing clinical episode data: {e}")
            return {
                "admission_at": datetime.now(),
                "status": EpisodeStatus.ACTIVE,
                "bed_room": None,
                "episode_identifier": None,
            }

    def _parse_clinical_episode_information(
        self, row: pd.Series
    ) -> list[Dict[str, Any]]:
        """
        Parse clinical episode information records from Excel row.

        These are additional structured data about the episode.
        Missing data is stored as null to preserve data completeness for analysis.
        
        From Score Social.xlsx columns:
        - Texto libre diagnóstico admisión: Diagnosis
        - Servicio: Service/department
        - Centro Atención: Healthcare center
        - Clasificación Marca 1, 2, 3: Classifications
        - Encuesta, Motivo, Puntaje: Survey information
        """
        records = []

        try:
            # Diagnosis information
            diagnosis = row.get("Texto libre diagnóstico admisión")
            diagnosis_value = str(diagnosis).strip() if not pd.isna(diagnosis) and str(diagnosis).strip().lower() != 'nan' else None
            if diagnosis_value:
                records.append({
                    "info_type": EpisodeInfoType.DIAGNOSIS,
                    "title": "Diagnóstico de Admisión",
                    "value": {"diagnosis": diagnosis_value},
                })

            # Service/Department
            servicio = row.get("Servicio")
            servicio_value = str(servicio).strip() if not pd.isna(servicio) and str(servicio).strip().lower() != 'nan' else None
            if servicio_value:
                records.append({
                    "info_type": EpisodeInfoType.NOTES,
                    "title": "Servicio",
                    "value": {"servicio": servicio_value},
                })

            # Healthcare Center
            centro = row.get("Centro Atención")
            centro_value = str(centro).strip() if not pd.isna(centro) and str(centro).strip().lower() != 'nan' else None
            if centro_value:
                records.append({
                    "info_type": EpisodeInfoType.NOTES,
                    "title": "Centro de Atención",
                    "value": {"centro_atencion": centro_value},
                })

            # Classifications (Marca 1, 2, 3)
            marca1 = row.get("Clasificación Marca 1")
            marca2 = row.get("Clasificación Marca 2")
            marca3 = row.get("Clasificación Marca 3")
            
            if not pd.isna(marca1) or not pd.isna(marca2) or not pd.isna(marca3):
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Clasificaciones",
                    "value": {
                        "marca_1": str(marca1).strip() if not pd.isna(marca1) else None,
                        "marca_2": str(marca2).strip() if not pd.isna(marca2) else None,
                        "marca_3": str(marca3).strip() if not pd.isna(marca3) else None,
                    },
                })

            # Insurance/Coverage information
            convenio = row.get("Desc. Convenio")
            aseguradora = row.get("Nombre de la aseguradora")
            prevision = row.get("Previsión Homóloga")
            
            if not pd.isna(convenio) or not pd.isna(aseguradora) or not pd.isna(prevision):
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Información de Cobertura",
                    "value": {
                        "convenio": str(convenio).strip() if not pd.isna(convenio) else None,
                        "aseguradora": str(aseguradora).strip() if not pd.isna(aseguradora) else None,
                        "prevision": str(prevision).strip() if not pd.isna(prevision) else None,
                    },
                })

            # Entry path
            via_ingreso = row.get("Vía de Ingreso")
            if not pd.isna(via_ingreso):
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Vía de Ingreso",
                    "value": {"via_ingreso": str(via_ingreso).strip()},
                })

            # Survey information
            encuesta = row.get("Encuesta")
            motivo = row.get("Motivo")
            puntaje = row.get("Puntaje")
            encuestadora = row.get("Encuestadora")
            
            if not pd.isna(encuesta) or not pd.isna(motivo) or not pd.isna(puntaje) or not pd.isna(encuestadora):
                puntaje_value = None
                if not pd.isna(puntaje):
                    try:
                        puntaje_value = float(puntaje) if isinstance(puntaje, (int, float)) else float(str(puntaje))
                    except:
                        puntaje_value = str(puntaje).strip()
                
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Información de Encuesta",
                    "value": {
                        "encuesta": str(encuesta).strip() if not pd.isna(encuesta) else None,
                        "motivo": str(motivo).strip() if not pd.isna(motivo) else None,
                        "puntaje": puntaje_value,
                        "encuestadora": str(encuestadora).strip() if not pd.isna(encuestadora) else None,
                    },
                })

            # Valor Parcial (partial value/cost)
            valor_parcial = row.get(" Valor Parcial ")  # Note the spaces in column name
            if pd.isna(valor_parcial):
                valor_parcial = row.get("Valor Parcial")  # Try without spaces
            
            if not pd.isna(valor_parcial):
                try:
                    valor_value = float(valor_parcial) if isinstance(valor_parcial, (int, float)) else float(str(valor_parcial))
                except:
                    valor_value = str(valor_parcial).strip()
                
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Valor Parcial",
                    "value": {"valor_parcial": valor_value},
                })

            # Days count
            dias = row.get("DÍAS PACIENTES ACOSTADOS")
            if not pd.isna(dias):
                try:
                    dias_value = int(dias) if isinstance(dias, (int, float)) else int(str(dias))
                except:
                    dias_value = str(dias).strip()
                
                records.append({
                    "info_type": EpisodeInfoType.OTHER,
                    "title": "Días de Hospitalización",
                    "value": {"dias_acostados": dias_value},
                })

            # Known columns that we've already processed
            known_columns = [
                # Patient info
                "RUT", "Nombre", "Fecha de nacimiento",
                # Episode info
                "Episodio / Estadía", "Fe.admisión", "Fecha del alta", 
                "Estado de alta", "Cama", "Fecha Asignación", 
                "Año Admisión", "Mes Admisión",
                # Already processed in records above
                "Texto libre diagnóstico admisión", "Servicio", "Centro Atención",
                "Clasificación Marca 1", "Clasificación Marca 2", "Clasificación Marca 3",
                "Desc. Convenio", "Nombre de la aseguradora", "Previsión Homóloga",
                "Vía de Ingreso", "Encuesta", "Motivo", "Puntaje", "Encuestadora",
                " Valor Parcial ", "Valor Parcial", "DÍAS PACIENTES ACOSTADOS"
            ]
            
            # Store any other columns as OTHER type
            for col in row.index:
                if col in known_columns:
                    continue
                
                value = row[col]
                if pd.isna(value):
                    value_data = None
                elif isinstance(value, (pd.Timestamp, datetime, date)):
                    value_data = value.isoformat()
                else:
                    str_value = str(value).strip()
                    value_data = str_value if str_value.lower() != 'nan' else None
                
                # Only add if there's actual data
                if value_data is not None:
                    records.append({
                        "info_type": EpisodeInfoType.OTHER,
                        "title": col,
                        "value": {col: value_data},
                    })

        except Exception as e:
            logger.error(f"Error parsing clinical episode information: {e}")

        return records

    async def _create_or_get_patient(self, patient_data: Dict[str, Any]) -> Patient:
        """Create or get existing patient by medical identifier."""
        stmt = select(Patient).where(
            Patient.medical_identifier == patient_data["medical_identifier"]
        )
        result = await self.db.execute(stmt)
        existing_patient = result.scalar_one_or_none()

        if existing_patient:
            logger.info(
                f"Found existing patient: {patient_data['medical_identifier']}"
            )
            return existing_patient

        # Create new patient
        patient = Patient(**patient_data)
        self.db.add(patient)
        await self.db.flush()  # Flush to get the ID
        logger.info(f"Created new patient: {patient_data['medical_identifier']}")
        return patient

    async def _create_or_update_patient_information(
        self, patient_id: UUID, information: Dict[str, Any]
    ) -> PatientInformation:
        """Create or update patient information."""
        stmt = select(PatientInformation).where(
            PatientInformation.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        existing_info = result.scalar_one_or_none()

        if existing_info:
            # Update existing information
            existing_info.information = information
            logger.info(f"Updated patient information for patient {patient_id}")
            return existing_info

        # Create new information record
        patient_info = PatientInformation(
            patient_id=patient_id, information=information
        )
        self.db.add(patient_info)
        await self.db.flush()
        logger.info(f"Created patient information for patient {patient_id}")
        return patient_info

    async def _create_clinical_episode(
        self, patient_id: UUID, episode_data: Dict[str, Any]
    ) -> ClinicalEpisode:
        """Create a new clinical episode with bed foreign key lookup."""
        # Episode identifier may be provided in episode_data and is now stored
        # directly on the ClinicalEpisode model (episode_identifier column).
        episode_identifier = episode_data.get("episode_identifier")
        
        # Handle bed lookup if bed_room is provided
        bed_room = episode_data.pop("bed_room", None)
        bed_id = None
        if bed_room:
            bed_id = await self._get_bed_id_by_room(bed_room)
            if not bed_id:
                logger.warning(f"Bed not found for room '{bed_room}', episode will have no bed assigned")
        
        episode_data["bed_id"] = bed_id
        episode = ClinicalEpisode(patient_id=patient_id, **episode_data)
        self.db.add(episode)
        await self.db.flush()  # Flush to get the ID
        # We store the episode_identifier directly on the ClinicalEpisode model.
        # For backward compatibility, older imports may have stored it in
        # ClinicalEpisodeInformation; we no longer create that duplicate.
        
        logger.info(f"Created clinical episode for patient {patient_id} with bed_id {bed_id}")
        return episode

    async def _find_episode_by_identifier(self, episode_identifier: str) -> Optional[ClinicalEpisode]:
        """Find a ClinicalEpisode by its episode_identifier column or via legacy info records.

        Returns the ClinicalEpisode or None if not found.
        """
        if not episode_identifier:
            return None

        # First, try direct match on the new column
        stmt = select(ClinicalEpisode).where(ClinicalEpisode.episode_identifier == episode_identifier)
        result = await self.db.execute(stmt)
        episode = result.scalar_one_or_none()
        if episode:
            return episode

        # Fallback: search legacy ClinicalEpisodeInformation JSONB value for episode_identifier
        try:
            stmt2 = select(ClinicalEpisodeInformation).where(
                ClinicalEpisodeInformation.value["episode_identifier"].astext == episode_identifier
            )
            res2 = await self.db.execute(stmt2)
            info = res2.scalar_one_or_none()
            if info:
                stmt3 = select(ClinicalEpisode).where(ClinicalEpisode.id == info.episode_id)
                res3 = await self.db.execute(stmt3)
                return res3.scalar_one_or_none()
        except Exception:
            # JSONB lookup may fail if DB doesn't support the operator; ignore and return None
            pass

        return None

    async def _process_altas_sheet(self, excel_path: str | Path) -> int:
        """Read the ALTAS sheet and update episode discharge datetimes.

        Expected columns (variants):
        - Episodio
        - Fe. Alta / Fecha Alta / Fecha de Alta / Fecha
        - Hr. Alta / Hora Alta / Hora
        """
        logger.info(f"Reading ALTAS data from {excel_path}")
        try:
            raw = pd.read_excel(excel_path, sheet_name="ALTAS", header=None)

            # Try to detect header row similarly to UCCC
            def _detect_header_row(df_raw, max_scan=20, min_tokens=2):
                tokens = ["episodio", "alta", "fe", "fe.", "hr", "hora"]
                scan_rows = min(max_scan, len(df_raw))
                for i in range(scan_rows):
                    row = df_raw.iloc[i].fillna("").astype(str).str.lower().tolist()
                    found = set()
                    for cell in row:
                        for t in tokens:
                            if t in cell:
                                found.add(t)
                    if len(found) >= min_tokens:
                        return i
                return None

            header_idx = _detect_header_row(raw)
            if header_idx is None:
                df = pd.read_excel(excel_path, sheet_name="ALTAS")
            else:
                df = pd.read_excel(excel_path, sheet_name="ALTAS", header=header_idx)

            # Normalize column names and build map
            df.columns = df.columns.map(lambda c: c if not isinstance(c, str) else c.strip())
            col_map = {}
            for col in df.columns:
                if isinstance(col, str):
                    norm = self._normalize_col_name(col) if hasattr(self, '_normalize_col_name') else col.strip().lower()
                    col_map[norm] = col

            # Map ALTAS canonical columns
            candidates = {
                "Episodio": ["Episodio", "episodio"],
                "Fe. Alta": ["Fe. Alta", "Fe Alta", "Fecha Alta", "Fecha de Alta", "fecha alta", "fe. alta", "fe alta", "fecha"],
                "Hr. Alta": ["Hr. Alta", "Hr Alta", "Hora Alta", "Hora", "hr", "hora"]
            }

            def find_orig_alt(col_map, cand_list):
                for c in cand_list:
                    norm = self._normalize_col_name(c)
                    if norm in col_map:
                        return col_map[norm]
                for c in cand_list:
                    norm = self._normalize_col_name(c)
                    for k, v in col_map.items():
                        if k.startswith(norm) or norm.startswith(k):
                            return v
                return None

            rename_map = {}
            for canonical, cands in candidates.items():
                orig = find_orig_alt(col_map, cands)
                if orig:
                    rename_map[orig] = canonical

            if rename_map:
                df = df.rename(columns=rename_map)

            logger.info(f"Found {len(df)} rows in ALTAS sheet; columns: {list(df.columns)}")

            updated = 0
            for idx, row in df.iterrows():
                try:
                    eps_raw = row.get("Episodio")
                    if pd.isna(eps_raw):
                        continue
                    episode_identifier = str(eps_raw).strip()
                    # Parse date
                    fecha_raw = row.get("Fe. Alta")
                    hora_raw = row.get("Hr. Alta")

                    if pd.isna(fecha_raw) and pd.isna(hora_raw):
                        continue

                    dis_dt = None
                    # Parse fecha
                    if not pd.isna(fecha_raw):
                        try:
                            if isinstance(fecha_raw, pd.Timestamp) or isinstance(fecha_raw, date):
                                dis_candidate = fecha_raw
                            else:
                                s = str(fecha_raw).strip()
                                s = s.replace("\xa0", " ").strip()
                                dis_candidate = s

                            # Try DD-MM-YYYY first
                            dis_dt = pd.to_datetime(dis_candidate, format='%d-%m-%Y', dayfirst=True, errors='coerce')
                            if pd.isna(dis_dt):
                                dis_dt = pd.to_datetime(dis_candidate, dayfirst=True, errors='coerce')
                        except Exception:
                            dis_dt = None

                    # If only time present, parse time and combine with today? skip if no date
                    if (dis_dt is None or pd.isna(dis_dt)) and (not pd.isna(hora_raw)):
                        # Can't set discharge without a date; skip
                        continue

                    # Combine time if present
                    if dis_dt is not None and not pd.isna(dis_dt):
                        discharge_at = dis_dt.to_pydatetime()
                        if not pd.isna(hora_raw):
                            try:
                                if isinstance(hora_raw, pd.Timestamp):
                                    t_candidate = hora_raw
                                else:
                                    t_candidate = str(hora_raw).strip()

                                t_dt = pd.to_datetime(t_candidate, format='%H:%M:%S', errors='coerce')
                                if pd.isna(t_dt):
                                    t_dt = pd.to_datetime(t_candidate, format='%H:%M', errors='coerce')
                                if pd.isna(t_dt):
                                    t_dt = pd.to_datetime(t_candidate, errors='coerce')

                                if not pd.isna(t_dt):
                                    discharge_at = discharge_at.replace(
                                        hour=t_dt.hour, minute=t_dt.minute, second=t_dt.second
                                    )
                            except Exception:
                                pass
                    else:
                        continue

                    # Find the episode and update
                    episode = await self._find_episode_by_identifier(episode_identifier)
                    if not episode:
                        logger.warning(f"ALTAS: episode with identifier '{episode_identifier}' not found; skipping")
                        continue

                    episode.discharge_at = discharge_at
                    episode.status = EpisodeStatus.DISCHARGED
                    try:
                        episode.expected_discharge = discharge_at.date()
                    except Exception:
                        episode.expected_discharge = None
                    episode.status = EpisodeStatus.DISCHARGED
                    await self.db.flush()
                    updated += 1

                except Exception as e:
                    logger.error(f"Error processing ALTAS row {idx}: {e}")
                    continue

            logger.info(f"ALTAS updates applied: {updated} episodes updated")
            return updated

        except Exception as e:
            logger.warning(f"ALTAS sheet not available or parsing failed: {e}")
            return 0

    async def _create_clinical_episode_information(
        self, episode_id: UUID, info_data: Dict[str, Any]
    ) -> ClinicalEpisodeInformation:
        """Create a clinical episode information record."""
        info = ClinicalEpisodeInformation(episode_id=episode_id, **info_data)
        self.db.add(info)
        await self.db.flush()
        return info

    async def _get_bed_id_by_room(self, room: str) -> Optional[UUID]:
        """Get bed ID by room identifier."""
        stmt = select(Bed).where(Bed.room == room)
        result = await self.db.execute(stmt)
        bed = result.scalar_one_or_none()
        return bed.id if bed else None

    # ==================== SOCIAL SCORE DATA UPLOAD ====================

    async def upload_social_scores_from_excel(self, excel_path: str | Path) -> Dict[str, Any]:
        """
        Upload social score data from "Data Casos" sheet in the Score Social Excel file.

        This method:
        - Reads the "Data Casos" sheet
        - Extracts: Episodio / Estadía (to match episode), Puntaje (score), 
          Fecha Asignación (recorded_at), Encuestadora (recorded_by), Motivo (no_score_reason)
        - Creates SocialScoreHistory records for matching episodes
        - Handles null scores by storing the reason from "Motivo" column

        Args:
            excel_path: Path to the "Score Social.xlsx" file

        Returns:
            Dictionary with upload statistics:
            - count: Number of social scores uploaded
            - missing_count: Number of records where episode was not found
            - missing_ids: List of episode identifiers that were not found
        """
        logger.info(f"Reading social score data from {excel_path}")

        try:
            df = pd.read_excel(excel_path, sheet_name="Data Casos")
            logger.info(f"Found {len(df)} rows in Data Casos sheet")

            scores_created = 0
            missing_ids = []

            # Build a map of episode_identifier -> episode_id for quick lookup
            episode_map = await self._build_episode_identifier_map()
            logger.info(f"Built episode map with {len(episode_map)} entries")

            for idx, row in df.iterrows():
                try:
                    score_data = self._parse_social_score_row(row)
                    if score_data:
                        episode_identifier = score_data.pop("episode_identifier", None)
                        if episode_identifier and episode_identifier in episode_map:
                            episode_id = episode_map[episode_identifier]
                            await self._create_social_score(episode_id, score_data)
                            scores_created += 1
                        else:
                            logger.warning(f"Episode not found for identifier: {episode_identifier}")
                            if episode_identifier:
                                missing_ids.append(episode_identifier)
                except Exception as e:
                    logger.error(f"Error processing social score row {idx}: {e}")
                    continue

            await self.db.commit()
            logger.info(f"Successfully uploaded {scores_created} social scores. Missing episodes: {len(missing_ids)}")
            
            return {
                "count": scores_created,
                "missing_count": len(missing_ids),
                "missing_ids": missing_ids
            }

        except Exception as e:
            logger.error(f"Error uploading social scores: {e}")
            await self.db.rollback()
            raise

    async def _build_episode_identifier_map(self) -> Dict[str, UUID]:
        """
        Build a map of identifiers to episode IDs.
        
        This method creates a lookup map using three sources:
        1. Episode identifiers stored directly on ClinicalEpisode.episode_identifier (new approach)
        2. Episode identifiers stored in ClinicalEpisodeInformation (legacy)
        3. Patient medical identifiers (for manually created patients)
        
        This allows matching social scores to episodes whether they were imported
        from Excel or created manually.
        """
        episode_map = {}
        
        def normalize_identifier(identifier: str) -> str:
            """Normalize identifier by removing trailing .0 from floats."""
            s = str(identifier).strip()
            if s.endswith('.0'):
                s = s[:-2]
            return s
        
        # 1. Get episode identifiers directly from ClinicalEpisode model (new approach)
        stmt = select(ClinicalEpisode).where(ClinicalEpisode.episode_identifier.isnot(None))
        result = await self.db.execute(stmt)
        episodes = result.scalars().all()
        
        for episode in episodes:
            if episode.episode_identifier:
                identifier = normalize_identifier(episode.episode_identifier)
                episode_map[identifier] = episode.id
        
        logger.info(f"Found {len(episode_map)} episodes with direct episode_identifier")
        
        # 2. Get episode identifiers from ClinicalEpisodeInformation (legacy)
        stmt = select(ClinicalEpisodeInformation).where(
            ClinicalEpisodeInformation.title == "Episodio / Estadía"
        )
        result = await self.db.execute(stmt)
        episode_infos = result.scalars().all()
        
        for info in episode_infos:
            if info.value and "episode_identifier" in info.value:
                identifier = info.value["episode_identifier"]
                if identifier:
                    normalized = normalize_identifier(identifier)
                    if normalized not in episode_map:
                        episode_map[normalized] = info.episode_id
        
        # 3. Also map by patient medical_identifier for manually created patients
        # Get all episodes with their associated patients
        stmt = select(ClinicalEpisode, Patient).join(Patient)
        result = await self.db.execute(stmt)
        episode_patient_pairs = result.all()
        
        for episode, patient in episode_patient_pairs:
            if patient.medical_identifier:
                # Only add if not already in the map (episode identifier takes precedence)
                normalized = normalize_identifier(patient.medical_identifier)
                if normalized not in episode_map:
                    episode_map[normalized] = episode.id
        
        logger.info(f"Episode map contains {len(episode_map)} entries (from episode_identifier, episode info, and patient medical identifiers)")
        
        return episode_map

    def _parse_social_score_row(self, row: pd.Series) -> Optional[Dict[str, Any]]:
        """
        Parse social score data from Excel row.
        
        Expected columns from "Score Social.xlsx":
        - Episodio / Estadía: Episode identifier to match
        - Puntaje: The social score (can be null)
        - Fecha Asignación: Recorded date
        - Encuestadora: Person who recorded the score
        - Motivo: Reason if score is null
        """
        try:
            # Get episode identifier
            episodio_raw = row.get("Episodio / Estadía")
            if pd.isna(episodio_raw) or str(episodio_raw).strip() == "" or str(episodio_raw).strip().lower() == "nan":
                logger.warning("Skipping row with missing Episodio / Estadía")
                return None
            
            # Normalize identifier by removing trailing .0 from floats
            episode_identifier = str(episodio_raw).strip()
            if episode_identifier.endswith('.0'):
                episode_identifier = episode_identifier[:-2]
            
            # Parse score (Puntaje) - can be null
            puntaje_raw = row.get("Puntaje")
            score = None
            if not pd.isna(puntaje_raw):
                try:
                    score_value = float(puntaje_raw) if isinstance(puntaje_raw, (int, float)) else float(str(puntaje_raw))
                    score = int(score_value)
                except (ValueError, TypeError):
                    score = None
            
            # Parse reason for no score (Motivo)
            motivo_raw = row.get("Motivo")
            no_score_reason = None
            if pd.isna(puntaje_raw) or score is None:
                if not pd.isna(motivo_raw):
                    motivo_str = str(motivo_raw).strip()
                    if motivo_str and motivo_str.lower() != 'nan':
                        no_score_reason = motivo_str
            
            # Parse recorded date (Fecha Asignación)
            fecha_raw = row.get("Fecha Asignación")
            recorded_at = None
            if not pd.isna(fecha_raw):
                try:
                    if isinstance(fecha_raw, pd.Timestamp):
                        recorded_at = fecha_raw.to_pydatetime()
                    elif isinstance(fecha_raw, str):
                        # Try DD-MM-YYYY format first
                        fecha_dt = pd.to_datetime(fecha_raw, format='%d-%m-%Y', errors='coerce')
                        if pd.isna(fecha_dt):
                            fecha_dt = pd.to_datetime(fecha_raw, errors='coerce')
                        if not pd.isna(fecha_dt):
                            recorded_at = fecha_dt.to_pydatetime()
                    else:
                        fecha_dt = pd.to_datetime(fecha_raw, errors='coerce')
                        if not pd.isna(fecha_dt):
                            recorded_at = fecha_dt.to_pydatetime()
                except Exception as e:
                    logger.warning(f"Could not parse Fecha Asignación '{fecha_raw}': {e}")
            
            # Parse recorded by (Encuestadora)
            encuestadora_raw = row.get("Encuestadora")
            recorded_by = None
            if not pd.isna(encuestadora_raw):
                encuestadora_str = str(encuestadora_raw).strip()
                if encuestadora_str and encuestadora_str.lower() != 'nan':
                    recorded_by = encuestadora_str
            
            # Only create record if we have score or no_score_reason
            if score is None and no_score_reason is None:
                logger.debug(f"Skipping row {episode_identifier}: no score and no reason")
                return None
            
            return {
                "episode_identifier": episode_identifier,
                "score": score,
                "no_score_reason": no_score_reason,
                "recorded_at": recorded_at,
                "recorded_by": recorded_by,
            }
            
        except Exception as e:
            logger.error(f"Error parsing social score row: {e}")
            return None

    async def _create_social_score(self, episode_id: UUID, score_data: Dict[str, Any]) -> SocialScoreHistory:
        """Create a social score history record."""
        social_score = SocialScoreHistory(
            episode_id=episode_id,
            score=score_data.get("score"),
            no_score_reason=score_data.get("no_score_reason"),
            recorded_at=score_data.get("recorded_at"),
            recorded_by=score_data.get("recorded_by"),
        )
        self.db.add(social_score)
        await self.db.flush()
        logger.info(f"Created social score for episode {episode_id}: score={score_data.get('score')}, reason={score_data.get('no_score_reason')}")
        return social_score


# ==================== MAIN UPLOAD FUNCTIONS ====================


async def upload_all_data(
    beds_excel_path: str | Path, patients_excel_path: str | Path
) -> Dict[str, int]:
    """
    Upload all data from both Excel files.

    Args:
        beds_excel_path: Path to "Camas NWP1 24-09-2025 1235.xlsx"
        patients_excel_path: Path to "Score Social.xlsx"

    Returns:
        Dictionary with counts of uploaded records
    """
    async with SessionLocal() as session:
        uploader = ExcelUploader(session)

        results = {}

        # Upload beds first (patients may reference beds)
        logger.info("Starting bed data upload...")
        results["beds"] = await uploader.upload_beds_from_excel(beds_excel_path)

        # Upload patients and related data
        logger.info("Starting patient data upload...")
        results["patients"] = await uploader.upload_patients_from_excel(
            patients_excel_path
        )

        return results


async def upload_beds_only(excel_path: str | Path) -> int:
    """Upload only bed data."""
    async with SessionLocal() as session:
        uploader = ExcelUploader(session)
        return await uploader.upload_beds_from_excel(excel_path)


async def upload_patients_only(excel_path: str | Path) -> int:
    """Upload only patient data."""
    async with SessionLocal() as session:
        uploader = ExcelUploader(session)
        return await uploader.upload_patients_from_excel(excel_path)


async def upload_social_scores_only(excel_path: str | Path) -> Dict[str, Any]:
    """Upload only social score data from the Score Social Excel file."""
    async with SessionLocal() as session:
        uploader = ExcelUploader(session)
        return await uploader.upload_social_scores_from_excel(excel_path)


# ==================== CLI INTERFACE ====================


def main():
    """Main CLI interface for uploading Excel data."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Upload Excel data to the database"
    )
    parser.add_argument(
        "--beds",
        type=str,
        help='Path to beds Excel file (e.g., "Camas NWP1 24-09-2025 1235.xlsx")',
    )
    parser.add_argument(
        "--patients",
        type=str,
        help='Path to patients Excel file (e.g., "Score Social.xlsx")',
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Upload all data (requires both --beds and --patients)",
    )

    args = parser.parse_args()

    if args.all:
        if not args.beds or not args.patients:
            print("Error: --all requires both --beds and --patients arguments")
            return

        print("Uploading all data...")
        results = asyncio.run(upload_all_data(args.beds, args.patients))
        print(f"Upload complete!")
        print(f"  Beds uploaded: {results['beds']}")
        print(f"  Patients uploaded: {results['patients']}")

    elif args.beds:
        print(f"Uploading beds from {args.beds}...")
        count = asyncio.run(upload_beds_only(args.beds))
        print(f"Upload complete! {count} beds uploaded.")

    elif args.patients:
        print(f"Uploading patients from {args.patients}...")
        count = asyncio.run(upload_patients_only(args.patients))
        print(f"Upload complete! {count} patients uploaded.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
