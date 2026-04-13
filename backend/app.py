# LinkedIn Job Hunter Backend API
# Flask server for Vercel frontend integration

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# In-memory storage (use database in production)
profiles = {}
jobs = {}
applications = {}
app_counter = 1
job_counter = 1

# Settings storage
settings = {
    "linkedin_email": os.getenv("LINKEDIN_EMAIL", ""),
    "linkedin_password": os.getenv("LINKEDIN_PASSWORD", ""),
    "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
}


@app.route("/")
def home():
    return jsonify({
        "message": "LinkedIn Job Hunter API",
        "version": "2.0.0",
        "status": "running"
    })


@app.route("/health")
def health():
    return jsonify({"status": "healthy"})


# Profile endpoints
@app.route("/api/profile", methods=["GET", "POST", "PUT"])
def profile():
    global profiles
    
    if request.method == "GET":
        if not profiles:
            return jsonify({"error": "No profile found"}), 404
        return jsonify(profiles)
    
    # Create or update profile
    data = request.json or {}
    profiles = {
        "name": data.get("name", ""),
        "email": data.get("email", ""),
        "phone": data.get("phone", ""),
        "linkedin_url": data.get("linkedin_url", ""),
        "github_url": data.get("github_url", ""),
        "summary": data.get("summary", ""),
        "skills": data.get("skills", []),
        "experience": data.get("experience", []),
        "education": data.get("education", []),
        "industries": data.get("industries", []),
        "target_companies": data.get("target_companies", []),
    }
    return jsonify({"message": "Profile saved", "profile": profiles})


@app.route("/api/profile/resume", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["file"]
    filename = file.filename
    
    return jsonify({
        "message": "Resume uploaded",
        "filename": filename
    })


# Jobs endpoints
@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    company = request.args.get("company")
    limit = int(request.args.get("limit", 20))
    
    result = []
    for j in jobs.values():
        if company and company.lower() not in j.get("company", "").lower():
            continue
        result.append(j)
    
    return jsonify({
        "jobs": result[:limit],
        "count": len(result)
    })


@app.route("/api/jobs/scrape", methods=["POST"])
def scrape_jobs():
    global job_counter, jobs
    
    data = request.json or {}
    company = data.get("company", "")
    keywords = data.get("keywords", "hiring")
    limit = data.get("limit", 10)
    
    if not company:
        return jsonify({"error": "No company specified"}), 400
    
    # Mock job data (replace with real LinkedIn scraping)
    # Note: LinkedIn scraping requires Playwright - run locally or use dedicated scraper
    new_jobs = []
    for i in range(min(limit, 3)):
        job_id = f"job_{job_counter}"
        job_counter += 1
        
        job = {
            "id": job_id,
            "company": company,
            "title": f"{keywords.title()} Specialist - {company}",
            "location": "Remote",
            "description": f"Join {company} as a {keywords} specialist. We offer competitive salary and benefits.",
            "requirements": "3+ years experience, relevant skills",
            "url": f"https://linkedin.com/jobs/view/{job_id}",
            "source": "linkedin"
        }
        
        jobs[job_id] = job
        new_jobs.append(job)
    
    return jsonify({
        "jobs": new_jobs,
        "count": len(new_jobs)
    })


# Applications endpoints
@app.route("/api/applications", methods=["GET"])
def get_applications():
    status = request.args.get("status")
    limit = int(request.args.get("limit", 20))
    
    result = []
    for a in applications.values():
        if status and a.get("status") != status:
            continue
        result.append(a)
    
    return jsonify({
        "applications": result[:limit],
        "count": len(result)
    })


@app.route("/api/applications/generate", methods=["POST"])
def generate_applications():
    global app_counter, applications
    
    data = request.json or {}
    job_ids = data.get("job_ids", [])
    
    if not job_ids:
        return jsonify({"error": "No jobs specified"}), 400
    
    if not profiles.get("name"):
        return jsonify({"error": "No profile found. Create profile first."}), 400
    
    # Generate AI applications
    generated = []
    for job_id in job_ids[:10]:
        job = jobs.get(job_id)
        if not job:
            continue
        
        # Mock generated content
        app_id = f"app_{app_counter}"
        app_counter += 1
        
        application = {
            "id": app_id,
            "job_id": job_id,
            "company": job.get("company"),
            "position": job.get("title"),
            "post_url": job.get("url"),
            "resume_text": f"Experienced professional interested in {job.get('title')} role at {job.get('company')}",
            "cover_letter": f"I'm excited about the opportunity to join {job.get('company')} as a {job.get('title')}. My skills align well with your requirements.",
            "match_score": 75,
            "status": "generated",
            "created_at": "2024-01-01"
        }
        
        applications[app_id] = application
        generated.append(application)
    
    return jsonify({
        "applications": generated,
        "count": len(generated)
    })


@app.route("/api/applications/<app_id>", methods=["PUT"])
def update_application(app_id):
    if app_id not in applications:
        return jsonify({"error": "Application not found"}), 404
    
    data = request.json or {}
    applications[app_id].update(data)
    
    return jsonify({"message": "Application updated"})


@app.route("/api/applications/<app_id>/apply", methods=["POST"])
def apply_to_job(app_id):
    if app_id not in applications:
        return jsonify({"error": "Application not found"}), 404
    
    # Update status to applied
    applications[app_id]["status"] = "applied"
    
    return jsonify({
        "message": "Application submitted!",
        "application": applications[app_id]
    })


@app.route("/api/applications/stats", methods=["GET"])
def get_stats():
    all_apps = list(applications.values())
    
    stats = {
        "total": len(all_apps),
        "pending": len([a for a in all_apps if a.get("status") == "pending"]),
        "generated": len([a for a in all_apps if a.get("status") == "generated"]),
        "applied": len([a for a in all_apps if a.get("status") == "applied"]),
        "interview": len([a for a in all_apps if a.get("status") == "interview"]),
        "rejected": len([a for a in all_apps if a.get("status") == "rejected"]),
    }
    
    return jsonify(stats)


# Settings endpoints
@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    global settings
    
    if request.method == "GET":
        # Don't expose passwords
        return jsonify({
            "linkedin_email": settings.get("linkedin_email", "")[:3] + "***" if settings.get("linkedin_email") else "",
            "gemini_api_key": "set" if settings.get("gemini_api_key") else "",
        })
    
    # Update settings
    data = request.json or {}
    if data.get("linkedin_email"):
        settings["linkedin_email"] = data["linkedin_email"]
    if data.get("linkedin_password"):
        settings["linkedin_password"] = data["linkedin_password"]
    if data.get("gemini_api_key"):
        settings["gemini_api_key"] = data["gemini_api_key"]
    
    return jsonify({"message": "Settings updated"})


# Run locally
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)