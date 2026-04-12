"""Manages log.json to track posted comments and prevent duplicates."""
import json
import os
from datetime import datetime

LOG_FILE = "log.json"


def _load():
    if not os.path.exists(LOG_FILE):
        return {"total_posted": 0, "commented_post_ids": [], "entries": []}
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"total_posted": 0, "commented_post_ids": [], "entries": []}


def _save(data):
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)


def already_commented(post_id):
    data = _load()
    return post_id in data.get("commented_post_ids", [])


def log_comment(post, company, comment):
    data = _load()
    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "company": company,
        "post_id": post.get("post_id", ""),
        "post_url": post.get("url", ""),
        "post_snippet": post.get("text", "")[:150],
        "comment": comment,
    }
    data.setdefault("commented_post_ids", []).append(post.get("post_id", ""))
    data.setdefault("entries", []).append(entry)
    data["total_posted"] = data.get("total_posted", 0) + 1
    _save(data)


def get_total_count():
    return _load().get("total_posted", 0)