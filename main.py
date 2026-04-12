"""LinkedIn Job Hunter Agent - Main orchestrator (Fully Agentic v2.0)."""
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
import ai_resume_analyzer
import ai_resume_customizer
import cli_wizard
import application_tracker


def validate_config():
    """Validate configuration."""
    placeholders = [
        ("your_email@gmail.com", config.LINKEDIN_EMAIL, "LINKEDIN_EMAIL"),
        ("your_linkedin_password", config.LINKEDIN_PASSWORD, "LINKEDIN_PASSWORD"),
        ("AIzaYourGeminiKeyHere", config.GEMINI_API_KEY, "GEMINI_API_KEY"),
    ]
    for placeholder, value, name in placeholders:
        if placeholder == value or not value:
            terminal_ui.print_error(f"Missing {name} in .env file.")
            return False
    return True


def load_preferences():
    """Load saved preferences."""
    return cli_wizard.load_preferences()


def load_resume(industry):
    """Load resume for industry."""
    return ai_resume_analyzer.load_resume(industry)


def main():
    """Main agentic workflow."""
    terminal_ui.print_banner_agentic()

    # Check config
    terminal_ui.print_step("Checking configuration...")
    if not validate_config():
        sys.exit(1)

    # Check/setup preferences
    prefs = load_preferences()
    
    if not prefs.get("done_setup"):
        terminal_ui.print_warning("First time setup required!")
        print()
        cli_wizard.run_setup()
        return
    
    industry = prefs.get("industry")
    companies = prefs.get("companies", [])
    
    if not industry or not companies:
        terminal_ui.print_error("Invalid preferences. Run setup again.")
        return
    
    # Load resume
    resume = load_resume(industry)
    if not resume:
        terminal_ui.print_error(f"No resume found for {industry}")
        return
    
    # Show status
    terminal_ui.print_success(f"Industry: {resume.get('display_name')}")
    terminal_ui.print_success(f"Companies ({len(companies)}): {', '.join(companies)}")
    
    # Show application stats
    stats = application_tracker.get_summary()
    if stats.get("total", 0) > 0:
        terminal_ui.print_info(f"Total applications so far: {stats['total']}")
        print(f"  Applied: {stats['applied']} | Interview: {stats['interview']} | Offer: {stats['offer']}")
    
    # Confirm start
    print()
    if not terminal_ui.ask_continue("Start hunting for jobs?"):
        terminal_ui.print_warning("Cancelled.")
        return
    
    already_done = set(logger._load().get("commented_post_ids", []))
    
    session_posted = 0
    session_skipped = 0
    session_errors = 0

    terminal_ui.print_step("Launching browser...")
    
    with sync_playwright() as pw:
        browser_obj, context, page = browser.create_browser(pw)
        terminal_ui.print_success("Browser launched.")

        # Login
        terminal_ui.print_step("Logging into LinkedIn...")
        if not linkedin_login.login(page, config.LINKEDIN_EMAIL, config.LINKEDIN_PASSWORD):
            browser_obj.close()
            sys.exit(1)

        # Process each company
        for idx, company in enumerate(companies, 1):
            terminal_ui.print_company_header(company, idx, len(companies))

            # Search jobs
            terminal_ui.print_step(f"Searching for job posts at {company}...")
            posts = linkedin_search.find_hiring_posts(page, company, config.MAX_POSTS_PER_COMPANY)

            if not posts:
                terminal_ui.print_warning(f"No job posts found for {company}")
                continue

            terminal_ui.print_success(f"Found {len(posts)} post(s)")

            # Process each post
            for p_idx, post in enumerate(posts, 1):
                terminal_ui.print_post_preview(p_idx, len(posts), post["url"], post["text"])

                # Skip duplicates
                if post["post_id"] in already_done:
                    terminal_ui.print_duplicate_skip(post["post_id"])
                    session_skipped += 1
                    continue

                # ==== AGENTIC WORKFLOW ====
                # Step 1: Analyze job requirements
                terminal_ui.print_step("Analyzing job requirements...")
                job_analysis = ai_resume_analyzer.analyze_job_requirements(post["text"])
                
                if not job_analysis:
                    terminal_ui.print_error("Failed to analyze job. Skipping.")
                    session_errors += 1
                    continue
                
                # Step 2: Calculate match score
                match_score = ai_resume_analyzer.calculate_skill_match(
                    resume.get("skills", {}), 
                    job_analysis
                )
                terminal_ui.print_job_match_info(
                    job_analysis.get("title", "Unknown"),
                    match_score,
                    ai_resume_analyzer.detect_experience_level(resume.get("experience", [])),
                    job_analysis.get("experience_years", "N/A")
                )
                
                # Skip if very low match (optional)
                if match_score < 30:
                    terminal_ui.print_warning(f"Low match ({match_score}%). Skip?")
                    if not terminal_ui.ask_continue():
                        session_skipped += 1
                        continue

                # Step 3: Customize resume for this job
                terminal_ui.print_step("Customizing resume for this position...")
                customized = ai_resume_customizer.customize_resume_for_job(
                    resume, 
                    job_analysis, 
                    post["text"]
                )
                
                if not customized:
                    terminal_ui.print_warning("Using default resume items")
                
                # Step 4: Generate personalized comment
                terminal_ui.print_step("Generating AI comment...")
                comment = ai_resume_customizer.generate_cover_snippet(
                    resume,
                    job_analysis,
                    job_analysis.get("title", company)
                )

                if not comment:
                    terminal_ui.print_error("AI could not generate comment. Skipping.")
                    session_errors += 1
                    continue

                # Show match
                terminal_ui.print_match_percentage(match_score, "Resume Match")

                # Step 5: User approval
                choice = terminal_ui.ask_approval(comment)

                if choice == "e":
                    comment = terminal_ui.ask_edited_comment()
                    if not comment:
                        terminal_ui.print_warning("Empty comment. Skipping.")
                        session_skipped += 1
                        continue
                    choice = terminal_ui.ask_approval(comment)

                # Step 6: Post comment
                if choice == "y":
                    terminal_ui.print_step("Posting comment...")
                    success = linkedin_comment.post_comment(page, post["url"], comment)
                    
                    if success:
                        terminal_ui.print_success("Comment posted!")
                        logger.log_comment(post, company, comment)
                        already_done.add(post["post_id"])
                        session_posted += 1
                        
                        # Track application
                        try:
                            application_tracker.add_application(
                                company=company,
                                position=job_analysis.get("title", ""),
                                post_url=post["url"],
                                post_text=post["text"],
                                comment=comment,
                                status="applied"
                            )
                        except:
                            pass
                    else:
                        terminal_ui.print_error("Failed to post comment.")
                        session_errors += 1
                else:
                    terminal_ui.print_warning("Skipped.")
                    session_skipped += 1

                # Delay between posts
                browser.human_delay(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS + 2)

        context.close()
        browser_obj.close()

    # Session summary
    stats = application_tracker.get_summary()
    terminal_ui.print_session_summary(
        session_posted, 
        session_skipped, 
        session_errors, 
        config.LOG_FILE
    )
    
    # Show updated stats
    new_stats = application_tracker.get_summary()
    if new_stats["total"] > stats["total"]:
        print()
        terminal_ui.print_success(f"Total all-time applications: {new_stats['total']}")


def main_setup():
    """Run setup wizard."""
    cli_wizard.run_setup()


def main_status():
    """View status."""
    cli_wizard.view_status()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--setup":
            main_setup()
        elif cmd == "--status":
            main_status()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python main.py [--setup|--status]")
    else:
        main()