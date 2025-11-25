from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SocialScoreHistoryBase(BaseModel):
    """Base schema for social score history"""
    score: int = Field(..., description="The social score value")
    recorded_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class SocialScoreHistoryCreate(SocialScoreHistoryBase):
    """Schema for creating a social score history record"""
    episode_id: UUID
    recorded_at: Optional[datetime] = None  # If not provided, server will use current time


class SocialScoreHistoryUpdate(BaseModel):
    """Schema for updating a social score history record"""
    score: Optional[int] = None
    recorded_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class SocialScoreHistory(SocialScoreHistoryBase):
    """Schema for social score history response"""
    id: UUID
    episode_id: UUID
    recorded_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

