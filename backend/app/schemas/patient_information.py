from datetime import datetime
from uuid import UUID
from typing import Dict, Any

from pydantic import BaseModel, ConfigDict


class PatientInformationBase(BaseModel):
    """Base schema for patient information"""
    information: Dict[str, Any]


class PatientInformationCreate(PatientInformationBase):
    """Schema for creating patient information"""
    patient_id: UUID


class PatientInformationUpdate(BaseModel):
    """Schema for updating patient information"""
    information: Dict[str, Any] | None = None


class PatientInformation(PatientInformationBase):
    """Schema for patient information response"""
    id: UUID
    patient_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
