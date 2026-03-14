"""
Full Playwright LinkedIn agent — annotated reference implementation.

This is the authoritative reference for the browser automation layer.
The production code in backend/automation/browser_agent.py imports from here.

Key design principles:
1. Stealth-first: mask all automation signals before any interaction
2. Human-like timing: randomized delays drawn from normal distributions
3. Session persistence: reuse cookies to avoid repeated logins
4. Graceful degradation: circuit-break on restriction signals
5. Dry-run support: DRY_RUN=true skips actual clicks for safe testing
"""
import asyncio
import random
import json
import os
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

# ─── Constants ────────────────────────────────────────────────────────────────

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

LINKEDIN_FEED = "https://www.linkedin.com/feed/"
LINKEDIN_LOGIN = "https://www.linkedin.com/login"

DAILY_LIMIT = int(os.getenv("DAILY_LIMIT_PER_REGION", "20"))
SESSION_LIMIT = int(os.getenv("SESSION_LIMIT", "10"))
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"


# ─── Browser Setup ────────────────────────────────────────────────────────────

async def launch_stealth_browser() -> tuple[Browser, BrowserContext, Page]:
    """
    Launch a Chromium browser with stealth hardening.

    Key stealth measures:
    - Disable 'webdriver' navigator property (primary bot signal)
    - Spoof navigator.languages and navigator.plugins
    - Use realistic viewport and user agent
    - Set locale and timezone to match target region
    """
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1366,768",
        ],
    )
    context = await browser.new_context(
        user_agent=USER_AGENT,
        viewport={"width": 1366, "height": 768},
        locale="en-US",
        timezone_id="America/New_York",  # override per region as needed
        java_script_enabled=True,
        accept_downloads=False,
    )
    # Inject stealth JS before any page load
    await context.add_init_script("""
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        // Spoof plugins (bots have 0, real browsers have several)
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        // Spoof languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        // Spoof chrome object
        window.chrome = { runtime: {} };
    """)
    page = await context.new_page()
    return browser, context, page


# ─── Session Management ───────────────────────────────────────────────────────

SESSION_FILE = ".linkedin_session.json"


async def load_session(context: BrowserContext) -> bool:
    """Load saved cookies. Returns True if session file found."""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)
        return True
    return False


async def save_session(context: BrowserContext) -> None:
    with open(SESSION_FILE, "w") as f:
        json.dump(await context.cookies(), f)


async def ensure_logged_in(page: Page, context: BrowserContext, email: str, password: str) -> bool:
    """Check if logged in; attempt login if not."""
    await load_session(context)
    await page.goto(LINKEDIN_FEED, wait_until="domcontentloaded")

    if "feed" in page.url:
        return True  # session valid

    # Login flow
    await page.goto(LINKEDIN_LOGIN, wait_until="domcontentloaded")
    await human_delay(1, 2)
    await page.fill("#username", email)
    await human_delay(0.3, 0.8)
    await page.fill("#password", password)
    await human_delay(0.5, 1.5)
    await page.click('[type="submit"]')
    await page.wait_for_load_state("networkidle")

    if "feed" in page.url:
        await save_session(context)
        return True
    return False


# ─── Human Behavior ───────────────────────────────────────────────────────────

async def human_delay(min_s: float = 2.0, max_s: float = 5.0) -> None:
    """Sleep for a random duration sampled from a normal distribution."""
    mean = (min_s + max_s) / 2
    std = (max_s - min_s) / 4
    delay = max(min_s, min(max_s, random.gauss(mean, std)))
    await asyncio.sleep(delay)


async def simulate_reading(page: Page, scrolls: int = 3) -> None:
    """Simulate a human reading a page by scrolling gradually."""
    for _ in range(scrolls):
        scroll_amount = random.randint(200, 600)
        await page.mouse.wheel(0, scroll_amount)
        await human_delay(1, 3)


async def warm_up_session(page: Page) -> None:
    """Browse the feed briefly before sending requests (1–2 min warm-up)."""
    await page.goto(LINKEDIN_FEED, wait_until="domcontentloaded")
    await simulate_reading(page, scrolls=random.randint(3, 6))
    await human_delay(30, 90)


# ─── Restriction Detection ────────────────────────────────────────────────────

async def check_restrictions(page: Page) -> bool:
    """Return True if LinkedIn is showing a restriction or CAPTCHA."""
    signals = [
        "text=We've temporarily limited your account",
        "text=account has been restricted",
        "text=complete a security verification",
        "#captcha-internal",
        ".challenge-dialog",
        "text=unusual activity",
    ]
    for sel in signals:
        try:
            if await page.locator(sel).count() > 0:
                print(f"[RESTRICTION] Detected: {sel}")
                return True
        except Exception:
            pass
    return False


