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
    from app.models.episode_document import EpisodeDocument
    from app.models.clinical_episode_information import ClinicalEpisodeInformation
    from app.models.task_instance import TaskInstance
    from app.models.social_score_history import SocialScoreHistory
    from app.models.alert import Alert


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
    episode_identifier: Mapped[str] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    grd_expected_days: Mapped[int] = mapped_column(
        nullable=True,
        comment="Expected stay days from GRD (Estancia Norma GRD)"
    )
    grd_name: Mapped[str] = mapped_column(
        String(500),
        nullable=True,
        comment="GRD diagnosis name (e.g., PH TRASPLANTE CARDÍACO Y/O PULMONAR W/MCC)"
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
    documents: Mapped[list["EpisodeDocument"]] = relationship(
        "EpisodeDocument",
        back_populates="clinical_episode",
        cascade="all, delete-orphan"
    )
    information_records: Mapped[list["ClinicalEpisodeInformation"]] = relationship(
        "ClinicalEpisodeInformation",
        back_populates="clinical_episode",
        cascade="all, delete-orphan"
    )
    task_instances: Mapped[list["TaskInstance"]] = relationship(
        "TaskInstance",
        back_populates="clinical_episode",
        cascade="all, delete-orphan"
    )
    social_score_history: Mapped[list["SocialScoreHistory"]] = relationship(
        "SocialScoreHistory",
        back_populates="clinical_episode",
        cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="clinical_episode",
        cascade="all, delete-orphan"
    )
