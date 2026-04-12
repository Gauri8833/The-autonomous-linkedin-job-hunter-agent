"""Dynamic Resume Customizer - Customizes resume for specific job posts."""
import json
import re
import google.generativeai as genai
import config
import terminal_ui
import ai_resume_analyzer


def customize_resume_for_job(resume, job_requirements, job_text):
    """Dynamically customize resume highlights for a specific job.
    
    Returns customized highlights that match the job requirements.
    """
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    # Build prompt with resume info and job requirements
    prompt = f"""You are an expert resume customizer. Your task is to create 2-3 highly personalized bullet points that connect the candidate's experience to this specific job.

CANDIDATE RESUME:
---
Industry: {resume.get('industry')}
Display Name: {resume.get('display_name')}
Summary: {resume.get('summary')}

SKILLS:
{json.dumps(resume.get('skills', {}), indent=2)}

EXPERIENCE:
{json.dumps(resume.get('experience', []), indent=2)}

JOB REQUIREMENTS:
{json.dumps(job_requirements, indent=2)}

JOB POST (for context):
---
{job_text[:800]}
---

TASK:
Create 2-3 bullet points (each 15-30 words) that:
1. Directly match candidate skills to job requirements
2. Use numbers/metrics where possible (e.g., "40% improvement", "$2M savings")
3. Sound natural and confident (not desperate)
4. Reference specific technologies mentioned in job
5. Bridge any gap between resume skills and job needs

OUTPUT FORMAT:
Respond ONLY with bullet points, one per line. Start each with action verb.
Example output:
- Built REST APIs handling 50K+ daily requests using Python and PostgreSQL
- Reduced system latency by 40% through Redis caching optimization
- Led migration from monolithic to microservices architecture on AWS

No other text. Just the bullet points."""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.7, "max_output_tokens": 300}
        )
        
        bullets = []
        for line in response.text.strip().split("\n"):
            line = line.strip()
            line = re.sub(r"^[\d\.\)\-•\*]+\s*", "", line)
            if line and len(line) > 10:
                bullets.append(line)
        
        return bullets[:3]
        
    except Exception as e:
        terminal_ui.print_error(f"Error customizing resume: {e}")
        return None


def generate_cover_snippet(resume, job_requirements, job_title):
    """Generate a short cover letter snippet for the job."""
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
    
    key_skills = job_requirements.get("required_skills", [])[:5]
    top_skill = key_skills[0] if key_skills else "technology"
    
    prompt = f"""Write a SHORT, impactful LinkedIn comment (under 200 words) for a job post.

JOB: {job_title}
TOP SKILLS NEEDED: {key_skills}

CANDIDATE PROFILE:
- Industry: {resume.get('display_name')}
- Summary: {resume.get('summary')[:200]}

RULES:
1. Start with something specific about THEIR company/product (not "I")
2. Mention 1-2 relevant skills that match the job
3. Include ONE metric/achievement from your experience
4. End with soft call to action: "Happy to connect" or "DM me"
5. Sound confident, not desperate
6. ZERO clichés (no "passionate", "excited", "team player")

OUTPUT: Just the comment. No quotes. Max 200 words."""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.85, "max_output_tokens": 300}
        )
        
        text = response.text.strip()
        text = re.sub(r"^[\"']", "", text)
        text = re.sub(r"[\"']$", "", text)
        text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
        
        if len(text) > 500:
            text = text[:500].rsplit(" ", 1)[0] + "..."
        
        return text
        
    except Exception as e:
        terminal_ui.print_error(f"Error generating cover snippet: {e}")
        return None


def extract_keywords_from_job(job_text):
    """Extract key requirements/keywords from job post."""
    analyzer = ai_resume_analyzer.analyze_job_requirements(job_text)
    if not analyzer:
        return {"required": [], "preferred": []}
    
    return {
        "required": analyzer.get("required_skills", []),
        "preferred": analyzer.get("preferred_skills", [])
    }


def match_resume_to_job(resume, job_text):
    """Full analysis: match resume to job and return insights."""
    # First analyze job
    job_req = ai_resume_analyzer.analyze_job_requirements(job_text)
    if not job_req:
        return None
    
    # Calculate match score
    match_score = ai_resume_analyzer.calculate_skill_match(
        resume.get("skills", {}),
        job_req
    )
    
    # Get experience level match
    resume_exp = ai_resume_analyzer.detect_experience_level(
        resume.get("experience", [])
    )
    job_exp = job_req.get("experience_years", "0")
    
    return {
        "job_title": job_req.get("title"),
        "match_score": match_score,
        "resume_experience_level": resume_exp,
        "required_experience": job_exp,
        "key_skills_matched": job_req.get("required_skills", [])[:5],
        "missing_skills": [],  # Could calculate this
        "customized_bullets": customize_resume_for_job(resume, job_req, job_text),
    }