# ─── Connect Flow ─────────────────────────────────────────────────────────────

async def connect_button_visible(page: Page) -> bool:
    """Check whether a Connect button is available on the current profile."""
    selectors = [
        "button:has-text('Connect')",
        ".pvs-profile-actions button:has-text('Connect')",
    ]
    for sel in selectors:
        el = page.locator(sel)
        if await el.count() > 0 and await el.first.is_visible():
            return True
    return False


async def send_connection_request(page: Page, note: str = "") -> bool:
    """
    Click Connect, optionally add a personalized note, and send.
    Returns True on success.

    In DRY_RUN mode, just logs the action without clicking.
    """
    if DRY_RUN:
        print(f"[DRY RUN] Would send connection with note: {note[:50]}...")
        return True

    connect_btn = page.locator("button:has-text('Connect')").first
    await connect_btn.click()
    await human_delay(1, 2)

    # If there's an "Add a note" option and we have a note, use it
    add_note_btn = page.locator("button:has-text('Add a note')")
    if note and await add_note_btn.count() > 0:
        await add_note_btn.click()
        await human_delay(0.5, 1)
        textarea = page.locator("textarea[name='message']")
        await textarea.fill(note[:280])
        await human_delay(1, 2)

    # Click Send
    send_btn = page.locator("button:has-text('Send')")
    if await send_btn.count() > 0:
        await send_btn.click()
        await human_delay(1, 2)
        return True

    # Dismiss modal if Send not found
    dismiss = page.locator("button:has-text('Dismiss')")
    if await dismiss.count() > 0:
        await dismiss.click()
    return False


# ─── Main Campaign Runner ─────────────────────────────────────────────────────

async def run_campaign(profiles: list[dict], email: str, password: str, region: str) -> list[dict]:
    """
    Full campaign run:
    1. Launch stealth browser
    2. Ensure logged in
    3. Warm up session
    4. For each profile: navigate → check connect → send → log → delay

    Returns list of results with status per profile.
    """
    results = []
    sent_count = 0

    browser, context, page = await launch_stealth_browser()
    try:
        logged_in = await ensure_logged_in(page, context, email, password)
        if not logged_in:
            print("[ERROR] Could not log in to LinkedIn")
            return results

        await warm_up_session(page)

        for profile in profiles:
            if sent_count >= SESSION_LIMIT:
                print(f"[INFO] Session limit ({SESSION_LIMIT}) reached")
                break

            url = profile["linkedin_url"]
            print(f"[INFO] Processing: {profile.get('full_name')} @ {url}")

            # Navigate to profile
            await page.goto(url, wait_until="domcontentloaded")
            await human_delay(2, 5)
            await simulate_reading(page, scrolls=random.randint(1, 3))

            # Check restrictions
            if await check_restrictions(page):
                print("[WARN] Restriction detected — pausing campaign")
                results.append({"url": url, "status": "restricted"})
                break

            if not await connect_button_visible(page):
                results.append({"url": url, "status": "skipped"})
                print(f"[SKIP] No Connect button for {profile.get('full_name')}")
                continue

            # Generate note (placeholder — use personalizer in production)
            note = f"Hi {profile.get('full_name','').split()[0]}, I'd love to connect!"

            success = await send_connection_request(page, note)
            status = "sent" if success else "failed"
            results.append({"url": url, "status": status, "note": note})
            print(f"[{status.upper()}] {profile.get('full_name')}")

            if success:
                sent_count += 1

            # Human-like delay between requests (8–20 sec)
            await human_delay(8, 20)

    except Exception as e:
        print(f"[ERROR] Campaign error: {e}")
    finally:
        await browser.close()

    print(f"\nCampaign complete — {sent_count} sent, {len(results)} processed")
    return results


# ─── CLI entrypoint ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="LinkedIn connection campaign runner")
    parser.add_argument("--email",    required=True, help="LinkedIn email")
    parser.add_argument("--password", required=True, help="LinkedIn password")
    parser.add_argument("--region",   default="SG",  help="Target region code")
    parser.add_argument("--dry-run",  action="store_true", help="Skip actual sends")
    args = parser.parse_args()

    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    sample_profiles = [
        {"linkedin_url": "https://www.linkedin.com/in/example1", "full_name": "Alice Tan"},
        {"linkedin_url": "https://www.linkedin.com/in/example2", "full_name": "Bob Lee"},
    ]

    asyncio.run(run_campaign(sample_profiles, args.email, args.password, args.region))
