"""FastAPI main application."""
import os
import json
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import database
import linkedin_service
import ai_service

# Models
class ProfileCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    summary: Optional[str] = None
    skills: Optional[List[str]] = []
    experience: Optional[List[dict]] = []
    education: Optional[List[dict]] = []
    industries: Optional[List[str]] = []
    target_companies: Optional[List[str]] = []


class JobSearch(BaseModel):
    company: Optional[str] = None
    keywords: Optional[str] = None
    limit: int = 10


class ApplicationUpdate(BaseModel):
    status: str
    resume_text: Optional[str] = None
    cover_letter: Optional[str] = None


# Initialize database
database.init_db()

# Create app
app = FastAPI(
    title="LinkedIn Job Hunter API",
    description="AI-powered LinkedIn job application automation",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "LinkedIn Job Hunter API", "version": "2.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


# Profile endpoints
@app.post("/api/profile")
async def create_profile(profile: ProfileCreate):
    """Create or update profile."""
    db_id = database.create_profile(
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        summary=profile.summary,
    )
    
    # Save additional JSON fields
    if profile.skills:
        database.set_setting("skills", json.dumps(profile.skills))
    if profile.experience:
        database.set_setting("experience", json.dumps(profile.experience))
    if profile.education:
        database.set_setting("education", json.dumps(profile.education))
    if profile.industries:
        database.set_setting("industries", json.dumps(profile.industries))
    if profile.target_companies:
        database.set_setting("target_companies", json.dumps(profile.target_companies))
    
    return {"id": db_id, "message": "Profile saved"}


@app.get("/api/profile")
async def get_profile():
    """Get current profile."""
    profile = database.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="No profile found")
    
    # Add JSON fields
    profile["skills"] = json.loads(database.get_setting("skills") or "[]")
    profile["experience"] = json.loads(database.get_setting("experience") or "[]")
    profile["education"] = json.loads(database.get_setting("education") or "[]")
    profile["industries"] = json.loads(database.get_setting("industries") or "[]")
    profile["target_companies"] = json.loads(database.get_setting("target_companies") or "[]")
    
    return profile


@app.put("/api/profile")
async def update_profile(profile: ProfileCreate):
    """Update profile."""
    db_profile = database.get_profile()
    if not db_profile:
        raise HTTPException(status_code=404, detail="No profile found")
    
    database.create_profile(
        name=profile.name,
        email=profile.email,
        phone=profile.phone,
        linkedin_url=profile.linkedin_url,
        github_url=profile.github_url,
        summary=profile.summary,
    )
    
    if profile.skills:
        database.set_setting("skills", json.dumps(profile.skills))
    if profile.experience:
        database.set_setting("experience", json.dumps(profile.experience))
    if profile.education:
        database.set_setting("education", json.dumps(profile.education))
    if profile.industries:
        database.set_setting("industries", json.dumps(profile.industries))
    if profile.target_companies:
        database.set_setting("target_companies", json.dumps(profile.target_companies))
    
    return {"message": "Profile updated"}


@app.post("/api/profile/resume")
async def upload_resume(file: UploadFile = File(...)):
    """Upload resume file."""
    contents = await file.read()
    
    # Save to file
    resume_dir = Path(__file__).parent.parent / "data" / "resumes"
    resume_dir.mkdir(exist_ok=True)
    
    file_path = resume_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Extract text if PDF
    text = ""
    if file.filename.endswith(".txt"):
        text = contents.decode("utf-8")
    elif file.filename.endswith(".pdf"):
        # Would need PDF parser
        text = "PDF resume uploaded"
    
    database.set_setting("resume_text", text)
    database.set_setting("resume_file", str(file_path))
    
    return {"message": "Resume uploaded", "path": str(file_path)}


# Jobs endpoints
@app.post("/api/jobs/scrape")
async def scrape_jobs(search: JobSearch):
    """Scrape jobs from LinkedIn."""
    profile = database.get_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="No profile found")
    
    companies = search.company or json.loads(database.get_setting("target_companies") or "[]")
    if not companies:
        raise HTTPException(status_code=400, detail="No target companies found")
    
    jobs = []
    for company in companies[:5]:  # Limit to 5 companies
        try:
            company_jobs = await linkedin_service.scrape_jobs(company, search.keywords, search.limit)
            jobs.extend(company_jobs)
            
            # Save to database
            for job in company_jobs:
                database.save_job(
                    job_id=job.get("id"),
                    company=job.get("company"),
                    title=job.get("title"),
                    location=job.get("location"),
                    description=job.get("description"),
                    requirements=job.get("requirements"),
                    url=job.get("url"),
                )
        except Exception as e:
            print(f"Error scraping {company}: {e}")
    
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/jobs")
async def get_jobs(company: str = None, limit: int = 20):
    """Get scraped jobs."""
    jobs = database.get_jobs(company, limit)
    return {"jobs": jobs, "count": len(jobs)}


