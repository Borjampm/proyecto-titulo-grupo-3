from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, Date, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.patient import Patient
    from app.models.bed import Bed


class EpisodeStatus(enum.Enum):
    """Enum for clinical episode status"""
    ACTIVE = "active"
    DISCHARGED = "discharged"
    TRANSFERRED = "transferred"
    CANCELLED = "cancelled"


class ClinicalEpisode(Base):
    __tablename__ = "clinical_episodes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    discharge_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    expected_discharge: Mapped[Date] = mapped_column(
        Date,
        nullable=True
    )
    status: Mapped[EpisodeStatus] = mapped_column(
        SQLEnum(EpisodeStatus),
        nullable=False,
        default=EpisodeStatus.ACTIVE
    )
    bed_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("beds.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    admission_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
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
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="clinical_episodes"
    )
    bed: Mapped["Bed"] = relationship(
        "Bed",
        back_populates="clinical_episodes"
    )
