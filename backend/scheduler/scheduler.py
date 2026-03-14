"""
Region-aware APScheduler — fires connection campaigns at local morning/evening windows.
"""
import asyncio
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from backend.scheduler.job_registry import get_all_jobs
from backend.db.session import AsyncSessionLocal
from backend.db.models import Campaign

log = structlog.get_logger()

_scheduler: AsyncIOScheduler | None = None


async def _get_active_campaign_id(region: str) -> str | None:
    """Fetch the first active campaign that targets the given region."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Campaign).where(
                Campaign.is_active == True,
                Campaign.target_regions.any(region),
            ).limit(1)
        )
        campaign = result.scalar_one_or_none()
        return str(campaign.id) if campaign else None


async def _scheduled_job(region: str) -> None:
    """Wrapper called by APScheduler for each region/window."""
    from backend.automation.browser_agent import run_connection_campaign

    campaign_id = await _get_active_campaign_id(region)
    if not campaign_id:
        log.info("No active campaign for region, skipping", region=region)
        return

    log.info("Scheduled job triggered", region=region, campaign_id=campaign_id)
    await run_connection_campaign(campaign_id=campaign_id, region=region)


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
        _register_jobs(_scheduler)
    return _scheduler


def _register_jobs(scheduler: AsyncIOScheduler) -> None:
    for job in get_all_jobs():
        scheduler.add_job(
            _scheduled_job,
            CronTrigger(hour=job["hour"], minute=job["minute"], timezone=job["timezone"]),
            kwargs={"region": job["region"]},
            id=job["id"],
            replace_existing=True,
            misfire_grace_time=300,  # 5 min grace
        )
        log.info(
            "Job registered",
            id=job["id"],
            region=job["region"],
            hour=job["hour"],
        )


def start_scheduler() -> None:
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        log.info("APScheduler started", job_count=len(scheduler.get_jobs()))


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        log.info("APScheduler stopped")
