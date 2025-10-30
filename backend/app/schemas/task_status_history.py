from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.task_instance import TaskStatus


class TaskStatusHistoryBase(BaseModel):
    """Base schema for task status history"""
    old_status: Optional[TaskStatus] = None
    new_status: TaskStatus
    changed_by: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=1000)


class TaskStatusHistoryCreate(TaskStatusHistoryBase):
    """Schema for creating a task status history record"""
    task_id: UUID


class TaskStatusHistory(TaskStatusHistoryBase):
    """Schema for task status history response"""
    id: UUID
    task_id: UUID
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)

