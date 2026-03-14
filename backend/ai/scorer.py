"""
Multi-dimension relevance scorer (0–100).

score = 0.35 * role_match
      + 0.20 * region_match
      + 0.20 * seniority
      + 0.15 * activity
      + 0.10 * network_proximity
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher

TARGET_ROLES = [
    "ceo", "cto", "coo", "cio", "chief executive", "chief technology",
    "chief operating", "chief information", "hr recruiter", "hr manager",
    "human resources", "talent acquisition", "ai architect", "platform engineer",
    "cloud solution engineer", "cloud architect", "ai engineer", "ml engineer",
    "machine learning engineer", "job consultant", "recruitment",
]

SENIORITY_KEYWORDS = {
    "c-suite": ["ceo", "cto", "coo", "cio", "chief", "president"],
    "vp": ["vp", "vice president", "svp", "evp"],
    "director": ["director", "head of", "global head"],
    "manager": ["manager", "lead", "principal"],
    "senior": ["senior", "sr.", "sr "],
    "mid": ["engineer", "developer", "analyst", "consultant", "recruiter", "architect"],
}

SENIORITY_SCORES = {
    "c-suite": 1.0, "vp": 0.9, "director": 0.8,
    "manager": 0.7, "senior": 0.6, "mid": 0.4,
}

TARGET_REGIONS = {"sg", "in", "uk", "eu", "us", "uae"}

REGION_COUNTRY_MAP = {
    "singapore": "sg", "india": "in", "united kingdom": "uk", "uk": "uk",
    "europe": "eu", "germany": "eu", "france": "eu", "netherlands": "eu",
    "united states": "us", "usa": "us", "america": "us",
    "uae": "uae", "dubai": "uae", "emirates": "uae",
}


def _fuzzy(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _role_match_score(title: str, headline: str) -> float:
    combined = f"{title} {headline}".lower()
    best = 0.0
    for role in TARGET_ROLES:
        if role in combined:
            best = 1.0
            break
        score = max(_fuzzy(role, word) for word in combined.split())
        best = max(best, score)
    return min(best, 1.0)


def _region_match_score(location: str, region: str | None, campaign_regions: list[str]) -> float:
    if not campaign_regions:
        return 1.0
    normalized = (region or "").lower()
    loc_lower = (location or "").lower()
    # Check explicit region code
    for cr in campaign_regions:
        if cr.lower() == normalized:
            return 1.0
    # Check location string against country map
    for keyword, code in REGION_COUNTRY_MAP.items():
        if keyword in loc_lower:
            if code in [r.lower() for r in campaign_regions]:
                return 1.0
    return 0.0


def _seniority_score(title: str) -> float:
    t = title.lower()
    for level, keywords in SENIORITY_KEYWORDS.items():
        if any(kw in t for kw in keywords):
            return SENIORITY_SCORES[level]
    return 0.2


def _activity_score(recent_posts: int = 0) -> float:
    """Normalize post count (0–10+) to 0–1."""
    return min(recent_posts / 10.0, 1.0)


def _network_proximity_score(mutual_connections: int) -> float:
    """Normalize mutual connections count to 0–1 (caps at 50+)."""
    return min(mutual_connections / 50.0, 1.0)


def compute_relevance_score(
    profile: dict,
    campaign_regions: list[str] | None = None,
) -> float:
    """Return a relevance score 0–100."""
    title = profile.get("title") or ""
    headline = profile.get("headline") or ""
    location = profile.get("location") or ""
    region = profile.get("region")
    mutual = profile.get("mutual_connections", 0)
    recent_posts = profile.get("recent_posts", 0)

    role = _role_match_score(title, headline)
    reg = _region_match_score(location, region, campaign_regions or [])
    sen = _seniority_score(title)
    act = _activity_score(recent_posts)
    net = _network_proximity_score(mutual)

    raw = (
        0.35 * role
        + 0.20 * reg
        + 0.20 * sen
        + 0.15 * act
        + 0.10 * net
    )
    return round(raw * 100, 2)
