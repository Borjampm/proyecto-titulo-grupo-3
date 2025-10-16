from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
import enum
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.patient import Patient


class DocumentType(enum.Enum):
    """Enum for document types"""
    MEDICAL_REPORT = "medical_report"
    LAB_RESULT = "lab_result"
    PRESCRIPTION = "prescription"
    IMAGING = "imaging"
    CONSENT_FORM = "consent_form"
    DISCHARGE_SUMMARY = "discharge_summary"
    OTHER = "other"


class PatientDocument(Base):
    __tablename__ = "patient_documents"

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
    document_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
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
    patient: Mapped["Patient"] = relationship(
        "Patient",
        back_populates="documents"
    )

