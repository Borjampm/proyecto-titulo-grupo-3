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
from app.schemas.social_score_history import SocialScoreHistory

class ClinicalEpisodeWithPatient(ClinicalEpisodeBase):
    id: UUID
    patient_id: UUID
    patient: Optional[Patient] = None  # Add this to include the full patient data
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ClinicalEpisodeWithIncludes(ClinicalEpisodeBase):
    """Schema for clinical episode with optional includes (patient, social_score)"""
    id: UUID
    patient_id: UUID
    patient: Optional[Patient] = None
    latest_social_score: Optional[SocialScoreHistory] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# Schema classes for episode history endpoint
class HistoryEventType(str, Enum):
    """Enum for history event types"""
    PATIENT_ADMISSION = "patient_admission"
    DOCUMENT_UPLOADED = "document_uploaded"
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"


class HistoryEvent(BaseModel):
    """Schema for a single history event"""
    event_type: HistoryEventType
    event_date: datetime
    description: str
    metadata: dict = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)


class EpisodeHistory(BaseModel):
    """Schema for episode history response"""
    episode_id: UUID
    events: list[HistoryEvent]


class PaginatedClinicalEpisodes(BaseModel):
    """Schema for paginated clinical episodes response"""
    data: list[ClinicalEpisode | ClinicalEpisodeWithPatient | ClinicalEpisodeWithIncludes]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = ConfigDict(from_attributes=True)


class ReferralCreate(BaseModel):
    """Schema for creating a referral"""
    patient_id: UUID
    service: str
    diagnosis: str
    expected_days: int
    social_factors: Optional[str] = None
    clinical_notes: Optional[str] = None
    submitted_by: str
    admission_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ReferralResponse(ClinicalEpisodeBase):
    """Schema for referral response"""
    id: UUID
    patient_id: UUID
    patient: Optional[Patient] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)