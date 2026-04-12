LINKEDIN JOB HUNTER AGENT - SETUP GUIDE
=======================================

WHAT THIS DOES
-------------
A local command-line Python tool that:
1. Opens a visible Chromium browser on your computer
2. Logs into LinkedIn using your credentials
3. Searches for hiring posts from target companies
4. Uses Google Gemini AI to generate personalized comments
5. Shows you the comment and asks for approval (y/n/e)
6. Posts the comment on LinkedIn if approved
7. Logs all activity to prevent duplicate commenting

REQUIREMENTS
-----------
- Python 3.10 or higher
- Internet connection
- LinkedIn account
- Google Gemini API key (free)

STEP 1 - INSTALL PYTHON
----------------------
Download from: https://www.python.org/downloads
During installation, make sure to tick "Add Python to PATH"

Verify: python --version

STEP 2 - INSTALL PACKAGES
---------------------
Open terminal/command prompt in this folder and run:

pip install -r requirements.txt

STEP 3 - INSTALL BROWSER
-----------------------
After installing packages, run:

playwright install chromium

STEP 4 - GET GEMINI API KEY
--------------------------
1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

STEP 5 - SETUP CONFIGURATION
-------------------------
1. Rename "env.txt" to ".env"
2. Open .env in a text editor
3. Fill in your values:

LINKEDIN_EMAIL=your_email@gmail.com
LINKEDIN_PASSWORD=your_linkedin_password
GEMINI_API_KEY=AIzaYourAPIKeyHere

STEP 6 - YOUR RESUME
-------------------
Replace the contents of resume.txt with your actual resume in plain text.
Include: Summary, Skills, Experience, Education, Projects.

STEP 7 - YOUR COMPANIES
--------------------
Edit target_companies.txt - one company name per line.
Use names exactly as they appear on LinkedIn.

STEP 8 - RUN IT
--------------
python main.py

WHAT YOU'LL SEE
----------------
1. Banner showing the app
2. Configuration check
3. Browser launches (watch it work!)
4. LinkedIn login prompt
5. For each company: searches posts, generates comments
6. For each post: shows AI comment, asks y/n/e
7. After approval: posts comment
8. Session summary at the end

TROUBLESHOOTING
--------------

LOGIN FAILS
- Check LINKEDIN_EMAIL and LINKEDIN_PASSWORD in .env
- Make sure there are no spaces around the = sign

CAPTCHA / VERIFICATION
- If LinkedIn asks for verification, complete it in the browser
- The script will pause and wait for you

NO POSTS FOUND
- Try different company names
- The search uses multiple keywords

GEMINI ERROR
- Check GEMINI_API_KEY is correct
- Get a fresh key from aistudio.google.com/app/apikey

RATE LIMIT
- The script automatically waits 30 seconds and retries

BROWSER NOT FOUND
- Run: playwright install chromium

For issues, open an issue on GitHub:
https://github.com/Gauri8833/linkedin-hunter/issues