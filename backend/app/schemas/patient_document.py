from datetime import datetime
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DocumentType(str, Enum):
    """Enum for document types"""
    MEDICAL_REPORT = "medical_report"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    IMAGING = "imaging"
    CONSENT_FORM = "consent_form"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER = "other"


class PatientDocumentBase(BaseModel):
    """Base schema for patient document"""
    document_type: DocumentType
    file_url: str = Field(..., max_length=1024)


class PatientDocumentCreate(PatientDocumentBase):
    """Schema for creating a patient document"""
    patient_id: UUID


class PatientDocumentUpdate(BaseModel):
    """Schema for updating a patient document"""
    document_type: DocumentType | None = None
    file_url: str | None = Field(None, max_length=1024)


class PatientDocument(PatientDocumentBase):
    """Schema for patient document response"""
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

