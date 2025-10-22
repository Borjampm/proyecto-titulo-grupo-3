from datetime import datetime, date
from uuid import UUID
from enum import Enum
from typing import Dict, Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class TaskStatus(str, Enum):
    """Enum for task instance status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class TaskInstanceBase(BaseModel):
    """Base schema for task instance"""
    title: str = Field(..., max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    priority: int = Field(..., ge=1, le=5)
    status: TaskStatus = TaskStatus.PENDING
    meta_json: Optional[Dict[str, Any]] = None


class TaskInstanceCreate(TaskInstanceBase):
    """Schema for creating a task instance"""
    episode_id: UUID
    task_definition_id: UUID


class TaskInstanceUpdate(BaseModel):
    """Schema for updating a task instance"""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    priority: Optional[int] = Field(None, ge=1, le=5)
    status: Optional[TaskStatus] = None
    meta_json: Optional[Dict[str, Any]] = None


class TaskInstance(TaskInstanceBase):
    """Schema for task instance response"""
    id: UUID
    episode_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
