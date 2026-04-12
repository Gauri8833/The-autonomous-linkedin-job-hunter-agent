"""Settings and configuration constants."""
import os
from dotenv import load_dotenv

load_dotenv()

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

RESUME_FILE = "resume.txt"
TARGET_COMPANIES = "target_companies.txt"
LOG_FILE = "log.json"

MAX_POSTS_PER_COMPANY = 3
COMMENT_MAX_CHARS = 500
HEADLESS = False
BROWSER_SLOW_MO = 70
MIN_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 4.5
TYPING_SPEED_MIN_MS = 40
TYPING_SPEED_MAX_MS = 120

HIRING_KEYWORDS = [
    "hiring",
    "we are hiring",
    "join our team",
    "open position",
    "job opening",
    "looking for",
    "now hiring",
]

HIRING_SIGNALS = [
    "hiring", "join", "open", "position", "role",
    "looking for", "opportunity", "vacancy", "apply",
    "career", "recruit", "talent", "onboard",
]