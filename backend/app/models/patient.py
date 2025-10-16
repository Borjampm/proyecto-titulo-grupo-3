from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Date, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.patient_document import PatientDocument
    from app.models.patient_information import PatientInformation


class Patient(Base):
    __tablename__ = "patients"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    medical_identifier: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        index=True
    )
    first_name: Mapped[str] = mapped_column(String(320))
    last_name: Mapped[str] = mapped_column(String(320))
    rut: Mapped[str] = mapped_column(String(320))
    birth_date: Mapped[Date] = mapped_column(Date)
    gender: Mapped[str] = mapped_column(String(320))
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
    documents: Mapped[list["PatientDocument"]] = relationship(
        "PatientDocument",
        back_populates="patient",
        cascade="all, delete-orphan"
    )
    information: Mapped["PatientInformation"] = relationship(
        "PatientInformation",
        back_populates="patient",
        uselist=False,
        cascade="all, delete-orphan"
    )
