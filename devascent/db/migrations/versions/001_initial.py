"""Initial schema — assessment platform core tables

Revision ID: 001
Revises: None
Create Date: 2026-06-23
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")

    op.create_table(
        "users",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(255)),
        sa.Column("avatar_url", sa.String(1024)),
        sa.Column("github_username", sa.String(255)),
        sa.Column("auth_provider", sa.String(50), nullable=False,
                  server_default="credentials"),
        sa.Column("hashed_password", sa.String(255)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )

    op.create_table(
        "challenges",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("difficulty", sa.String(50), nullable=False,
                  server_default="intermediate"),
        sa.Column("target_skills", pg.ARRAY(sa.String()), nullable=False),
        sa.Column("target_level", sa.String(50), nullable=False,
                  server_default="BASELINE"),
        sa.Column("rubric", pg.JSONB()),
        sa.Column("constraints", pg.JSONB()),
        sa.Column("hints", pg.JSONB()),
        sa.Column("solution_checklist", pg.JSONB()),
        sa.Column("embedding", pg.VECTOR(1536)),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )

    op.create_table(
        "assessment_sessions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("users.id"), nullable=False),
        sa.Column("current_level", sa.String(50), nullable=False,
                  server_default="BASELINE"),
        sa.Column("skills_matrix", pg.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("active_challenge_id", pg.UUID(as_uuid=True)),
        sa.Column("escalation_depth", sa.Integer(), server_default="0"),
        sa.Column("challenge_attempt", sa.Integer(), server_default="0"),
        sa.Column("state_snapshot", pg.JSONB(), server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(50), nullable=False,
                  server_default="in_progress"),
        sa.Column("started_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "submissions",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("session_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("assessment_sessions.id"), nullable=False),
        sa.Column("challenge_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("challenges.id"), nullable=False),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("language", sa.String(50), nullable=False),
        sa.Column("score", sa.Numeric(5, 2)),
        sa.Column("rubric_breakdown", pg.JSONB()),
        sa.Column("ai_feedback", sa.Text()),
        sa.Column("constraints_applied", pg.JSONB()),
        sa.Column("job_id", sa.String(255)),
        sa.Column("status", sa.String(50), nullable=False,
                  server_default="queued"),
        sa.Column("submitted_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
        sa.Column("evaluated_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "organizations",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), unique=True, nullable=False),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("settings", pg.JSONB()),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )

    op.create_table(
        "cohorts",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("uuid_generate_v4()")),
        sa.Column("org_id", pg.UUID(as_uuid=True),
                  sa.ForeignKey("organizations.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("start_date", sa.Date()),
        sa.Column("end_date", sa.Date()),
        sa.Column("challenge_set_id", pg.UUID(as_uuid=True)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()")),
    )

    op.create_index(
        "idx_challenges_embedding",
        "challenges",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )


def downgrade() -> None:
    op.drop_table("cohorts")
    op.drop_table("organizations")
    op.drop_table("submissions")
    op.drop_table("assessment_sessions")
    op.drop_index("idx_challenges_embedding", table_name="challenges")
    op.drop_table("challenges")
    op.drop_table("users")
