from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db import Base
from app.models.task_instance import TaskStatus
from app.models.task_instance import TaskInstance


class TaskStatusHistory(Base):
    __tablename__ = "task_status_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    task_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("task_instances.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    old_status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, create_type=False),
        nullable=True  # NULL for initial creation
    )
    new_status: Mapped[TaskStatus] = mapped_column(
        SQLEnum(TaskStatus, create_type=False),
        nullable=False
    )
    changed_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    changed_by: Mapped[str] = mapped_column(
        String(255),
        nullable=True  # For future user tracking
    )
    notes: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )

    # Relationship
    task_instance: Mapped["TaskInstance"] = relationship(
        "TaskInstance",
        back_populates="status_history"
    )

