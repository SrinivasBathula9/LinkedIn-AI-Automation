"""
LinkedIn session manager — persist cookies to avoid repeated logins.
Stores session state to disk; restores on next run.
"""
from __future__ import annotations
import json
import os
import structlog
from playwright.async_api import Page, BrowserContext

from backend.config import settings

log = structlog.get_logger()
SESSION_FILE = os.path.join(os.path.dirname(__file__), "../../.linkedin_session.json")

LINKEDIN_LOGIN_URL = "https://www.linkedin.com/login"
LINKEDIN_FEED_URL = "https://www.linkedin.com/feed/"


async def restore_session(context: BrowserContext) -> bool:
    """Load saved cookies into context. Returns True if cookies were found."""
    if settings.linkedin_session_cookie:
        # Use the li_at cookie directly
        await context.add_cookies([
            {
                "name": "li_at",
                "value": settings.linkedin_session_cookie,
                "domain": ".linkedin.com",
                "path": "/",
                "httpOnly": True,
                "secure": True,
            }
        ])
        log.info("Session cookie loaded from env")
        return True

    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        log.info("Session cookies loaded from file", path=SESSION_FILE)
        return True

    return False


async def save_session(context: BrowserContext) -> None:
    """Persist current cookies to disk."""
    cookies = await context.cookies()
    with open(SESSION_FILE, "w") as f:
        json.dump(cookies, f)
    log.info("Session cookies saved", path=SESSION_FILE)


async def linkedin_login(page: Page) -> bool:
    """
    Log in to LinkedIn using credentials from settings.
    Returns True on success, False on failure.
    """
    await page.goto(LINKEDIN_LOGIN_URL, wait_until="domcontentloaded")
    await page.fill("#username", settings.linkedin_email)
    await page.fill("#password", settings.linkedin_password)
    await page.click('[type="submit"]')
    from backend.automation.anti_ban import human_like_delay
    await human_like_delay(3, 5)

    if "feed" in page.url or "checkpoint" not in page.url:
        log.info("LinkedIn login successful")
        await save_session(page.context)
        return True

    log.error("LinkedIn login failed or CAPTCHA detected", url=page.url)
    return False


async def ensure_logged_in(page: Page, context: BrowserContext) -> bool:
    """Check if currently logged in; log in if needed."""
    await page.goto(LINKEDIN_FEED_URL, wait_until="domcontentloaded")
    if "login" in page.url or "authwall" in page.url:
        restored = await restore_session(context)
        if restored:
            await page.reload(wait_until="domcontentloaded")
            if "feed" in page.url:
                return True
        return await linkedin_login(page)
    return True
