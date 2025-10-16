from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class PatientInformation(Base):
    __tablename__ = "patient_information"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("patients.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )
    information: Mapped[dict] = mapped_column(
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
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="information"
    )
