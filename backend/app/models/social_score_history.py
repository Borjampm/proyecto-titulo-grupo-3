from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from typing import TYPE_CHECKING
from app.db import Base

if TYPE_CHECKING:
    from app.models.clinical_episode import ClinicalEpisode


class SocialScoreHistory(Base):
    __tablename__ = "social_score_history"

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
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )
    recorded_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    recorded_by: Mapped[str] = mapped_column(
        String(255),
        nullable=True  # For future user tracking
    )
    notes: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationship
    clinical_episode: Mapped["ClinicalEpisode"] = relationship(
        "ClinicalEpisode",
        back_populates="social_score_history"
    )

