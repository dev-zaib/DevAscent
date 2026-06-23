"""Assessment session and submission models."""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from devascent.db.models.base import Base


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    current_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="BASELINE"
    )
    skills_matrix: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    active_challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True)
    )
    escalation_depth: Mapped[int] = mapped_column(Integer, default=0)
    challenge_attempt: Mapped[int] = mapped_column(Integer, default=0)
    state_snapshot: Mapped[dict] = mapped_column(JSONB, default=dict)
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="in_progress"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("assessment_sessions.id"), nullable=False
    )
    challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("challenges.id"), nullable=False
    )
    code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), nullable=False)
    score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    rubric_breakdown: Mapped[dict | None] = mapped_column(JSONB)
    ai_feedback: Mapped[str | None] = mapped_column(Text)
    constraints_applied: Mapped[list | None] = mapped_column(JSONB)
    job_id: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="queued"
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
