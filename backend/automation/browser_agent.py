"""
Playwright browser agent — core automation engine.
Manages stealth browser, LinkedIn session, profile navigation,
and connection request sending with human-like behavior.
"""
from __future__ import annotations
import asyncio
import structlog

# Playwright imported lazily inside functions — not required at server startup
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from playwright.async_api import Browser, BrowserContext, Page

from backend.config import settings
from backend.automation.anti_ban import (
    human_like_delay, is_daily_limit_reached, increment_sent_count,
    page_has_restriction_warning, exponential_backoff, log_event,
)
from backend.api.websocket import broadcast
from backend.db.session import AsyncSessionLocal
from backend.db.models import Profile, ConnectionRequest

log = structlog.get_logger()

_playwright_instance = None  # module-level ref so callers can stop it cleanly


async def stop_playwright() -> None:
    """Stop the Playwright subprocess — call after browser.close() to avoid pipe errors."""
    global _playwright_instance
    if _playwright_instance is not None:
        await _playwright_instance.stop()
        _playwright_instance = None


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


async def launch_stealth_browser():
    """Launch a Playwright browser with stealth settings."""
    global _playwright_instance
    from playwright.async_api import async_playwright
    from backend.automation.session_manager import restore_session
    _playwright_instance = await async_playwright().start()
    playwright = _playwright_instance
    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
        ],
    )
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",
        java_script_enabled=True,
    )
    # Apply stealth patches
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    """)
    page = await context.new_page()
    await restore_session(context)
    return browser, context, page


async def _connect_button_visible(page: Page) -> bool:
    """Check if the Connect button is present on a profile page."""
    selectors = [
        "button:has-text('Connect')",
        "div.pvs-profile-actions button:has-text('Connect')",
    ]
    for sel in selectors:
        el = page.locator(sel)
        if await el.count() > 0 and await el.first.is_visible():
            return True
    return False


async def _click_connect(page: Page, note: str) -> bool:
    """Click Connect, optionally add a note, and confirm.

    Success is determined by verifying the Connect button is gone after
    the attempt (LinkedIn changes it to Pending/Message on success) —
    not by whether intermediate button clicks raised exceptions.
    """
    if settings.dry_run:
        log.info("DRY RUN: Skipping connect click")
        return True

    connect_btn = page.locator("button:has-text('Connect')").first
    await connect_btn.click()
    await human_like_delay(1, 2)

    send_inv     = page.locator("button[aria-label='Send invitation'], button[aria-label='Send now']")
    send_without = page.locator("button:has-text('Send without a note')")
    add_note_btn = page.locator("button:has-text('Add a note')")

    # Step 1: personalised note via "Add a note" flow
    if note and await add_note_btn.count() > 0:
        await add_note_btn.click()
        await human_like_delay(0.5, 1)
        textarea = page.locator("textarea[name='message']")
        await textarea.click()
        # press_sequentially fires real keyboard events → triggers React onChange
        # so the Send button transitions from disabled → enabled
        await textarea.press_sequentially(note[:280], delay=25)
        await human_like_delay(0.5, 1.5)

        if await send_inv.count() > 0:
            try:
                await send_inv.first.wait_for(state="enabled", timeout=8000)
                await send_inv.first.click()
            except Exception:
                log.warning("Send invitation button issue — falling back")

    # Step 2: "Send without a note" (initial dialog or fallback)
    elif await send_without.count() > 0:
        await send_without.click()

    # Step 3: generic Send button (older LinkedIn modal)
    else:
        send_generic = page.locator("button:has-text('Send')")
        if await send_generic.count() > 0:
            try:
                await send_generic.first.wait_for(state="enabled", timeout=5000)
                await send_generic.first.click()
            except Exception:
                log.warning("Generic Send button unreachable")

    await human_like_delay(1, 2)

    # ── Definitive success check ──────────────────────────────────────────────
    # After a successful send LinkedIn closes the modal and changes the profile
    # button from "Connect" → "Pending" / "Message".  If the Connect button is
    # gone we know the invitation was dispatched, regardless of any intermediate
    # click exceptions.
    try:
        await page.locator("button:has-text('Connect')").wait_for(state="hidden", timeout=4000)
        log.info("Connection sent — Connect button gone (Pending/Message)")
        return True
    except Exception:
        pass

    # Dismiss stale modal if still open
    dismiss = page.locator("button:has-text('Dismiss')")
    if await dismiss.count() > 0:
        await dismiss.click()
    log.warning("Connect button still visible after send attempt — marking failed")
    return False


async def run_connection_campaign(campaign_id: str, region: str) -> None:
    """
    Main campaign runner. Called by the scheduler.
    Searches, classifies, scores, and sends connection requests.
    """
    # Lazy imports — only required when automation actually runs
    try:
        from backend.automation.session_manager import ensure_logged_in
        from backend.automation.scraper import search_profiles, scrape_profile_page, scrape_profile_location
        from backend.ai.classifier import classifier
        from backend.ai.scorer import compute_relevance_score
        from backend.ai.personalizer import generate_connection_note
    except ImportError as e:
        log.error("Automation dependencies not installed", error=str(e),
                  hint="Run: pip install playwright sentence-transformers scikit-learn && playwright install chromium")
        return

    async with AsyncSessionLocal() as db:
        await log_event(db, "campaign_start", f"Campaign {campaign_id} started for {region}")
        await broadcast({"type": "campaign_start", "campaign_id": campaign_id, "region": region})

    browser, context, page = await launch_stealth_browser()
    try:
        logged_in = await ensure_logged_in(page, context)
        if not logged_in:
            log.error("Could not authenticate with LinkedIn")
            return

        # Session warm-up: browse feed 1–2 min
        await _warm_up(page)

        # No keywords needed for the My Network -> Grow page
        raw_profiles = await search_profiles(page, region=region, max_results=30)
        log.info("Grow page extraction complete", count=len(raw_profiles), region=region)

        sent_count = 0
        async with AsyncSessionLocal() as db:
            for raw in raw_profiles:
                if await is_daily_limit_reached(db, region):
                    log.info("Daily limit reached, stopping", region=region)
                    break

                if await page_has_restriction_warning(page):
                    await log_event(db, "throttle", "LinkedIn restriction detected, pausing 24h")
                    await broadcast({"type": "restriction", "region": region})
                    await asyncio.sleep(86400)
                    break

                # Visit profile page to get real headline/title/location.
                # Grow page cards don't expose job title in their DOM, so we
                # must scrape the individual page before classifying.
                detail = await scrape_profile_page(page, raw["linkedin_url"])
                location = await scrape_profile_location(page)
                raw["headline"] = detail.get("headline", "")
                raw["location"] = location
                # Replace placeholder title with real headline when possible
                if raw.get("title") == "LinkedIn Connection":
                    raw["title"] = raw["headline"] or "LinkedIn Connection"

                # AI classification + scoring with real profile data
                result = classifier.predict(raw)
                if not result["is_relevant"]:
                    log.info("Skipping irrelevant profile", name=raw.get("full_name"), title=raw.get("title"), confidence=result["confidence"])
                    continue

                raw["relevance_score"] = compute_relevance_score(raw, campaign_regions=[])
                if raw["relevance_score"] < 30:
                    log.info("Skipping low score profile", name=raw.get("full_name"), score=raw["relevance_score"])
                    continue

                # Page is already on the profile URL — pass flag to avoid re-navigation
                was_sent = await _process_profile(page, db, raw, campaign_id, region, result, page_loaded=True)
                if was_sent:
                    sent_count += 1
                await human_like_delay(5, 12)

        log.info("Campaign run complete", region=region, sent=sent_count)
        await broadcast({"type": "campaign_done", "region": region, "sent": sent_count})

    except BaseException as e:
        import traceback
        err_msg = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        log.exception("Campaign error", error=str(e), traceback=err_msg)
        async with AsyncSessionLocal() as db:
            await log_event(db, "error", f"Campaign error: {e}\n{err_msg}", {"region": region})
    finally:
        await browser.close()
        await stop_playwright()


async def _warm_up(page: Page) -> None:
    """Browse the LinkedIn feed briefly to simulate human behavior."""
    log.info("Session warm-up — browsing feed")
    await page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded")
    await human_like_delay(3, 8)
    # Scroll through the feed
    for _ in range(3):
        await page.mouse.wheel(0, 500)
        await human_like_delay(1, 2)


async def _process_profile(page: Page, db, raw: dict, campaign_id: str, region: str, cls_result: dict, page_loaded: bool = False) -> None:
    """Navigate to a profile and send a connection request."""
    url = raw["linkedin_url"]

    # Upsert profile in DB
    from sqlalchemy import select
    result = await db.execute(
        select(Profile).where(Profile.linkedin_url == url)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = Profile(
            linkedin_url=url,
            full_name=raw.get("full_name"),
            title=raw.get("title"),
            company=raw.get("company"),
            location=raw.get("location"),
            region=region,
            relevance_score=raw.get("relevance_score"),
            is_relevant=cls_result["is_relevant"],
            classifier_confidence=cls_result["confidence"],
        )
        db.add(profile)
        await db.commit()
        await db.refresh(profile)

    # Navigate only if page wasn't already loaded by the caller
    if not page_loaded:
        await page.goto(url, wait_until="domcontentloaded")
        await human_like_delay(2, 5)

    # Scroll to simulate reading
    for _ in range(2):
        await page.mouse.wheel(0, 300)
        await human_like_delay(0.5, 1)

    # Use pre-fetched location from raw if available, otherwise scrape it
    from backend.automation.scraper import scrape_profile_location
    actual_location = raw.get("location") or await scrape_profile_location(page)
    loc_lower = actual_location.lower()

    forbidden_regions = ["pakistan", "turkey", "bangladesh", "syria", "iran", "iraq", "afghanistan", "russia", "nigeria", "china", "yemen", "somalia"]
    if any(f in loc_lower for f in forbidden_regions):
        log.info("Skipping profile in forbidden region", location=actual_location, url=url)
        await _record_request(db, profile.id, campaign_id, "skipped")
        return False

    # Update profile in DB with real location if missing
    if not profile.location and actual_location:
        profile.location = actual_location
        await db.commit()

    if not await _connect_button_visible(page):
        await _record_request(db, profile.id, campaign_id, "skipped")
        return False

    # Generate personalized note (lazy import — personalizer requires httpx)
    try:
        from backend.ai.personalizer import generate_connection_note
        note = await generate_connection_note(
            sender_name="Srinivas Bathula",
            sender_title="AI & Platform Engineering",
            recipient_name=raw.get("full_name", ""),
            recipient_title=raw.get("title", ""),
            company=raw.get("company", ""),
        )
    except Exception:
        note = f"Hi {raw.get('full_name','').split()[0]}, I'd love to connect!"

    success = await _click_connect(page, note)
    status = "sent" if success else "failed"
    await _record_request(db, profile.id, campaign_id, status, message_sent=note if success else None)

    if success:
        await increment_sent_count(db, region)
        await log_event(db, "send", f"Connection sent to {raw.get('full_name')}", {"url": url, "region": region})
        await broadcast({
            "type": "connection_sent",
            "name": raw.get("full_name"),
            "title": raw.get("title"),
            "region": region,
        })

    return success


async def _record_request(db, profile_id, campaign_id: str | None, status: str, message_sent: str | None = None) -> None:
    import uuid
    from datetime import datetime
    cr = ConnectionRequest(
        profile_id=profile_id,
        campaign_id=uuid.UUID(campaign_id) if campaign_id else None,
        status=status,
        message_sent=message_sent,
        sent_at=datetime.utcnow() if status == "sent" else None,
    )
    db.add(cr)
    await db.commit()
