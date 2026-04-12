"""AI service for generating tailored resumes and cover letters."""
import json
import re
import google.generativeai as genai
from typing import Dict, Optional, List

import database


def get_gemini_model():
    """Get configured Gemini model."""
    api_key = database.get_setting("gemini_api_key")
    if not api_key:
        raise Exception("Gemini API key not configured")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


async def generate_application(
    job_title: str,
    job_description: str,
    job_requirements: str,
    profile: Dict,
) -> Dict:
    """Generate AI-tailored resume/cover letter for a job."""
    model = get_gemini_model()
    
    # Get profile data
    skills = json.loads(database.get_setting("skills") or "[]")
    experience = json.loads(database.get_setting("experience") or "[]")
    education = json.loads(database.get_setting("education") or "[]")
    resume_text = database.get_setting("resume_text") or ""
    
    prompt = f"""You are an expert career counselor. Create a personalized application for a job.

JOB:
Title: {job_title}
Description: {job_description}
Requirements: {job_requirements}

CANDIDATE PROFILE:
Name: {profile.get('name')}
Email: {profile.get('email')}
Summary: {profile.get('summary')}
Skills: {', '.join(skills) if skills else 'Not specified'}
Experience: {json.dumps(experience) if experience else 'Not specified'}
Education: {json.dumps(education) if education else 'Not specified'}

TASK:
1. Create a tailored resume (3 bullet points highlighting relevant experience)
2. Create a cover letter (under 200 words)
3. Calculate match score (0-100%)

RULES:
- Match specific skills from job requirements to candidate's experience
- Include metrics where possible
- Sound confident, not desperate
- No clichés (no "passionate", "excited", "team player")
- End with soft call to action

OUTPUT (JSON format):
{{
  "resume_text": "bullet point 1\\nbullet point 2\\nbullet point 3",
  "cover_letter": "cover letter text",
  "match_score": 75
}}

Respond ONLY with valid JSON. No explanation."""

    try:
        response = model.generate_content(prompt)
        
        # Parse response
        text = response.text.strip()
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"^```", "", text)
        text = re.sub(r"```$", "", text)
        
        result = json.loads(text)
        
        return {
            "resume_text": result.get("resume_text", ""),
            "cover_letter": result.get("cover_letter", ""),
            "match_score": result.get("match_score", 0),
        }
    
    except Exception as e:
        print(f"Error generating: {e}")
        return {
            "resume_text": f"Experienced {profile.get('name')} interested in {job_title} role",
            "cover_letter": f"I'm interested in the {job_title} position at the company. " + 
                          f"My skills and experience align well with the requirements.",
            "match_score": 50,
        }


async def analyze_job_requirements(job_text: str) -> Dict:
    """Analyze job post and extract requirements."""
    model = get_gemini_model()
    
    prompt = f"""Analyze this job posting and extract requirements.

JOB POST:
---
{job_text[:1500]}
---

OUTPUT (JSON):
{{
  "title": "job title",
  "required_skills": ["skill1", "skill2"],
  "preferred_skills": ["skill1"],
  "experience_years": "X years",
  "education": "required education",
  "key_responsibilities": ["duty1"],
  "benefits": ["benefit1"],
  "location": "location"
}}

Respond ONLY with valid JSON."""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        text = re.sub(r"^```json", "", text)
        text = re.sub(r"```$", "", text)
        
        return json.loads(text)
    
    except:
        return {
            "title": "Unknown",
            "required_skills": [],
            "preferred_skills": [],
            "experience_years": "0",
            "education": "",
            "key_responsibilities": [],
            "benefits": [],
            "location": "",
        }


async def match_resume_to_job(resume_skills: List[str], job_skills: List[str]) -> int:
    """Calculate match percentage."""
    if not job_skills:
        return 50
    
    resume_skills_lower = [s.lower() for s in resume_skills]
    matches = 0
    
    for job_skill in job_skills:
        for resume_skill in resume_skills_lower:
            if job_skill.lower() in resume_skill or resume_skill in job_skill.lower():
                matches += 1
                break
    
    return min(100, int((matches / len(job_skills)) * 100))