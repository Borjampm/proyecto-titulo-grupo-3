from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.clinical_episode import ClinicalEpisode


class AlertType(enum.Enum):
    """Enum for alert types"""
    STAY_DEVIATION = "stay-deviation"
    SOCIAL_RISK = "social-risk"
    PREDICTED_OVERSTAY = "predicted-overstay"


class AlertSeverity(enum.Enum):
    """Enum for alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNKNOWN = "unknown"


class Alert(Base):
    """Model for alerts related to clinical episodes"""
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    episode_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinical_episodes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    alert_type: Mapped[AlertType] = mapped_column(
        SQLEnum(AlertType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        SQLEnum(AlertSeverity, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
        index=True
    )
    created_by: Mapped[str] = mapped_column(
        String(255),
        nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationship
    clinical_episode: Mapped["ClinicalEpisode"] = relationship(
        "ClinicalEpisode",
        back_populates="alerts"
    )

