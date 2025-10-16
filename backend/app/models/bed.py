from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.clinical_episode import ClinicalEpisode


class Bed(Base):
    __tablename__ = "beds"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True
    )
    available: Mapped[bool] = mapped_column(
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

    # Relationship
    clinical_episodes: Mapped[list["ClinicalEpisode"]] = relationship(
        "ClinicalEpisode",
        back_populates="bed"
    )
