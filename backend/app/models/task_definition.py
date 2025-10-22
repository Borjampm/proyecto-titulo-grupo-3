from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, Boolean, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.task_instance import TaskInstance


class TaskDefinition(Base):
    __tablename__ = "task_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    description: Mapped[str] = mapped_column(
        String(2000)
    )
    estimate_duration: Mapped[int] = mapped_column(
        Integer
    )
    default_priority: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1
    )
    metadata_json: Mapped[dict] = mapped_column(
        JSONB,
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
