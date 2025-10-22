from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Date, Integer, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.clinical_episode import ClinicalEpisode
    from app.models.task_definition import TaskDefinition


class TaskStatus(enum.Enum):
    """Enum for task instance status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class TaskInstance(Base):
    __tablename__ = "task_instances"

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
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(2000)
    )
    due_date: Mapped[Date] = mapped_column(
        Date,
        nullable=True
    )
    priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus),
        nullable=False,
        default=TaskStatus.PENDING
    )
    meta_json: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    clinical_episode: Mapped["ClinicalEpisode"] = relationship(
        "ClinicalEpisode",
        back_populates="task_instances"
    )
