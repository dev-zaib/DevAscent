"""Challenge model — vector-driven assessment challenges."""
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from devascent.db.models.base import Base


class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    difficulty: Mapped[str] = mapped_column(
        String(50), nullable=False, default="intermediate"
    )
    target_skills: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    target_level: Mapped[str] = mapped_column(
        String(50), nullable=False, default="BASELINE"
    )
    rubric: Mapped[dict | None] = mapped_column(JSONB)
    constraints: Mapped[list | None] = mapped_column(JSONB)
    hints: Mapped[list | None] = mapped_column(JSONB)
    solution_checklist: Mapped[list | None] = mapped_column(JSONB)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
