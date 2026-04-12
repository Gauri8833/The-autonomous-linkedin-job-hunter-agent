"""LinkedIn Job Hunter Agent - Main orchestrator."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import config
import terminal_ui
import logger
import browser
import linkedin_login
import linkedin_search
import linkedin_comment
import ai_writer


def load_text_file(path, label):
    if not Path(path).exists():
        terminal_ui.print_error(f"{label} not found: {path}")
        sys.exit(1)
    content = Path(path).read_text().strip()
    if not content:
        terminal_ui.print_error(f"{label} is empty. Fill it in.")
        sys.exit(1)
    return content


def validate_config():
    placeholders = [
        ("your_email@gmail.com", config.LINKEDIN_EMAIL, "LINKEDIN_EMAIL"),
        ("your_linkedin_password", config.LINKEDIN_PASSWORD, "LINKEDIN_PASSWORD"),
        ("AIzaYourGeminiKeyHere", config.GEMINI_API_KEY, "GEMINI_API_KEY"),
    ]
    for placeholder, value, name in placeholders:
        if placeholder == value or not value:
            terminal_ui.print_error(f"Missing {name} in .env file. Fill it in and re-run.")
            return False
    return True


def main():
    terminal_ui.print_banner()

    terminal_ui.print_step("Checking configuration...")
    if not validate_config():
        sys.exit(1)

    resume = load_text_file(config.RESUME_FILE, "resume.txt")
    companies_text = load_text_file(config.TARGET_COMPANIES, "target_companies.txt")
    companies = [c.strip() for c in companies_text.splitlines() if c.strip() and not c.startswith("#")]

    terminal_ui.print_success(f"Resume loaded ({len(resume)} chars)")
    terminal_ui.print_success(f"{len(companies)} target companies: {', '.join(companies)}")

    already_done = set(logger._load().get("commented_post_ids", []))

    session_posted = 0
    session_skipped = 0
    session_errors = 0

    terminal_ui.print_step("Launching browser...")
    with sync_playwright() as pw:
        browser_obj, context, page = browser.create_browser(pw)
        terminal_ui.print_success("Browser launched.")

        terminal_ui.print_step("Logging into LinkedIn...")
        if not linkedin_login.login(page, config.LINKEDIN_EMAIL, config.LINKEDIN_PASSWORD):
            browser_obj.close()
            sys.exit(1)

        for idx, company in enumerate(companies, 1):
            terminal_ui.print_company_header(company, idx, len(companies))

            terminal_ui.print_step(f"Searching for hiring posts at {company}...")
            posts = linkedin_search.find_hiring_posts(page, company, config.MAX_POSTS_PER_COMPANY)

            if not posts:
                terminal_ui.print_warning(f"No hiring posts found for {company}")
                continue

            terminal_ui.print_success(f"Found {len(posts)} post(s)")

            for p_idx, post in enumerate(posts, 1):
                terminal_ui.print_post_preview(p_idx, len(posts), post["url"], post["text"])

                if post["post_id"] in already_done:
                    terminal_ui.print_duplicate_skip(post["post_id"])
                    session_skipped += 1
                    continue

                terminal_ui.print_step("Generating personalised comment with Gemini AI...")
                comment = ai_writer.generate_comment(
                    post_text=post["text"],
                    company=company,
                    resume=resume,
                    max_chars=config.COMMENT_MAX_CHARS,
                )

                if not comment:
                    terminal_ui.print_error("AI could not generate a comment. Skipping.")
                    session_errors += 1
                    continue

                choice = terminal_ui.ask_approval(comment)

                if choice == "e":
                    comment = terminal_ui.ask_edited_comment()
                    if not comment:
                        terminal_ui.print_warning("Empty comment after edit. Skipping.")
                        session_skipped += 1
                        continue
                    choice = terminal_ui.ask_approval(comment)

                if choice == "y":
                    terminal_ui.print_step("Posting comment...")
                    success = linkedin_comment.post_comment(page, post["url"], comment)
                    if success:
                        terminal_ui.print_success("Comment posted!")
                        logger.log_comment(post, company, comment)
                        already_done.add(post["post_id"])
                        session_posted += 1
                    else:
                        terminal_ui.print_error("Failed to post comment.")
                        session_errors += 1
                else:
                    terminal_ui.print_warning("Skipped.")
                    session_skipped += 1

                browser.human_delay(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS + 2)

        context.close()
        browser_obj.close()

    terminal_ui.print_session_summary(session_posted, session_skipped, session_errors, config.LOG_FILE)


if __name__ == "__main__":
    main()