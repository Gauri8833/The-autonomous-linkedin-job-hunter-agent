"""LinkedIn Job Hunter Agent - FastAPI Backend."""
import queue
import threading
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import existing modules
import browser
import linkedin_login
import linkedin_search
import linkedin_comment
import ai_writer
import logger
import config

# Create FastAPI app
app = FastAPI(title="LinkedIn Job Hunter Agent")

# CORS - Allow ALL origins, methods, headers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# GLOBAL STATE
# ============================================================
agent_thread: Optional[threading.Thread] = None
message_queue = queue.Queue()
approval_event = threading.Event()
approval_decision = {"action": "n", "comment": ""}
is_running = False
stop_requested = False


# ============================================================
# Pydantic models
# ============================================================
class StartRequest(BaseModel):
    linkedin_email: str
    linkedin_password: str
    gemini_api_key: str
    companies: list[str]
    resume: str


class ApproveRequest(BaseModel):
    action: str
    comment: Optional[str] = ""


# ============================================================
# HELPER FUNCTIONS
# ============================================================
def send(message: str, level: str = "info", msg_type: str = "log"):
    """Put a message into the queue."""
    import json
    data = {"type": msg_type, "message": message, "level": level}
    message_queue.put(json.dumps(data))


def run_agent(email: str, password: str, gemini_key: str, companies: list[str], resume: str):
    """Background thread that runs the LinkedIn agent."""
    global is_running, stop_requested
    
    send("Starting agent...", "info", "log")
    
    try:
        # Set the API key
        config.GEMINI_API_KEY = gemini_key
        
        # Create browser
        send("Launching browser...", "info", "log")
        
        from playwright.sync_api import sync_playwright
        pw = sync_playwright()
        pw.start()
        browser_obj, context, page = browser.create_browser(pw)
        
        # Login to LinkedIn
        send("Logging into LinkedIn...", "info", "log")
        login_success = linkedin_login.login(page, email, password)
        
        if not login_success:
            send("Failed to login. Check your credentials.", "error", "error")
            is_running = False
            browser_obj.close()
            pw.stop()
            return
        
        send("Logged in successfully!", "success", "log")
        
        # Process each company
        for company in companies:
            if stop_requested:
                send("Stopped by user.", "warning", "log")
                break
            
            send(f"Searching for posts at {company}...", "info", "log")
            posts = linkedin_search.find_hiring_posts(page, company, 3)
            
            if not posts:
                send(f"No hiring posts found for {company}", "warning", "log")
                continue
            
            send(f"Found {len(posts)} post(s) at {company}", "success", "log")
            
            # Process each post
            for post in posts:
                if stop_requested:
                    send("Stopped by user.", "warning", "log")
                    break
                
                # Check for duplicate
                if logger.already_commented(post["post_id"]):
                    send(f"Already commented on this post, skipping.", "warning", "log")
                    continue
                
                send(f"Found post: {post['text'][:80]}...", "info", "log")
                
                # Generate AI comment
                send("Generating AI comment...", "info", "log")
                comment = ai_writer.generate_comment(
                    post_text=post["text"],
                    company=company,
                    resume=resume,
                    max_chars=config.COMMENT_MAX_CHARS,
                )
                
                if not comment:
                    send("AI could not generate comment, skipping.", "error", "error")
                    continue
                
                # Send comment for approval
                send("Here is the AI comment:", "success", "comment_ready")
                import json
                message_queue.put(json.dumps({
                    "type": "comment_ready",
                    "message": "Here is the AI comment:",
                    "comment": comment,
                    "level": "success"
                }))
                
                # Wait for user approval with 2 minute timeout
                approval_event.clear()
                approval_decision["action"] = "n"
                approval_decision["comment"] = ""
                
                waited = approval_event.wait(timeout=120)
                
                if not waited:
                    send("Approval timeout (2 min), skipping.", "warning", "log")
                    action = "n"
                else:
                    action = approval_decision["action"]
                
                # Process the decision
                if action == "y":
                    # Post the comment
                    send("Posting comment...", "info", "log")
                    success = linkedin_comment.post_comment(page, post["url"], comment)
                    if success:
                        logger.log_comment(post, company, comment)
                        send("Comment posted!", "success", "log")
                    else:
                        send("Failed to post comment.", "error", "error")
                        
                elif action == "e":
                    # Use edited comment
                    edited = approval_decision.get("comment", comment)
                    send("Posting edited comment...", "info", "log")
                    success = linkedin_comment.post_comment(page, post["url"], edited)
                    if success:
                        logger.log_comment(post, company, edited)
                        send("Edited comment posted!", "success", "log")
                    else:
                        send("Failed to post edited comment.", "error", "error")
                        
                else:
                    send("Skipped by user.", "warning", "log")
                
                # Human delay between posts
                browser.human_delay(config.MIN_DELAY_SECONDS, config.MAX_DELAY_SECONDS + 2)
        
        # Close browser
        send("Closing browser...", "info", "log")
        context.close()
        browser_obj.close()
        pw.stop()
        
    except Exception as e:
        send(f"Error: {str(e)}", "error", "error")
        
    finally:
        is_running = False
        send("Session complete!", "success", "done")


