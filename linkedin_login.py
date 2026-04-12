"""LinkedIn login logic."""
import browser
import terminal_ui


def login(page, email, password):
    try:
        page.goto("https://www.linkedin.com/login", wait_until="domcontentloaded", timeout=30000)
        browser.human_delay(1.5, 2.5)
        browser.human_type(page, "#username", email)
        browser.human_delay(0.5, 1.0)
        browser.human_type(page, "#password", password)
        browser.human_delay(0.4, 0.9)
        page.click('button[type="submit"]')
        page.wait_for_load_state("domcontentloaded", timeout=20000)
        browser.human_delay(2.5, 4.0)

        current_url = page.url.lower()
        if "checkpoint" in current_url or "challenge" in current_url:
            terminal_ui.print_warning("LinkedIn is asking for verification.")
            terminal_ui.print_info("Complete it in the browser window, then press Enter here.")
            input()
            browser.human_delay(2.0, 3.0)
            current_url = page.url.lower()

        if "login" in current_url:
            terminal_ui.print_error("Login failed. Check credentials in .env file.")
            return False

        terminal_ui.print_success("Logged into LinkedIn!")
        return True

    except Exception as e:
        terminal_ui.print_error(f"Login error: {e}")
        return False