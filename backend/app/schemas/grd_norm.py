from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GrdNormBase(BaseModel):
    """Base schema for GRD norm"""
    grd_id: str = Field(..., max_length=50, description="GRD code identifier")
    expected_days: int = Field(..., ge=0, description="Expected stay days according to GRD norm")


class GrdNormCreate(GrdNormBase):
    """Schema for creating a GRD norm"""
    pass


class GrdNormUpdate(BaseModel):
    """Schema for updating a GRD norm"""
    expected_days: Optional[int] = Field(None, ge=0)


class GrdNorm(GrdNormBase):
    """Schema for GRD norm response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
