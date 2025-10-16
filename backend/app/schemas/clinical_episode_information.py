from datetime import datetime
from uuid import UUID
from enum import Enum
from typing import Dict, Any

from pydantic import BaseModel, ConfigDict, Field


class EpisodeInfoType(str, Enum):
    """Enum for clinical episode information types"""
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    VITAL_SIGNS = "vital_signs"
    LAB_RESULTS = "lab_results"
    NOTES = "notes"
    PROGRESS = "progress"
    DISCHARGE_PLANNING = "discharge_planning"
    OTHER = "other"


class ClinicalEpisodeInformationBase(BaseModel):
    """Base schema for clinical episode information"""
    info_type: EpisodeInfoType
    title: str = Field(..., max_length=500)
    value: Dict[str, Any]


class ClinicalEpisodeInformationCreate(ClinicalEpisodeInformationBase):
    """Schema for creating clinical episode information"""
    episode_id: UUID


class ClinicalEpisodeInformationUpdate(BaseModel):
    """Schema for updating clinical episode information"""
    info_type: EpisodeInfoType | None = None
    title: str | None = Field(None, max_length=500)
    value: Dict[str, Any] | None = None


class ClinicalEpisodeInformation(ClinicalEpisodeInformationBase):
    """Schema for clinical episode information response"""
    id: UUID
    episode_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
