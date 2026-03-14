from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.db.models import ConnectionRequest, DailyLimit, Profile

router = APIRouter(prefix="/stats", tags=["stats"])


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


@router.get("/overview", response_model=OverviewStats)
async def get_overview(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    today = now.date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    async def count_by_status_since(status: str, since: date) -> int:
        r = await db.execute(
            select(func.count()).where(
                and_(
                    ConnectionRequest.status == status,
                    func.date(ConnectionRequest.created_at) >= since,
                )
            )
        )
        return r.scalar() or 0

    sent_today = await count_by_status_since("sent", today)
    sent_week = await count_by_status_since("sent", week_ago)
    sent_month = await count_by_status_since("sent", month_ago)

    r_accepted = await db.execute(select(func.count()).where(ConnectionRequest.status == "accepted"))
    total_accepted = r_accepted.scalar() or 0

    r_sent_all = await db.execute(select(func.count()).where(ConnectionRequest.status == "sent"))
    total_sent_all = r_sent_all.scalar() or 0

    acceptance_rate = round(total_accepted / total_sent_all * 100, 1) if total_sent_all else 0.0

    r_pending = await db.execute(select(func.count()).where(ConnectionRequest.status == "pending"))
    total_pending = r_pending.scalar() or 0

    r_failed = await db.execute(
        select(func.count()).where(ConnectionRequest.status.in_(["failed", "skipped"]))
    )
    total_failed = r_failed.scalar() or 0

    r_profiles = await db.execute(select(func.count()).select_from(Profile))
    total_profiles = r_profiles.scalar() or 0

    return OverviewStats(
        total_sent_today=sent_today,
        total_sent_week=sent_week,
        total_sent_month=sent_month,
        total_accepted=total_accepted,
        acceptance_rate=acceptance_rate,
        total_pending=total_pending,
        total_failed=total_failed,
        total_profiles=total_profiles,
    )


@router.get("/daily", response_model=list[DailyStat])
async def get_daily_stats(days: int = 30, db: AsyncSession = Depends(get_db)):
    since = date.today() - timedelta(days=days)
    result = await db.execute(
        select(DailyLimit).where(DailyLimit.date >= since).order_by(DailyLimit.date)
    )
    rows = result.scalars().all()
    # Aggregate across regions per day
    aggregated: dict[date, DailyStat] = {}
    for row in rows:
        if row.date not in aggregated:
            aggregated[row.date] = DailyStat(date=row.date, sent=0, accepted=0)
        aggregated[row.date].sent += row.sent_count
        aggregated[row.date].accepted += row.accepted_count
    return sorted(aggregated.values(), key=lambda x: x.date)
