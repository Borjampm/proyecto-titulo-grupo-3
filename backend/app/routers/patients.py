from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.deps import get_session
from app.models.patient import Patient as PatientModel
from app.schemas.patient import Patient


router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/", response_model=list[Patient])
async def list_patients(session: AsyncSession = Depends(get_session)) -> list[Patient]:
    result = await session.execute(select(PatientModel))
    return result.scalars().all()

