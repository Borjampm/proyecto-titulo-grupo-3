from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.deps import get_session
from app.models.patient import Patient as PatientModel
from app.schemas.patient import Patient, PatientCreate


router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=list[Patient])
async def list_patients(session: AsyncSession = Depends(get_session)) -> list[Patient]:
    result = await session.execute(select(PatientModel))
    return result.scalars().all()


@router.post("/", response_model=Patient)
async def add_patient(
    patient: PatientCreate,
    session: AsyncSession = Depends(get_session)
) -> Patient:
    """Create a new patient."""
    now = datetime.now()
    db_patient = PatientModel(
        medical_identifier=patient.medical_identifier,
        first_name=patient.first_name,
        last_name=patient.last_name,
        rut=patient.rut,
        birth_date=patient.birth_date,
        gender=patient.gender,
        created_at=now,
        updated_at=now
    )
    session.add(db_patient)
    await session.flush()
    await session.refresh(db_patient)
    return db_patient
