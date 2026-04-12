"""Search LinkedIn for hiring posts from target companies."""
import re
import urllib.parse
import browser
import config
import terminal_ui


def find_hiring_posts(page, company, max_posts):
    posts = []
    for keyword in config.HIRING_KEYWORDS:
        if len(posts) >= max_posts:
            break
        query = f"{company} {keyword}"
        encoded_query = urllib.parse.quote(query)
        url = (
            f"https://www.linkedin.com/search/results/content/"
            f"?keywords={encoded_query}"
            "&sortBy=%22date_posted%22"
            "&origin=GLOBAL_SEARCH_HEADER"
        )
        terminal_ui.print_info(f'Searching: "{query}"...')
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        browser.human_delay(2.5, 4.0)
        browser.scroll_page(page, times=2)

        card_selectors = [
            'div[data-urn*="activity"]',
            'li.reusable-search__result-container',
            'div.feed-shared-update-v2',
        ]
        cards = []
        for sel in card_selectors:
            cards = page.query_selector_all(sel)
            if cards:
                break

        for card in cards:
            result = _extract_post(card, company, keyword)
            if result and result["post_id"] not in [p["post_id"] for p in posts]:
                if _is_hiring_post(result["text"]):
                    posts.append(result)
            if len(posts) >= max_posts:
                break

        browser.human_delay(2.0, 3.5)

    return posts[:max_posts]


def _extract_post(card, company, keyword):
    text_sel = [
        '.feed-shared-update-v2__description',
        '.update-components-text',
        '.feed-shared-text span[dir="ltr"]',
        'span[dir="ltr"]',
    ]
    text = ""
    for sel in text_sel:
        el = card.query_selector(sel)
        if el:
            text = el.inner_text().strip()
            if text and len(text) >= 50:
                break
    if not text or len(text) < 50:
        return None

    link_sel = 'a[href*="activity"], a[href*="/feed/update/"]'
    link = card.query_selector(link_sel)
    if link:
        href = link.get_attribute("href")
        url = "https://www.linkedin.com" + href if href.startswith("/") else href
    else:
        url = ""

    post_id = re.sub(r"[^a-zA-Z0-9]", "", url)[-40:]
    if not post_id or len(post_id) < 8:
        post_id = str(abs(hash(text[:80])))

    return {
        "post_id": post_id,
        "url": url,
        "text": text,
        "company": company,
        "keyword": keyword,
    }


def _is_hiring_post(text):
    text_lower = text.lower()
    return any(signal in text_lower for signal in config.HIRING_SIGNALS)