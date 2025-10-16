from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
import enum
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.clinical_episode import ClinicalEpisode


class EpisodeInfoType(enum.Enum):
    """Enum for clinical episode information types"""
    DIAGNOSIS = "diagnosis"
    TREATMENT = "treatment"
    MEDICATION = "medication"
    ALLERGY = "allergy"
    VITAL_SIGNS = "vital_signs"
    LAB_RESULTS = "lab_results"
    NOTES = "notes"
    PROGRESS = "progress"
    DISCHARGE_PLANNING = "discharge_planning"
    OTHER = "other"


class ClinicalEpisodeInformation(Base):
    __tablename__ = "clinical_episode_information"

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
    info_type: Mapped[EpisodeInfoType] = mapped_column(
        SQLEnum(EpisodeInfoType),
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )
    value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False
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
    clinical_episode: Mapped["ClinicalEpisode"] = relationship(
        "ClinicalEpisode",
        back_populates="information_records"
    )
