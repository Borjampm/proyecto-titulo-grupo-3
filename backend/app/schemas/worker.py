from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, EmailStr


class WorkerBase(BaseModel):
    """Base schema for worker"""
    name: str = Field(..., max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)


class WorkerCreate(WorkerBase):
    """Schema for creating a worker"""
    pass


class WorkerUpdate(BaseModel):
    """Schema for updating a worker"""
    name: Optional[str] = Field(None, max_length=255)
    email: Optional[EmailStr] = None
    role: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    active: Optional[bool] = None


class Worker(WorkerBase):
    """Schema for worker response"""
    id: UUID
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WorkerSimple(BaseModel):
    """Simplified worker schema for dropdowns"""
    id: UUID
    name: str
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

