"""AI Resume Analyzer - Analyzes resumes and extracts key information."""
import json
import re
from pathlib import Path
import google.generativeai as genai
import config
import terminal_ui


def load_resume(industry=None):
    """Load resume for given industry or list all available."""
    resumes = {}
    
    if not config.RESUMES_DIR.exists():
        return None
    
    for resume_file in config.RESUMES_DIR.glob("*.json"):
        try:
            with open(resume_file, "r") as f:
                resumes[resume_file.stem] = json.load(f)
        except:
            continue
    
    if industry:
        return resumes.get(industry)
    return resumes


def get_available_industries():
    """Get list of industries with available resumes."""
    resumes = load_resume()
    if not resumes:
        return []
    return list(resumes.keys())


def list_resumes():
    """Display available resumes."""
    resumes = load_resume()
    if not resumes:
        terminal_ui.print_warning("No resumes found. Run setup first.")
        return []
    
    for industry, resume in resumes.items():
        display = resume.get("display_name", industry)
        skills_count = len(resume.get("skills", {}))
        terminal_ui.print_info(f"  - {display} ({industry}) - {skills_count} skill categories")
    
    return list(resumes.keys())


def analyze_job_requirements(job_text):
    """Analyze job post and extract requirements using AI."""
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    prompt = f"""Analyze this job posting and extract key requirements.

JOB POST:
---
{job_text[:1500]}
---

Respond in JSON format:
{{
  "title": "detected job title",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["nice to have"],
  "experience_years": "X years",
  "education": "required education",
  "key_responsibilities": ["duty1", "duty2"],
  "soft_skills": ["communication", "teamwork"],
  "benefits": ["benefit1"],
  "location": "location if mentioned",
  "salary_range": "if mentioned"
}}

Only output valid JSON. No explanation."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)
        return json.loads(text)
    except json.JSONDecodeError:
        terminal_ui.print_error("Failed to parse job requirements")
        return None
    except Exception as e:
        terminal_ui.print_error(f"Error analyzing job: {e}")
        return None


def extract_skills_from_text(text):
    """Extract skills from any text using pattern matching."""
    text = text.lower()
    
    # Technical skills patterns
    programming_languages = [
        "python", "java", "javascript", "typescript", "go", "golang", "rust",
        "c++", "c#", "ruby", "php", "swift", "kotlin", "scala", "r"
    ]
    
    frameworks = [
        "django", "fastapi", "flask", "react", "angular", "vue", "nodejs",
        "express", "spring", "rails", "laravel", "nextjs"
    ]
    
    databases = [
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "cassandra", "dynamodb", "oracle", "sql server"
    ]
    
    cloud = ["aws", "azure", "gcp", "google cloud", "heroku"]
    
    tools = [
        "docker", "kubernetes", "git", "jenkins", "terraform", "ansible",
        "jira", "confluence", "figma"
    ]
    
    ml_tools = [
        "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
        "numpy", "matplotlib", "opencv"
    ]
    
    found = {
        "programming": [],
        "frameworks": [],
        "databases": [],
        "cloud": tools,
        "ml": [],
        "other": []
    }
    
    text_lower = text.lower()
    
    for skill in programming_languages:
        if skill in text_lower:
            found["programming"].append(skill)
    
    for skill in frameworks:
        if skill in text_lower:
            found["frameworks"].append(skill)
    
    for skill in databases:
        if skill in text_lower:
            found["databases"].append(skill)
    
    for skill in cloud:
        if skill in text_lower:
            found["cloud"].append(skill)
    
    for skill in ml_tools:
        if skill in text_lower:
            found["ml"].append(skill)
    
    return found


def calculate_skill_match(resume_skills, job_requirements):
    """Calculate percentage match between resume skills and job requirements."""
    if not resume_skills or not job_requirements:
        return 0
    
    resume_skills_flat = []
    for category, skills in resume_skills.items():
        if isinstance(skills, list):
            resume_skills_flat.extend([s.lower() for s in skills])
        elif isinstance(skills, dict):
            for subcategory, subskills in skills.items():
                if isinstance(subskills, list):
                    resume_skills_flat.extend([s.lower() for s in subskills])
    
    job_skills = []
    for skill in job_requirements.get("required_skills", []):
        job_skills.append(skill.lower())
    for skill in job_requirements.get("preferred_skills", []):
        job_skills.append(skill.lower())
    
    if not job_skills:
        return 50
    
    matches = 0
    for job_skill in job_skills:
        for resume_skill in resume_skills_flat:
            if job_skill in resume_skill or resume_skill in job_skill:
                matches += 1
                break
    
    return min(100, int((matches / len(job_skills)) * 100))


def detect_experience_level(experience_list):
    """Detect overall experience level from experience entries."""
    total_years = 0
    
    for exp in experience_list:
        duration = exp.get("duration", "")
        # Extract years from duration string
        years = re.findall(r"(\d+)\s*[-–]\s*(\d+|Present)", duration)
        for start, end in years:
            if end == "Present":
                end = "2026"
            try:
                total_years += int(end) - int(start)
            except:
                continue
    
    if total_years >= 5:
        return "Senior"
    elif total_years >= 3:
        return "Mid-Level"
    elif total_years >= 1:
        return "Junior"
    else:
        return "Entry-Level"


def get_resume_summary(industry):
    """Get a formatted summary of resume for a given industry."""
    resume = load_resume(industry)
    if not resume:
        return None
    
    summary = {
        "industry": resume.get("industry"),
        "display_name": resume.get("display_name"),
        "summary": resume.get("summary"),
        "skills": resume.get("skills", {}),
        "experience_count": len(resume.get("experience", [])),
        "experience_level": detect_experience_level(resume.get("experience", [])),
    }
    
    return summary