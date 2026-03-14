"""
LinkedIn profile scraper.
Extracts profile data from LinkedIn search results and profile pages.
"""
from __future__ import annotations
import re
import structlog
from playwright.async_api import Page

log = structlog.get_logger()

SEARCH_URL = "https://www.linkedin.com/mynetwork/grow/"


async def search_profiles(
    page: Page,
    keywords: str = "",
    region: str | None = None,
    max_results: int = 25,
) -> list[dict]:
    """
    Search LinkedIn and scrape profile cards from results pages.
    Returns list of raw profile dicts.
    """
    log.info("Starting LinkedIn network grow extraction", region=region)
    await page.goto(SEARCH_URL, wait_until="domcontentloaded")
    
    # 1. Initial scroll to ensure lazy-loaded sections (like 'People you may know') appear
    # We scroll down 1000 pixels to get past invitations
    await page.evaluate("window.scrollTo(0, 1000)")
    await page.wait_for_timeout(4000)

    # Check for login redirect
    if "login" in page.url or "uas/login" in page.url:
        log.error("Scraper redirected to login page. Session may be invalid.", url=page.url)
        return []

    profiles = []
    scroll_attempts = 0

    while len(profiles) < max_results and scroll_attempts < 12:
        # 2. Extract cards
        cards = await _extract_profile_cards(page)
        
        added_in_this_step = 0
        for card in cards:
            if card["linkedin_url"] not in [p["linkedin_url"] for p in profiles]:
                profiles.append(card)
                added_in_this_step += 1
                if len(profiles) >= max_results:
                    break

        log.debug("Scraped grow page", scroll=scroll_attempts, found=len(cards), added=added_in_this_step, total=len(profiles))

        if len(profiles) >= max_results:
            break
            
        # Scroll down incrementally
        await page.evaluate(f"window.scrollBy(0, 800)")
        await page.wait_for_timeout(3000)
        scroll_attempts += 1

    return profiles[:max_results]


async def _extract_profile_cards(page: Page) -> list[dict]:
    """Extract profile data using multiple discovery strategies, targeting main content."""
    profiles = []
    
    # 1. Focus on the main content container to avoid sidebar noise
    main_selectors = ["main", "#main", ".scaffold-layout__main", "div[class*='layout__main']", ".mn-discovery__container"]
    main_container = page
    for sel in main_selectors:
        if await page.locator(sel).count() > 0:
            main_container = page.locator(sel).first
            log.debug("Targeting main container", selector=sel)
            break

    # Strategy A: Find cards in specific 'People you may know' sections
    sections = main_container.locator("section:has(h2:has-text('know')), section:has(h3:has-text('know')), div:has(h2:has-text('know'))")
    section_count = await sections.count()
    
    if section_count > 0:
        log.info("Found 'People you may know' sections in main content", count=section_count)
        for i in range(section_count):
            section = sections.nth(i)
            # Find any list items or card-like divs in this section
            cards = section.locator("li, div[class*='card'], .artdeco-entity-lockup")
            count = await cards.count()
            for j in range(count):
                profile = await _parse_card(cards.nth(j))
                if profile:
                    profiles.append(profile)

    # Strategy B: Global main-content fallback
    if len(profiles) < 5:
        log.debug("Strategy A yield low, trying main content button discovery")
        buttons = main_container.locator("button:has-text('Connect')")
        btn_count = await buttons.count()
        for i in range(btn_count):
            btn = buttons.nth(i)
            # Find the card container for this button
            container = await btn.evaluate_handle("node => node.closest('li') || node.closest('div[class*=\"card\"]') || node.closest('.artdeco-entity-lockup') || node.parentElement.parentElement")
            profile = await _parse_card(container)
            if profile:
                # Check uniqueness before adding
                if profile["linkedin_url"] not in [p["linkedin_url"] for p in profiles]:
                    profiles.append(profile)

    return profiles


