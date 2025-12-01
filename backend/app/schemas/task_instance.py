from datetime import datetime, date
from uuid import UUID
from enum import Enum
from typing import Dict, Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.worker import WorkerSimple


class TaskStatus(str, Enum):
    """Enum for task instance status"""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    OVERDUE = "OVERDUE"


class TaskInstanceBase(BaseModel):
    """Base schema for task instance"""
    title: str = Field(..., max_length=500)
    description: Optional[str] = Field(None, max_length=2000)
    due_date: Optional[date] = None
    priority: int = Field(..., ge=1, le=5)
    status: TaskStatus = TaskStatus.PENDING
    meta_json: Optional[Dict[str, Any]] = None
    assigned_to_id: Optional[UUID] = None


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
    assigned_to_id: Optional[UUID] = None


class TaskInstance(TaskInstanceBase):
    """Schema for task instance response"""
    id: UUID
    episode_id: UUID
    created_at: datetime
    updated_at: datetime
    assigned_worker: Optional[WorkerSimple] = None

    model_config = ConfigDict(from_attributes=True)
