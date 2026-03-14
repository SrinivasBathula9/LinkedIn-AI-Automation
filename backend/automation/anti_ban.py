"""
Anti-ban module: rate limiting, circuit breaker, exponential backoff,
human-like delays, and LinkedIn restriction detection.
"""
from __future__ import annotations
import asyncio
import random
import math
import structlog
from datetime import date
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.models import ConnectionRequest, DailyLimit, AutomationLog

log = structlog.get_logger()


async def get_today_sent_count(db: AsyncSession, region: str | None = None) -> int:
    """Count connection requests sent today (optionally filtered by region)."""
    today = date.today()
    result = await db.execute(
        select(func.sum(DailyLimit.sent_count)).where(
            DailyLimit.date == today,
            *([] if region is None else [DailyLimit.region == region]),
        )
    )
    return result.scalar() or 0


async def increment_sent_count(db: AsyncSession, region: str) -> None:
    """Atomically increment daily sent counter for a region."""
    today = date.today()
    # Upsert
    result = await db.execute(
        select(DailyLimit).where(DailyLimit.date == today, DailyLimit.region == region)
    )
    row = result.scalar_one_or_none()
    if row:
        row.sent_count += 1
    else:
        db.add(DailyLimit(date=today, region=region, sent_count=1))
    await db.commit()


async def is_daily_limit_reached(db: AsyncSession, region: str) -> bool:
    count = await get_today_sent_count(db, region)
    if count >= settings.daily_limit_per_region:
        log.warning("Daily limit reached", region=region, count=count, limit=settings.daily_limit_per_region)
        return True
    return False


async def page_has_restriction_warning(page) -> bool:
    """Detect LinkedIn restriction / CAPTCHA signals on the current page."""
    restriction_selectors = [
        "text=We've temporarily limited",
        "text=account has been restricted",
        "text=complete the security verification",
        "#captcha-internal",
        ".challenge-dialog",
    ]
    for selector in restriction_selectors:
        try:
            el = page.locator(selector)
            if await el.count() > 0:
                log.error("LinkedIn restriction detected", selector=selector)
                return True
        except Exception:
            pass
    return False


async def human_like_delay(min_sec: float | None = None, max_sec: float | None = None) -> None:
    """Sleep for a random duration drawn from a normal distribution."""
    lo = min_sec or settings.min_delay_seconds
    hi = max_sec or settings.max_delay_seconds
    mean = (lo + hi) / 2
    std = (hi - lo) / 4
    delay = max(lo, min(hi, random.gauss(mean, std)))
    await asyncio.sleep(delay)


async def exponential_backoff(attempt: int, base: float = 2.0, cap: float = 300.0) -> None:
    """Sleep 2^attempt seconds (capped at cap) with jitter."""
    delay = min(base ** attempt + random.uniform(0, 1), cap)
    log.info("Exponential backoff", attempt=attempt, delay_sec=round(delay, 1))
    await asyncio.sleep(delay)


async def log_event(db: AsyncSession, event_type: str, message: str, metadata: dict | None = None) -> None:
    """Write an event to the automation_logs table."""
    entry = AutomationLog(event_type=event_type, message=message, log_metadata=metadata or {})
    db.add(entry)
    await db.commit()
