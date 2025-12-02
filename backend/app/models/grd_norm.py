from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db import Base


class GrdNorm(Base):
    """
    Model for GRD (Grupos Relacionados de Diagnóstico) norms.

    Stores the expected stay duration for each GRD code based on US norms.
    """
    __tablename__ = "grd_norms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    grd_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        comment="GRD code identifier"
    )
    expected_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Expected stay days according to GRD norm (Est Media)"
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
