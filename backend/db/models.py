import uuid
from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, Boolean, Integer, Float, Text, Date, ARRAY, TIMESTAMP,
    ForeignKey, UniqueConstraint, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB

TIMESTAMPTZ = TIMESTAMP(timezone=True)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    target_roles: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), default=list)
    target_regions: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text), default=list)
    daily_limit: Mapped[int] = mapped_column(Integer, default=20)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, server_default=func.now())

    connection_requests: Mapped[list["ConnectionRequest"]] = relationship(back_populates="campaign")


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    linkedin_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    company: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(Text)
    region: Mapped[Optional[str]] = mapped_column(String(10))
    headline: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    mutual_connections: Mapped[int] = mapped_column(Integer, default=0)
    relevance_score: Mapped[Optional[float]] = mapped_column(Float)
    is_relevant: Mapped[Optional[bool]] = mapped_column(Boolean)
    classifier_confidence: Mapped[Optional[float]] = mapped_column(Float)
    qdrant_id: Mapped[Optional[str]] = mapped_column(Text)
    scraped_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMPTZ)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, server_default=func.now())

    connection_requests: Mapped[list["ConnectionRequest"]] = relationship(back_populates="profile")


class ConnectionRequest(Base):
    __tablename__ = "connection_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("campaigns.id"))
    profile_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id"))
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('pending','sent','accepted','failed','skipped')"),
        default="pending"
    )
    message_sent: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMPTZ)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMPTZ)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, server_default=func.now())

    campaign: Mapped[Optional["Campaign"]] = relationship(back_populates="connection_requests")
    profile: Mapped[Optional["Profile"]] = relationship(back_populates="connection_requests")


class DailyLimit(Base):
    __tablename__ = "daily_limits"
    __table_args__ = (UniqueConstraint("date", "region"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    accepted_count: Mapped[int] = mapped_column(Integer, default=0)
    region: Mapped[Optional[str]] = mapped_column(String(10))


class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type: Mapped[Optional[str]] = mapped_column(String(50))
    message: Mapped[Optional[str]] = mapped_column(Text)
    log_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSONB)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMPTZ, server_default=func.now())
