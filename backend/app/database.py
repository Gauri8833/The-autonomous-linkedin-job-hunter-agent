"""Database configuration and models."""
import sqlite3
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager

DATABASE_URL = Path(__file__).parent.parent / "data" / "db.sqlite"

DATABASE_URL.parent.mkdir(exist_ok=True)


def get_db_connection():
    """Get SQLite database connection."""
    conn = sqlite3.connect(str(DATABASE_URL))
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Get database context manager."""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize database tables."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                linkedin_url TEXT,
                github_url TEXT,
                summary TEXT,
                skills TEXT,
                experience TEXT,
                education TEXT,
                industries TEXT,
                target_companies TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Jobs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                company TEXT NOT NULL,
                title TEXT NOT NULL,
                location TEXT,
                description TEXT,
                requirements TEXT,
                url TEXT,
                source TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Applications table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER,
                company TEXT,
                position TEXT,
                post_url TEXT,
                resume_text TEXT,
                cover_letter TEXT,
                match_score INTEGER,
                status TEXT DEFAULT 'pending',
                applied_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES jobs (id)
            )
        """)
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        conn.commit()


def create_profile(name, email, phone=None, linkedin_url=None, github_url=None, summary=None):
    """Create or update profile."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO profile 
            (name, email, phone, linkedin_url, github_url, summary, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, email, phone, linkedin_url, github_url, summary, datetime.now()))
        conn.commit()
        return cursor.lastrowid


def get_profile():
    """Get profile."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profile ORDER BY id DESC LIMIT 1")
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def update_profile(**kwargs):
    """Update profile fields."""
    fields = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [datetime.now()]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE profile SET {fields} WHERE id = (SELECT MAX(id) FROM profile)", values)
        conn.commit()


def save_job(job_id, company, title, location=None, description=None, requirements=None, url=None, source="linkedin"):
    """Save job to database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO jobs 
            (job_id, company, title, location, description, requirements, url, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, company, title, location, description, requirements, url, source))
        conn.commit()
        return cursor.lastrowid


def get_jobs(company=None, limit=20):
    """Get jobs."""
    with get_db() as conn:
        cursor = conn.cursor()
        if company:
            cursor.execute("SELECT * FROM jobs WHERE company LIKE ? ORDER BY scraped_at DESC LIMIT ?", (f"%{company}%", limit))
        else:
            cursor.execute("SELECT * FROM jobs ORDER BY scraped_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def save_application(job_id, company, position, post_url, resume_text=None, cover_letter=None, match_score=0):
    """Save application."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications 
            (job_id, company, position, post_url, resume_text, cover_letter, match_score, applied_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, company, position, post_url, resume_text, cover_letter, match_score, datetime.now()))
        conn.commit()
        return cursor.lastrowid


def get_applications(status=None, limit=20):
    """Get applications."""
    with get_db() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute("SELECT * FROM applications WHERE status = ? ORDER BY created_at DESC LIMIT ?", (status, limit))
        else:
            cursor.execute("SELECT * FROM applications ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]


def update_application_status(app_id, status):
    """Update application status."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE applications SET status = ? WHERE id = ?", (status, app_id))
        conn.commit()


def get_setting(key):
    """Get setting value."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row["value"] if row else None


def set_setting(key, value):
    """Set setting value."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()


init_db()