from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.clinical_episode import ClinicalEpisode


class EpisodeDocumentType(enum.Enum):
    """Enum for episode document types"""
    MEDICAL_REPORT = "medical_report"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    IMAGING = "imaging"
    CONSENT_FORM = "consent_form"
    DISCHARGE_SUMMARY = "discharge_summary"
    TREATMENT_PLAN = "treatment_plan"
    NURSING_NOTES = "nursing_notes"
    OTHER = "other"


class EpisodeDocument(Base):
    __tablename__ = "episode_documents"

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
    document_type: Mapped[EpisodeDocumentType] = mapped_column(
        SQLEnum(EpisodeDocumentType),
        nullable=False
    )
    file_url: Mapped[str] = mapped_column(
        String(1024),
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
        back_populates="documents"
    )
