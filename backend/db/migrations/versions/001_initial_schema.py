"""Initial schema

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    # pgvector not required — embeddings stored in Qdrant

    op.create_table(
        "campaigns",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("target_roles", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("target_regions", postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column("daily_limit", sa.Integer, server_default="20"),
        sa.Column("is_active", sa.Boolean, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("linkedin_url", sa.Text, unique=True, nullable=False),
        sa.Column("full_name", sa.Text, nullable=True),
        sa.Column("title", sa.Text, nullable=True),
        sa.Column("company", sa.Text, nullable=True),
        sa.Column("location", sa.Text, nullable=True),
        sa.Column("region", sa.String(10), nullable=True),
        sa.Column("headline", sa.Text, nullable=True),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("mutual_connections", sa.Integer, server_default="0"),
        sa.Column("relevance_score", sa.Float, nullable=True),
        sa.Column("is_relevant", sa.Boolean, nullable=True),
        sa.Column("classifier_confidence", sa.Float, nullable=True),
        sa.Column("qdrant_id", sa.Text, nullable=True),
        sa.Column("scraped_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    op.create_table(
        "connection_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("campaign_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("campaigns.id"), nullable=True),
        sa.Column("profile_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("profiles.id"), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("message_sent", sa.Text, nullable=True),
        sa.Column("sent_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("accepted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
        sa.CheckConstraint("status IN ('pending','sent','accepted','failed','skipped')"),
    )

    op.create_table(
        "daily_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("sent_count", sa.Integer, server_default="0"),
        sa.Column("accepted_count", sa.Integer, server_default="0"),
        sa.Column("region", sa.String(10), nullable=True),
        sa.UniqueConstraint("date", "region"),
    )

    op.create_table(
        "automation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("metadata", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("now()")),
    )

    op.create_index("ix_profiles_region", "profiles", ["region"])
    op.create_index("ix_profiles_relevance_score", "profiles", ["relevance_score"])
    op.create_index("ix_connection_requests_status", "connection_requests", ["status"])
    op.create_index("ix_automation_logs_created_at", "automation_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("automation_logs")
    op.drop_table("daily_limits")
    op.drop_table("connection_requests")
    op.drop_table("profiles")
    op.drop_table("campaigns")
