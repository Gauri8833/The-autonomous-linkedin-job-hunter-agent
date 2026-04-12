"""Settings and configuration constants."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Determine base directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
RESUMES_DIR = DATA_DIR / "resumes"

load_dotenv()

LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL", "")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

RESUME_FILE = "resume.txt"
TARGET_COMPANIES = "target_companies.txt"
LOG_FILE = "log.json"

# Data files
PREFERENCES_FILE = DATA_DIR / "preferences.json"
APPLICATIONS_FILE = DATA_DIR / "applications.json"

MAX_POSTS_PER_COMPANY = 3
COMMENT_MAX_CHARS = 500
HEADLESS = False
BROWSER_SLOW_MO = 70
MIN_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 4.5
TYPING_SPEED_MIN_MS = 40
TYPING_SPEED_MAX_MS = 120

# Job search keywords
HIRING_KEYWORDS = [
    "hiring",
    "we are hiring",
    "join our team",
    "open position",
    "job opening",
    "looking for",
    "now hiring",
    "careers",
    "job opportunity",
]

HIRING_SIGNALS = [
    "hiring", "join", "open", "position", "role",
    "looking for", "opportunity", "vacancy", "apply",
    "career", "recruit", "talent", "onboard",
    "job", "application", "resume", "interview",
]

# Industry mappings
INDUSTRY_KEYWORDS = {
    "software_engineering": ["software", "developer", "engineer", "backend", "frontend", "fullstack", "python", "java", "javascript", "api", "cloud", "aws", "docker", "kubernetes"],
    "data_science": ["data scientist", "machine learning", "ml", "ai", "artificial intelligence", "deep learning", "python", "tensorflow", "pytorch", "analytics", "model", "prediction"],
    "product_management": ["product manager", "product", "roadmap", "user research", "agile", "scrum", "stakeholder", "launch", "roadmap"],
    "marketing": ["marketing", "digital marketing", "seo", "content", "social media", "campaign", "brand"],
    "finance": ["finance", "financial", "analyst", "investment", "banking", "accounting"],
    "sales": ["sales", "account executive", "business development", "client", "revenue"],
}

# Available resumes
AVAILABLE_INDUSTRIES = ["software_engineering", "data_science", "product_management"]