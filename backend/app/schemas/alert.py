from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.alert import AlertType, AlertSeverity


class AlertBase(BaseModel):
    """Base schema for alerts"""
    alert_type: AlertType = Field(..., description="Type of alert (stay-deviation or social-risk)")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    message: str = Field(..., max_length=1000, description="Alert message/description")
    is_active: bool = Field(True, description="Whether the alert is active")


class AlertCreate(BaseModel):
    """Schema for creating an alert"""
    episode_id: UUID
    message: str = Field(..., max_length=1000)
    severity: AlertSeverity
    created_by: Optional[str] = Field(None, max_length=255)


class AlertCreateManual(BaseModel):
    """Schema for manually creating a social-risk alert via API"""
    message: str = Field(..., max_length=1000, description="Alert message/description")
    severity: AlertSeverity = Field(..., description="Alert severity (low, medium, high)")
    created_by: Optional[str] = Field(None, max_length=255, description="Person creating the alert")


class Alert(AlertBase):
    """Schema for alert response"""
    id: UUID
    episode_id: UUID
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