async def _parse_card(card) -> dict | None:
    """Parse a single profile container with maximum resilience."""
    try:
        # Use evaluate for deep inspection
        data = await card.evaluate("""(node) => {
            const clean = (t) => (t || '').trim().replace(/\\s+/g, ' ');
            const isProfileHref = (href) => {
                const h = (href || '').toLowerCase();
                return (h.includes('/in/') || h.includes('/profile/')) &&
                       !h.includes('invite-connect') && !h.includes('messaging') && !h.includes('company');
            };

            // 1. Find profile link — search descendants first, then walk up ancestors
            //    LinkedIn's grow page wraps cards in <a> ancestors (not inside <li>)
            let profileLink = null;

            // 1a. Descendants
            const descLinks = Array.from(node.querySelectorAll('a')).filter(a => isProfileHref(a.href));
            if (descLinks.length > 0) profileLink = descLinks[0];

            // 1b. Walk up ancestor chain (up to 12 levels)
            if (!profileLink) {
                let ancestor = node.parentElement;
                for (let depth = 0; depth < 12 && ancestor; depth++) {
                    if (ancestor.tagName === 'A' && isProfileHref(ancestor.href)) {
                        profileLink = ancestor;
                        break;
                    }
                    const found = Array.from(ancestor.querySelectorAll('a')).filter(a => isProfileHref(a.href));
                    if (found.length > 0) {
                        profileLink = found[0];
                        break;
                    }
                    ancestor = ancestor.parentElement;
                }
            }

            if (!profileLink) {
                const allLinks = Array.from(node.querySelectorAll('a')).map(a => ({href: a.href, text: (a.innerText||'').substring(0, 30)}));
                return { error: 'no_valid_profile_link', all_links: allLinks };
            }

            // 2. Name extraction — prioritise Connect button aria-label as most reliable
            let name = '';

            // 2a. Connect button aria-label: "Connect with John Doe" / "Invite John Doe to connect"
            const connectBtn = Array.from(node.querySelectorAll('button')).find(b =>
                /connect/i.test(b.innerText) || /connect/i.test(b.getAttribute('aria-label') || '')
            );
            if (connectBtn) {
                const btnAria = connectBtn.getAttribute('aria-label') || '';
                const m1 = btnAria.match(/Connect with (.+)/i);
                const m2 = btnAria.match(/Invite (.+?) to connect/i);
                if (m1) name = m1[1].trim();
                else if (m2) name = m2[1].trim();
            }

            // 2b. Named class selectors
            if (!name || /view profile|linkedin member/i.test(name)) {
                const nameEl = node.querySelector(
                    '.discover-person-card__name, .mn-discovery-entity-card__title, ' +
                    '.artdeco-entity-lockup__title, span.t-bold, strong'
                );
                if (nameEl) {
                    const txt = clean(nameEl.innerText);
                    if (txt.length > 2 && !/view profile|linkedin member/i.test(txt)) name = txt;
                }
            }

            // 2c. Link text / aria-label
            if (!name || /view profile|linkedin member/i.test(name)) {
                const linkText = clean(profileLink.innerText);
                if (linkText.length > 2 && !/view profile|linkedin member/i.test(linkText)) {
                    name = linkText;
                } else {
                    const aria = profileLink.getAttribute('aria-label') || '';
                    const extracted = aria.replace(/View |Go to | profile/gi, '').split(' profile')[0].trim();
                    if (extracted.length > 2) name = extracted;
                }
            }

            name = clean(name);

            // 3. Title extraction with noise reduction
            let title = '';
            const titleSelectors = [
                '.discover-person-card__occupation', '.mn-discovery-entity-card__occupation',
                '.artdeco-entity-lockup__subtitle', 'div.t-14', 'span.t-14', '.t-12'
            ];
            for (const sel of titleSelectors) {
                const els = Array.from(node.querySelectorAll(sel));
                for (const el of els) {
                    const txt = clean(el.innerText);
                    if (txt.length > 5 && !/connect|message|mutual|premium|member/i.test(txt)) {
                        if (name && txt.toLowerCase().includes(name.toLowerCase())) continue;
                        title = txt;
                        break;
                    }
                }
                if (title) break;
            }

            return { name: name, title: clean(title), url: profileLink.href };
        }""")

        if not data or "error" in data:
            if data and data.get("error") == "no_valid_profile_link":
                log.debug("No valid profile link found in card", links=data.get("all_links"))
            return None

        name = data.get("name")
        title = data.get("title")
        raw_url = data.get("url")
        linkedin_url = _clean_url(raw_url)

        # Ignore if it's "LinkedIn Member" or "View profile" (masked/garbage)
        if not name or any(x in name.lower() for x in ["linkedin member", "view profile", "go to profile", "view "]):
            log.debug("Skipping masked or incomplete profile", name=name)
            return None

        # Clean title if it repeated the name
        if title and name and title.lower().startswith(name.lower()):
            title = title[len(name):].strip().lstrip(",").strip()

        return {
            "full_name": name,
            "title": title or "LinkedIn Connection",
            "company": "", 
            "location": "", 
            "linkedin_url": linkedin_url,
            "mutual_connections": 0,
            "recent_posts": 0,
        }
    except Exception as e:
        log.debug("Exception in _parse_card", error=str(e))
        return None


async def scrape_profile_location(page: Page) -> str:
    """Extract location from a profile page header."""
    # This selector is usually stable for locations
    selectors = [
        "span.text-body-small.inline.t-black--light.break-words",
        "div.pb2 span.text-body-small"
    ]
    for sel in selectors:
        el = page.locator(sel)
        if await el.count() > 0:
            return (await el.first.text_content() or "").strip()
    return ""


async def scrape_profile_page(page: Page, url: str) -> dict:
    """Visit a profile page and scrape detailed info."""
    await page.goto(url, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)

    async def text(selector: str) -> str:
        el = page.locator(selector)
        return (await el.first.text_content() or "").strip() if await el.count() > 0 else ""

    headline = await text("div.text-body-medium.break-words")
    summary = await text("div.display-flex.ph5.pv3 span.visually-hidden")
    
    return {
        "headline": headline,
        "summary": summary[:500],
        "mutual_connections": 0, # Hard to scrape reliably without full load
    }


def _clean_url(href: str) -> str:
    """Extract clean profile URL from href, handling relative links."""
    if not href: return ""
    
    if href.startswith("/"):
        href = "https://www.linkedin.com" + href
    
    match = re.search(r"(https://www\.linkedin\.com/in/[^/?#]+)", href)
    return match.group(1) if match else ""