# ============================================================
# ENDPOINTS
# ============================================================
@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "LinkedIn Job Hunter Agent API", "version": "2.0.0"}


@app.get("/status")
def get_status():
    """Get agent status."""
    return {
        "running": is_running,
        "message": "Agent is running" if is_running else "Ready"
    }


@app.post("/start")
def start_agent(request: StartRequest):
    """Start the LinkedIn agent."""
    global is_running, stop_requested, agent_thread
    
    # Validate all fields
    if not request.linkedin_email or request.linkedin_email == "your_email@gmail.com":
        raise HTTPException(status_code=400, detail="Missing linkedin_email")
    if not request.linkedin_password or request.linkedin_password == "your_linkedin_password":
        raise HTTPException(status_code=400, detail="Missing linkedin_password")
    if not request.gemini_api_key or request.gemini_api_key == "AIzaYourGeminiKeyHere":
        raise HTTPException(status_code=400, detail="Missing gemini_api_key")
    if not request.companies:
        raise HTTPException(status_code=400, detail="Missing companies")
    if not request.resume:
        raise HTTPException(status_code=400, detail="Missing resume")
    
    # Check if already running
    if is_running:
        raise HTTPException(status_code=400, detail="Agent already running")
    
    # Reset state
    is_running = True
    stop_requested = False
    
    # Clear the message queue
    while not message_queue.empty():
        try:
            message_queue.get_nowait()
        except queue.Empty:
            break
    
    # Start the agent in a background thread
    agent_thread = threading.Thread(
        target=run_agent,
        args=(
            request.linkedin_email,
            request.linkedin_password,
            request.gemini_api_key,
            request.companies,
            request.resume,
        ),
        daemon=True
    )
    agent_thread.start()
    
    return {
        "status": "started",
        "message": "Agent is running. Watch /stream for updates."
    }


@app.get("/stream")
def stream():
    """Server-Sent Events endpoint for live log messages."""
    import json
    
    def event_generator():
        while True:
            try:
                # Try to get message from queue
                try:
                    message = message_queue.get(timeout=2)
                    yield f"data: {message}\n\n"
                except queue.Empty:
                    # Send heartbeat every 2 seconds
                    yield f"data: {json.dumps({'type': 'heartbeat', 'message': 'heartbeat'})}\n\n"
                    
            except GeneratorExit:
                break
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@app.post("/approve")
def approve_comment(request: ApproveRequest):
    """Submit user approval decision."""
    global approval_decision, approval_event
    
    if request.action not in ["y", "n", "e"]:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'y', 'n', or 'e'")
    
    if request.action == "e" and not request.comment:
        raise HTTPException(status_code=400, detail="Edited comment text required")
    
    # Store the decision
    approval_decision["action"] = request.action
    if request.action == "e":
        approval_decision["comment"] = request.comment
    
    # Wake up the waiting agent thread
    approval_event.set()
    
    return {
        "status": "ok",
        "action": request.action
    }


@app.get("/stop")
def stop_agent():
    """Stop the running agent."""
    global is_running, stop_requested
    
    stop_requested = True
    is_running = False
    
    # Add stop message to queue
    send("Stop requested.", "warning", "log")
    
    # Note: Browser closure happens in run_agent's finally block
    
    return {"status": "stopped"}


# ============================================================
# STARTUP
# ============================================================
if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("LinkedIn Job Hunter Agent Backend")
    print("Running at http://localhost:8000")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)