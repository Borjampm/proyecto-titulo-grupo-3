from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class EpisodeDocumentType(str, Enum):
    """Enum for episode document types"""
    MEDICAL_REPORT = "medical_report"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    IMAGING = "imaging"
    CONSENT_FORM = "consent_form"
    DISCHARGE_SUMMARY = "discharge_summary"
    TREATMENT_PLAN = "treatment_plan"
    NURSING_NOTES = "nursing_notes"
    OTHER = "other"


class EpisodeDocumentBase(BaseModel):
    """Base schema for episode document"""
    document_type: EpisodeDocumentType
    file_url: str = Field(..., max_length=1024)


class EpisodeDocumentCreate(EpisodeDocumentBase):
    """Schema for creating an episode document"""
    episode_id: UUID


class EpisodeDocumentUpdate(BaseModel):
    """Schema for updating an episode document"""
    document_type: EpisodeDocumentType | None = None
    file_url: str | None = Field(None, max_length=1024)


class EpisodeDocument(EpisodeDocumentBase):
    """Schema for episode document response"""
    id: UUID
    episode_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
