from datetime import datetime
from uuid import UUID
from typing import Dict, Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskDefinitionBase(BaseModel):
    """Base schema for task definition"""
    title: str = Field(..., max_length=500)
    description: str = Field(..., max_length=2000)
    estimate_duration: int = Field(..., gt=0)
    default_priority: int = Field(..., ge=1, le=5)
    metadata_json: Optional[Dict[str, Any]] = None
    active: bool = True


class TaskDefinitionCreate(TaskDefinitionBase):
    """Schema for creating a task definition"""
    pass


class TaskDefinitionUpdate(BaseModel):
    """Schema for updating a task definition"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    estimate_duration: Optional[int] = Field(None, gt=0)
    default_priority: Optional[int] = Field(None, ge=1, le=5)
    metadata_json: Optional[Dict[str, Any]] = None
    active: Optional[bool] = None


class TaskDefinition(TaskDefinitionBase):
    """Schema for task definition response"""
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
