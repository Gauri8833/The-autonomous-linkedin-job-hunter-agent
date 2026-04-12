# LinkedIn Job Hunter Agent - Specification v2.0 (Fully Agentic)

## Overview
An autonomous AI agent that logs into LinkedIn, searches for job posts in user-selected industries/companies, analyzes job requirements, dynamically customizes the user's resume to match, and posts personalized comments to maximize interview chances.

## Core Features

### 1. Multi-Industry Resume System
- Users create resumes for different industries (Tech, Finance, Marketing, etc.)
- Each resume has: industry标签, summary, skills, experience, projects
- AI selects the best resume for each job

### 2. AI Resume Analyzer
- Extracts skills (technical, soft, languages)
- Identifies years of experience
- Maps experience levels (Junior/Mid/Senior/Lead)
- Scores match percentage with job requirements

### 3. Dynamic Resume Customizer
- For each job post, AI rewrites resume highlights
- Matches specific keywords from job to user's experience
- Creates 2-3 bullet points specifically relevant to that job
- Ensures ATS compatibility

### 4. CLI Industry/Company Selector
- Interactive wizard: select industry → select companies
- Validates companies exist on LinkedIn
- Saves preferences for future runs

### 5. Enhanced Job Matching
- Uses semantic matching (not just keyword)
- Considers: job title, requirements, benefits, culture
- Ranks posts by match score

### 6. Application Tracker
- Tracks: company, position, post URL, date, status
- Status: applied, interview, rejected, offer
- Export to CSV

## File Structure (v2.0)

```
linkedin-hunter/
├── main.py                 # Main orchestrator
├── config.py              # Settings
├── terminal_ui.py        # UI
├── logger.py              # Logging
├── browser.py             # Browser automation
├── linkedin_login.py     # Login
├── linkedin_search.py     # Job search
├── linkedin_comment.py    # Post comments
├── ai_resume_analyzer.py  # NEW: Analyze resume
├── ai_resume_customizer.py # NEW: Dynamic customization
├── ai_job_matcher.py    # NEW: Match resume to job
├── cli_wizard.py          # NEW: Industry/company selector
├── application_tracker.py # NEW: Track applications
├── data/
│   ├── resumes/          # Multiple industry resumes
│   │   ├── tech.json
│   │   ├── finance.json
│   │   └── marketing.json
│   ├── preferences.json  # Saved company choices
│   └── applications.json # Application history
└── requirements.txt
```

## Workflow

1. **Setup** (first time)
   - cli_wizard.py → Select industry → Enter companies
   - Create resume for that industry (data/resumes/{industry}.json)

2. **Run** (each time)
   - main.py loads preferences
   - Logs into LinkedIn
   - For each company:
     - Search jobs
     - For each post:
       - ai_resume_analyzer.py → Analyze job requirements
       - ai_job_matcher.py → Score match
       - ai_resume_customizer.py → Customize resume for this job
       - ai_writer.py → Generate personalized comment
       - User approves
       - Post comment
       - application_tracker.py → Log activity

## Resume Format (JSON)

```json
{
  "industry": "software_engineering",
  "display_name": "Software Engineer",
  "summary": "Backend engineer with 3+ years...",
  "skills": {
    "languages": ["Python", "Go", "JavaScript"],
    "frameworks": ["Django", "FastAPI", "React"],
    "databases": ["PostgreSQL", "Redis"],
    "cloud": ["AWS", "GCP"],
    "tools": ["Docker", "Kubernetes", "Git"]
  },
  "experience": [
    {
      "title": "Senior Backend Engineer",
      "company": "TechCorp",
      "duration": "2022-Present",
      "highlights": [
        "Built APIs handling 50K+ requests/day",
        "Reduced response time by 40%"
      ]
    }
  ],
  "education": [...],
  "certifications": [...]
}
```

## AI Customization Prompt Example

Input: Job requires "Python, Django, PostgreSQL, AWS"
User resume has: "Python, FastAPI, Redis, AWS"

AI generates:
- "3+ years building REST APIs with Python (Django/FastAPI)"
- "Experience with PostgreSQL and Redis caching"
- "Deployed scalable services on AWS cloud"

This bridges the gap between user skills and job requirements.

## Cost: ₹0 (Free Tier)

- Gemini 1.5 Flash: 15 RPM, 1M tokens/minute (FREE)
- Playwright: Free open source
- Total: ₹0/month