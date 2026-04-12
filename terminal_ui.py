"""All terminal display functions using ANSI escape codes."""
import sys

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner():
    print(f"{CYAN}{BOLD}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║       LinkedIn Job Hunter Agent                  ║")
    print("║       Powered by Gemini AI  |  Cost: ₹0          ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(RESET)


def print_step(message):
    print(f"{CYAN}[STEP] {message}{RESET}")


def print_success(message):
    print(f"{GREEN}✓ {message}{RESET}")


def print_warning(message):
    print(f"{YELLOW}⚠  {message}{RESET}")


def print_error(message):
    print(f"{RED}✗ {message}{RESET}")


def print_info(message):
    print(f"{DIM}  {message}{RESET}")


def print_company_header(company, index, total):
    print(f"\n{BOLD}──────────────────────────────────────────────────────{RESET}")
    print(f"{BOLD}🏢  Company [{index}/{total}]: {company}{RESET}")
    print(f"{BOLD}──────────────────────────────────────────────────────{RESET}")


def print_post_preview(index, total, url, text):
    trunc_url = url[:70] + "..." if len(url) > 70 else url
    trunc_text = text[:200] + "..." if len(text) > 200 else text
    print(f"\n  Post {index}/{total}")
    print(f"  URL : {trunc_url}")
    print(f"{DIM}  Text: {trunc_text}{RESET}")


def print_comment_box(comment):
    lines = _wrap_text(comment, 50)
    width = 54
    print(f"{WHITE}{BOLD}")
    print("┌" + "─" * width + "┐")
    print("│" + " ✨ AI-Generated Comment".ljust(width) + "│")
    print("├" + "─" * width + "┤")
    for line in lines:
        print("│" + line.ljust(width) + "│")
    print("└" + "─" * width + "┘")
    print(RESET)


def _wrap_text(text, width):
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= width:
            current += (" " if current else "") + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines if lines else [""]


def ask_approval(comment):
    while True:
        print_comment_box(comment)
        choice = input("Post this comment? [y = post / n = skip / e = edit]: ").strip().lower()
        if choice in ("y", "n", "e"):
            return choice


def ask_edited_comment():
    print("Type your edited comment below.")
    print("Press Enter twice when finished.")
    lines = []
    empty_count = 0
    while True:
        line = input()
        if not line:
            empty_count += 1
            if empty_count >= 2:
                break
        else:
            empty_count = 0
            lines.append(line)
        if empty_count >= 2:
            break
    return "\n".join(lines).strip()


def print_session_summary(posted, skipped, errors, log_path):
    total = posted + skipped + errors
    print(f"\n{BOLD}──────────────────────────────────────────────────────{RESET}")
    print(f"{BOLD}                    SESSION SUMMARY{RESET}")
    print(f"{BOLD}──────────────────────────────────────────────────────{RESET}")
    print(f"  Posts processed: {total}")
    print(f"  Comments posted: {GREEN}{posted}{RESET}")
    print(f"  Skipped: {YELLOW}{skipped}{RESET}")
    print(f"  Errors: {RED}{errors}{RESET}")
    print(f"  Log file: {log_path}")
    print(RESET)


def print_duplicate_skip(post_id):
    print(f"{YELLOW}⏭  Already commented on this post — skipping{RESET}")


def print_job_match_info(job_title, match_score, resume_exp, required_exp):
    """Print job match information."""
    score_color = GREEN if match_score >= 70 else (YELLOW if match_score >= 50 else RED)
    print(f"\n  Job Title: {job_title}")
    print(f"  Match Score: {score_color}{match_score}%{RESET}")
    print(f"  Your Level: {resume_exp} | Required: {required_exp}")


def print_resume_summary(resume):
    """Print resume summary."""
    if not resume:
        return
    print(f"\n{BOLD}── Resume Summary ──{RESET}")
    print(f"  Industry: {resume.get('display_name')}")
    print(f"  Summary: {resume.get('summary')[:100]}...")
    skills = resume.get("skills", {})
    print(f"  Skills: {len(skills)} categories")
    for category, skill_list in skills.items():
        if isinstance(skill_list, list):
            print(f"    - {category}: {', '.join(skill_list[:5])}")


def print_banner_agentic():
    """Print agentic version banner."""
    print(f"{CYAN}{BOLD}")
    print("╔══════════════════════════════════════════════════════╗")
    print("║   🎯 LinkedIn Job Hunter Agent (Agentic)            ║")
    print("║   AI-Powered Resume Customization              ║")
    print("║   Cost: ₹0 (Free Gemini API)                 ║")
    print("╚══════════════════════════════════════════════════════╝")
    print(RESET)


def ask_continue(prompt_msg="Continue?"):
    """Ask user yes/no question."""
    while True:
        response = input(f"{prompt_msg} [y/n]: ").strip().lower()
        if response in ("y", "yes"):
            return True
        elif response in ("n", "no"):
            return False


def print_match_percentage(percentage, label=""):
    """Print match percentage with color coding."""
    if percentage >= 70:
        color = GREEN
        emoji = "🔥"
    elif percentage >= 50:
        color = YELLOW
        emoji = "◐"
    else:
        color = RED
        emoji = "○"
    
    if label:
        print(f"{color}{emoji} {label}: {percentage}%{RESET}")
    else:
        print(f"{color}{emoji} Match: {percentage}%{RESET}")