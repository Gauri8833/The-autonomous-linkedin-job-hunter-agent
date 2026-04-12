"""CLI Wizard for first-time setup - Industry and company selection."""
import json
from pathlib import Path
import config
import terminal_ui
import ai_resume_analyzer


def load_preferences():
    """Load saved preferences."""
    if not config.PREFERENCES_FILE.exists():
        return {"industry": None, "companies": [], "done_setup": False}
    
    try:
        with open(config.PREFERENCES_FILE, "r") as f:
            return json.load(f)
    except:
        return {"industry": None, "companies": [], "done_setup": False}


def save_preferences(prefs):
    """Save preferences."""
    config.DATA_DIR.mkdir(exist_ok=True)
    with open(config.PREFERENCES_FILE, "w") as f:
        json.dump(prefs, f, indent=2)


def show_available_resumes():
    """Show available resumes and return user's choice."""
    terminal_ui.print_step("Available resumes in your profile:")
    print()
    
    industries = ai_resume_analyzer.get_available_industries()
    
    if not industries:
        terminal_ui.print_error("No resumes found!")
        terminal_ui.print_info("Please create a resume JSON file in data/resumes/{industry}.json")
        return None
    
    for i, industry in enumerate(industries, 1):
        summary = ai_resume_analyzer.get_resume_summary(industry)
        if summary:
            print(f"  {i}. {summary['display_name']}")
            print(f"     Experience: {summary['experience_level']}")
            print(f"     Skills: {len(summary['skills'])} categories")
            print()
    
    while True:
        try:
            choice = input(f"Select industry [1-{len(industries)}]: ").strip()
            if not choice:
                continue
            idx = int(choice) - 1
            if 0 <= idx < len(industries):
                return industries[idx]
        except ValueError:
            pass


def add_companies():
    """Add target companies."""
    companies = []
    
    terminal_ui.print_step("Add companies to target (one per line)")
    terminal_ui.print_info("Press Enter on empty line when done")
    print()
    
    while True:
        company = input("Company name: ").strip()
        if not company:
            break
        if company.lower() not in [c.lower() for c in companies]:
            companies.append(company)
            terminal_ui.print_success(f"Added: {company}")
    
    return companies


def confirm_setup(industry, companies):
    """Confirm setup details."""
    print()
    terminal_ui.print_info("=" * 50)
    terminal_ui.print_step("SETUP SUMMARY")
    terminal_ui.print_info("=" * 50)
    
    summary = ai_resume_analyzer.get_resume_summary(industry)
    print(f"  Industry: {summary['display_name']}")
    print(f"  Companies ({len(companies)}): {', '.join(companies)}")
    print()
    
    confirm = input("Confirm? [y/n]: ").strip().lower()
    return confirm in ("y", "yes", "")


def run_setup():
    """Run full setup wizard."""
    terminal_ui.print_banner()
    print()
    terminal_ui.print_step("WELCOME TO LINKEDIN JOB HUNTER SETUP")
    print()
    
    # Step 1: Select industry
    industry = show_available_resumes()
    if not industry:
        return None
    
    # Step 2: Add companies
    companies = add_companies()
    if not companies:
        terminal_ui.print_error("No companies added!")
        return None
    
    # Step 3: Confirm
    if not confirm_setup(industry, companies):
        terminal_ui.print_warning("Setup cancelled. Please try again.")
        return None
    
    # Step 4: Save
    prefs = {
        "industry": industry,
        "companies": companies,
        "done_setup": True
    }
    save_preferences(prefs)
    
    terminal_ui.print_success("Setup complete!")
    terminal_ui.print_info("Run 'python main.py' to start hunting!")
    
    return prefs


def run_update_companies():
    """Update companies list."""
    prefs = load_preferences()
    
    if not prefs.get("industry"):
        terminal_ui.print_error("No setup found. Run setup first.")
        return None
    
    terminal_ui.print_info(f"Current industry: {prefs['industry']}")
    print()
    
    if prefs.get("companies"):
        terminal_ui.print_info(f"Current companies: {', '.join(prefs['companies'])}")
        print()
    
    update = input("Update companies? [y/n]: ").strip().lower()
    if update in ("y", "yes"):
        companies = add_companies()
        prefs["companies"] = companies
        save_preferences(prefs)
        terminal_ui.print_success("Companies updated!")
    
    return prefs


def view_status():
    """View current setup status."""
    prefs = load_preferences()
    
    if not prefs.get("done_setup"):
        terminal_ui.print_warning("No setup completed. Run 'python main.py --setup' first.")
        return None
    
    summary = ai_resume_analyzer.get_resume_summary(prefs["industry"])
    
    terminal_ui.print_step("CURRENT STATUS")
    print(f"  Industry: {summary['display_name'] if summary else prefs['industry']}")
    print(f"  Companies: {len(prefs.get('companies', []))}")
    for company in prefs.get("companies", []):
        print(f"    - {company}")
    
    return prefs


def main():
    """Main entry point for CLI wizard."""
    import sys
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "--setup":
            run_setup()
        elif cmd == "--update":
            run_update_companies()
        elif cmd == "--status":
            view_status()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: python cli_wizard.py [--setup|--update|--status]")
    else:
        view_status()


if __name__ == "__main__":
    main()