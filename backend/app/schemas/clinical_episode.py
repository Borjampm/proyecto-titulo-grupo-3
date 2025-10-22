from datetime import datetime, date
from uuid import UUID
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class EpisodeStatus(str, Enum):
    """Enum for clinical episode status"""
    ACTIVE = "active"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    CANCELLED = "cancelled"


class ClinicalEpisodeBase(BaseModel):
    """Base schema for clinical episode"""
    discharge_at: Optional[datetime] = None
    expected_discharge: Optional[date] = None
    status: EpisodeStatus = EpisodeStatus.ACTIVE
    bed_id: Optional[UUID] = None
    admission_at: datetime = Field(default_factory=datetime.utcnow)


class ClinicalEpisodeCreate(ClinicalEpisodeBase):
    """Schema for creating a clinical episode"""
    patient_id: UUID


class ClinicalEpisodeUpdate(BaseModel):
    """Schema for updating a clinical episode"""
    discharge_at: Optional[datetime] = None
    expected_discharge: Optional[date] = None
    status: Optional[EpisodeStatus] = None
    bed_id: Optional[UUID] = None
    admission_at: Optional[datetime] = None


class ClinicalEpisode(ClinicalEpisodeBase):
    """Schema for clinical episode response"""
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

 # In schemas/clinical_episode.py
from app.schemas.patient import Patient  # Import the Patient schema

class ClinicalEpisodeWithPatient(ClinicalEpisodeBase):
    id: UUID
    patient_id: UUID
    patient: Optional[Patient] = None  # Add this to include the full patient data
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)