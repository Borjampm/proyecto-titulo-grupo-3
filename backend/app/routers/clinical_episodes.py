from fastapi import APIRouter, HTTPException

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from app.deps import get_session
from sqlalchemy.orm import selectinload
from enum import Enum
from typing import Union

from app.models.clinical_episode import ClinicalEpisode as ClinicalEpisodeModel
from app.schemas.clinical_episode import ClinicalEpisodeWithPatient, ClinicalEpisode



router = APIRouter(prefix="/clinical-episodes", tags=["clinical-episodes"])


class ClinicalEpisodeInclude(str, Enum):
    PATIENT = "patient"

@router.get("/", response_model=Union[list[ClinicalEpisodeWithPatient], list[ClinicalEpisode]])
async def list_clinical_episodes(
    include: ClinicalEpisodeInclude | None = None,
    session: AsyncSession = Depends(get_session)
) -> Union[list[ClinicalEpisodeWithPatient], list[ClinicalEpisode]]:
    if include == ClinicalEpisodeInclude.PATIENT:
        clinical_episodes = select(ClinicalEpisodeModel)
        clinical_episodes_with_patient_info = clinical_episodes.options(selectinload(ClinicalEpisodeModel.patient))
        result = await session.execute(clinical_episodes_with_patient_info)
    else:
        clinical_episodes = select(ClinicalEpisodeModel)
        result = await session.execute(clinical_episodes)
    return result.scalars().all()