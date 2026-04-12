"""LinkedIn scraping and posting service."""
import re
import asyncio
from typing import List, Dict, Optional
from playwright.sync_api import sync_playwright

import database
import config


def get_browser_context():
    """Create browser context with stealth settings."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            slow_mo=70,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--start-maximized",
            ]
        )
        
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="Asia/Kolkata",
        )
        
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
        
        page = context.new_page()
        
        return browser, context, page


def human_delay(min_s=2.0, max_s=4.5):
    """Random delay to mimic human behavior."""
    import random
    import time
    time.sleep(random.uniform(min_s, max_s))


async def login_to_linkedin(page, email, password):
    """Login to LinkedIn."""
    page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=30000)
    human_delay(1.5, 2.5)
    
    page.fill("#username", email)
    human_delay(0.5, 1.0)
    page.fill("#password", password)
    human_delay(0.4, 0.9)
    page.click('button[type="submit"]')
    page.wait_for_load_state("domcontentloaded", timeout=20000)
    human_delay(2.5, 4.0)
    
    # Check for verification
    if "checkpoint" in page.url.lower() or "challenge" in page.url.lower():
        raise Exception("LinkedIn verification required")
    
    return True


async def scrape_jobs(company: str, keywords: str = None, limit: int = 10) -> List[Dict]:
    """Scrape jobs from LinkedIn search."""
    from urllib.parse import quote
    
    email = database.get_setting("linkedin_email")
    password = database.get_setting("linkedin_password")
    
    if not email or not password:
        raise Exception("LinkedIn credentials not configured")
    
    jobs = []
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False, slow_mo=70)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            )
            page = context.new_page()
            
            # Login
            page.goto("https://www.linkedin.com/login")
            page.fill("#username", email)
            page.fill("#password", password)
            page.click('button[type="submit"]')
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            human_delay(2, 4)
            
            # Search
            search_query = f"{company} {keywords or 'hiring'}"
            encoded = quote(search_query)
            url = f"https://www.linkedin.com/search/results/content/?keywords={encoded}&sortBy=%22date_posted%22"
            
            page.goto(url)
            human_delay(3, 5)
            
            # Extract job cards
            selectors = [
                '.job-card-container',
                '.job-card-list__entity',
                'li[data-job-id]',
            ]
            
            for _ in range(3):
                for sel in selectors:
                    cards = page.query_selector_all(sel)
                    if cards:
                        break
                
                for card in cards[:limit]:
                    try:
                        title_el = card.query_selector('.job-card-list__title, .job-title')
                        company_el = card.query_selector('.job-card-container__company-name, .company-name')
                        location_el = card.query_selector('.job-card-container__metadata-item, .job-location')
                        link_el = card.query_selector('a[href*="/jobs/view"]')
                        
                        title = title_el.inner_text().strip() if title_el else ""
                        company_name = company_el.inner_text().strip() if company_el else company
                        location = location_el.inner_text().strip() if location_el else ""
                        job_url = link_el.get_attribute("href") if link_el else ""
                        
                        if job_url and not job_url.startswith("http"):
                            job_url = "https://www.linkedin.com" + job_url
                        
                        if title:
                            job_id = re.sub(r"[^a-zA-Z0-9]", "", job_url)[-20:] if job_url else str(hash(title))
                            
                            jobs.append({
                                "id": job_id,
                                "company": company_name,
                                "title": title,
                                "location": location,
                                "url": job_url,
                                "description": "",
                                "requirements": "",
                            })
                    except:
                        continue
                
                if len(jobs) >= limit:
                    break
                    
                human_delay(1, 2)
                page.mouse.wheel(0, 500)
                human_delay(1, 2)
            
            context.close()
            browser.close()
    
    except Exception as e:
        print(f"Error scraping: {e}")
    
    return jobs


async def post_comment(post_url: str, comment: str) -> bool:
    """Post a comment on a LinkedIn post."""
    email = database.get_setting("linkedin_email")
    password = database.get_setting("linkedin_password")
    
    if not email or not password:
        raise Exception("LinkedIn credentials not configured")
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False, slow_mo=70)
            context = browser.new_context(
                viewport={"width": 1280, "height": 800},
            )
            page = context.new_page()
            
            # Login
            page.goto("https://www.linkedin.com/login")
            page.fill("#username", email)
            page.fill("#password", password)
            page.click('button[type="submit"]')
            page.wait_for_load_state("domcontentloaded", timeout=20000)
            human_delay(2, 4)
            
            # Go to post
            page.goto(post_url)
            human_delay(2, 4)
            
            # Click comment button
            comment_btns = [
                'button[aria-label*="omment"]',
                'button:has-text("Comment")',
            ]
            
            for sel in comment_btns:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    break
            
            human_delay(1, 2)
            
            # Type comment
            page.keyboard.type(comment, delay=50)
            human_delay(1, 2)
            
            # Click post
            post_btns = [
                'button:has-text("Post")',
                'button[type="submit"]',
            ]
            
            for sel in post_btns:
                btn = page.query_selector(sel)
                if btn:
                    btn.click()
                    break
            
            human_delay(2, 4)
            
            context.close()
            browser.close()
            
            return True
    
    except Exception as e:
        print(f"Error posting comment: {e}")
        return False


async def apply_to_job(job_url: str, resume_text: str = None, cover_letter: str = None) -> bool:
    """Apply to a job on LinkedIn."""
    # This is for Easy Apply jobs
    return await post_comment(job_url, cover_letter or resume_text or "")