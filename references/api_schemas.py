"""
Pydantic request/response schemas — canonical reference for all API contracts.
"""
import uuid
from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, HttpUrl, Field


# ─── Campaigns ────────────────────────────────────────────────────────────────

class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_roles: list[str] = Field(default_factory=list)
    target_regions: list[str] = Field(default_factory=list)
    daily_limit: int = Field(default=20, ge=1, le=25)


class CampaignOut(BaseModel):
    id: uuid.UUID
    name: str
    target_roles: list[str]
    target_regions: list[str]
    daily_limit: int
    is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Profiles ─────────────────────────────────────────────────────────────────

class ProfileIn(BaseModel):
    linkedin_url: str
    full_name: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    region: Optional[str] = None
    headline: Optional[str] = None
    summary: Optional[str] = None
    mutual_connections: int = 0
    recent_posts: int = 0


class ProfileOut(BaseModel):
    id: uuid.UUID
    linkedin_url: str
    full_name: Optional[str]
    title: Optional[str]
    company: Optional[str]
    region: Optional[str]
    relevance_score: Optional[float]
    classifier_confidence: Optional[float]
    is_relevant: Optional[bool]
    model_config = {"from_attributes": True}


# ─── Connection Requests ───────────────────────────────────────────────────────

ConnectionStatus = Literal["pending", "sent", "accepted", "failed", "skipped"]


class ConnectionRequestOut(BaseModel):
    id: uuid.UUID
    campaign_id: Optional[uuid.UUID]
    profile_id: Optional[uuid.UUID]
    status: ConnectionStatus
    message_sent: Optional[str]
    sent_at: Optional[datetime]
    accepted_at: Optional[datetime]
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── Stats ────────────────────────────────────────────────────────────────────

class OverviewStats(BaseModel):
    total_sent_today: int
    total_sent_week: int
    total_sent_month: int
    total_accepted: int
    acceptance_rate: float
    total_pending: int
    total_failed: int
    total_profiles: int


class DailyStat(BaseModel):
    date: date
    sent: int
    accepted: int


# ─── Logs ─────────────────────────────────────────────────────────────────────

class LogOut(BaseModel):
    id: uuid.UUID
    event_type: Optional[str]
    message: Optional[str]
    metadata: Optional[dict]
    created_at: datetime
    model_config = {"from_attributes": True}


# ─── AI ───────────────────────────────────────────────────────────────────────

class ClassificationResult(BaseModel):
    is_relevant: bool
    confidence: float = Field(..., ge=0, le=1)


class ScoringResult(BaseModel):
    relevance_score: float = Field(..., ge=0, le=100)
    role_match: float
    region_match: float
    seniority: float
    activity: float
    network_proximity: float
