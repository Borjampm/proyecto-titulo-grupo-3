from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import TYPE_CHECKING, Optional
from app.db import Base

if TYPE_CHECKING:
    from app.models.task_instance import TaskInstance


class Worker(Base):
    """Model for workers that can be assigned to tasks"""
    __tablename__ = "workers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        unique=True
    )
    role: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
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
    assigned_tasks: Mapped[list["TaskInstance"]] = relationship(
        "TaskInstance",
        back_populates="assigned_worker",
        foreign_keys="TaskInstance.assigned_to_id"
    )