@app.get("/api/jobs/{job_id}")
async def get_job(job_id: int):
    """Get job details."""
    jobs = database.get_jobs(limit=100)
    for job in jobs:
        if job["id"] == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")


# Applications endpoints
@app.post("/api/applications/generate")
async def generate_applications(job_ids: List[int] = None):
    """Generate AI-tailored applications for jobs."""
    profile = database.get_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="No profile found")
    
    # Get jobs
    jobs = database.get_jobs(limit=50)
    if job_ids:
        jobs = [j for j in jobs if j["id"] in job_ids]
    
    applications = []
    for job in jobs[:10]:  # Limit to 10
        try:
            # Generate tailored resume/cover letter
            result = await ai_service.generate_application(
                job_title=job.get("title"),
                job_description=job.get("description"),
                job_requirements=job.get("requirements"),
                profile=profile,
            )
            
            # Save application
            app_id = database.save_application(
                job_id=job.get("id"),
                company=job.get("company"),
                position=job.get("title"),
                post_url=job.get("url"),
                resume_text=result.get("resume_text"),
                cover_letter=result.get("cover_letter"),
                match_score=result.get("match_score", 0),
            )
            
            applications.append({
                "id": app_id,
                "job": job,
                "generated": result,
            })
        except Exception as e:
            print(f"Error generating application: {e}")
    
    return {"applications": applications, "count": len(applications)}


@app.get("/api/applications")
async def get_applications(status: str = None, limit: int = 20):
    """Get applications."""
    apps = database.get_applications(status, limit)
    return {"applications": apps, "count": len(apps)}


@app.get("/api/applications/{app_id}")
async def get_application(app_id: int):
    """Get application details."""
    apps = database.get_applications(limit=100)
    for app in apps:
        if app["id"] == app_id:
            return app
    raise HTTPException(status_code=404, detail="Application not found")


@app.put("/api/applications/{app_id}")
async def update_application(app_id: int, update: ApplicationUpdate):
    """Update application."""
    if update.resume_text:
        database.set_setting(f"app_{app_id}_resume", update.resume_text)
    if update.cover_letter:
        database.set_setting(f"app_{app_id}_cover", update.cover_letter)
    
    database.update_application_status(update.status, app_id)
    return {"message": "Application updated"}


@app.post("/api/applications/{app_id}/apply")
async def apply_to_job(app_id: int):
    """Submit application to LinkedIn."""
    apps = database.get_applications(limit=100)
    app = None
    for a in apps:
        if a["id"] == app_id:
            app = a
            break
    
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    
    # Submit via LinkedIn
    try:
        result = await linkedin_service.post_comment(
            post_url=app["post_url"],
            comment=app["cover_letter"] or app["resume_text"],
        )
        
        if result:
            database.update_application_status("applied", app_id)
            return {"message": "Application submitted!"}
        else:
            return {"message": "Failed to submit"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/applications/stats")
async def get_stats():
    """Get application statistics."""
    all_apps = database.get_applications(limit=1000)
    
    stats = {
        "total": len(all_apps),
        "pending": len([a for a in all_apps if a["status"] == "pending"]),
        "applied": len([a for a in all_apps if a["status"] == "applied"]),
        "interview": len([a for a in all_apps if a["status"] == "interview"]),
        "rejected": len([a for a in all_apps if a["status"] == "rejected"]),
        "offer": len([a for a in all_apps if a["status"] == "offer"]),
    }
    
    return stats


# Settings endpoints
@app.get("/api/settings")
async def get_settings():
    """Get all settings."""
    return {
        "linkedin_email": database.get_setting("linkedin_email"),
        "linkedin_password": database.get_setting("linkedin_password"),
        "gemini_api_key": database.get_setting("gemini_api_key"),
    }


@app.post("/api/settings")
async def update_settings(
    linkedin_email: str = Form(None),
    linkedin_password: str = Form(None),
    gemini_api_key: str = Form(None),
):
    """Update settings."""
    if linkedin_email:
        database.set_setting("linkedin_email", linkedin_email)
    if linkedin_password:
        database.set_setting("linkedin_password", linkedin_password)
    if gemini_api_key:
        database.set_setting("gemini_api_key", gemini_api_key)
    
    return {"message": "Settings updated"}


# Run locally
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)