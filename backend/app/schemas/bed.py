from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BedBase(BaseModel):
    """Base schema for bed"""
    room: str
    active: bool = True
    available: bool = True


class BedCreate(BedBase):
    """Schema for creating a bed"""
    pass


class BedUpdate(BaseModel):
    """Schema for updating a bed"""
    active: bool | None = None
    available: bool | None = None


class Bed(BedBase):
    """Schema for bed response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
