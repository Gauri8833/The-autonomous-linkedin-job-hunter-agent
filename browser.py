"""Browser automation with Playwright and stealth settings."""
import random
import time
import config


def create_browser(playwright_instance):
    browser = playwright_instance.chromium.launch(
        headless=config.HEADLESS,
        slow_mo=config.BROWSER_SLOW_MO,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-infobars",
            "--start-maximized",
        ],
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


def human_delay(min_s=None, max_s=None):
    if min_s is None:
        min_s = config.MIN_DELAY_SECONDS
    if max_s is None:
        max_s = config.MAX_DELAY_SECONDS
    time.sleep(random.uniform(min_s, max_s))


def human_type(page, selector, text):
    page.click(selector)
    time.sleep(random.uniform(0.3, 0.6))
    for char in text:
        page.keyboard.type(char)
        time.sleep(random.uniform(config.TYPING_SPEED_MIN_MS, config.TYPING_SPEED_MAX_MS) / 1000.0)


def scroll_page(page, times=2):
    for _ in range(times):
        page.mouse.wheel(0, random.randint(350, 650))
        time.sleep(random.uniform(0.7, 1.4))