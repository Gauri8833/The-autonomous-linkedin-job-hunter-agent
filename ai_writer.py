"""Call Gemini API to generate personalised LinkedIn comments."""
import re
import time
import google.generativeai as genai
import config
import terminal_ui


def generate_comment(post_text, company, resume, max_chars):
    genai.configure(api_key=config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""You are a career coach helping a job seeker get noticed on LinkedIn.

TASK: Write a personalised, human-sounding LinkedIn comment on a hiring post. The comment should get the recruiter to click on the candidate's profile.

HIRING POST (from {company}):
---
{post_text[:700]}
---

CANDIDATE'S RESUME:
---
{resume[:1400]}
---

STRICT RULES FOR THE COMMENT:
1. Under {max_chars} characters total
2. Do NOT start the comment with the word "I"
3. Do NOT use these cliché phrases:
   "passionate about", "excited to", "thrilled", "team player", "hard worker", "love to", "would love to", "fast learner", "go-getter", "results-driven"
4. DO mention 1 or 2 SPECIFIC skills or achievements from the resume that directly match what this post is asking for
5. Sound like a real human wrote it — confident, specific, not desperate, not generic
6. End with ONE soft call to action like:
   "Happy to connect if there's a fit."
   OR "Feel free to check my profile."
   OR "DM me if this looks interesting."
7. Zero or one emoji maximum
8. Tone: confident, warm, direct

OUTPUT: Write ONLY the comment text.
No quotes around it. No explanation. Nothing else."""

    try:
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.85, "max_output_tokens": 300}
        )
        comment = _clean_comment(response.text)

        if len(comment) > max_chars:
            comment = comment[:max_chars].rsplit(" ", 1)[0] + "..."

        return comment

    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            terminal_ui.print_warning("Gemini rate limit. Waiting 30 seconds...")
            time.sleep(30)
            try:
                response = model.generate_content(prompt)
                return _clean_comment(response.text)
            except:
                terminal_ui.print_error("AI error after retry.")
                return None
        terminal_ui.print_error(f"AI error: {e}")
        return None


def _clean_comment(text):
    text = text.strip().strip('"').strip("'")
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    text = re.sub(r"^Comment:\s*", "", text, flags=re.IGNORECASE)
    return text.strip()