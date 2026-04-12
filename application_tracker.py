"""Application Tracker - Track job applications and their status."""
import json
from datetime import datetime
from pathlib import Path
import config
import terminal_ui


def load_applications():
    """Load all applications."""
    if not config.APPLICATIONS_FILE.exists():
        return {"applications": [], "stats": {"total": 0, "applied": 0, "interview": 0, "rejected": 0, "offer": 0}}
    
    try:
        with open(config.APPLICATIONS_FILE, "r") as f:
            return json.load(f)
    except:
        return {"applications": [], "stats": {"total": 0, "applied": 0, "interview": 0, "rejected": 0, "offer": 0}}


def save_applications(data):
    """Save applications."""
    config.DATA_DIR.mkdir(exist_ok=True)
    with open(config.APPLICATIONS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_application(company, position, post_url, post_text, comment, status="applied"):
    """Add a new application."""
    data = load_applications()
    
    application = {
        "id": len(data["applications"]) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "company": company,
        "position": position,
        "post_url": post_url,
        "post_snippet": post_text[:150],
        "comment": comment,
        "status": status,
    }
    
    data["applications"].append(application)
    data["stats"]["total"] += 1
    data["stats"]["applied"] += 1
    
    save_applications(data)
    return application["id"]


def update_status(application_id, new_status):
    """Update application status."""
    data = load_applications()
    
    for app in data["applications"]:
        if app["id"] == application_id:
            old_status = app["status"]
            if old_status in data["stats"]:
                data["stats"][old_status] -= 1
            
            app["status"] = new_status
            if new_status in data["stats"]:
                data["stats"][new_status] += 1
            
            save_applications(data)
            terminal_ui.print_success(f"Updated application #{application_id} to {new_status}")
            return True
    
    return False


def get_applications_by_company(company):
    """Get all applications for a company."""
    data = load_applications()
    return [app for app in data["applications"] if app["company"].lower() == company.lower()]


def get_applications_by_status(status):
    """Get applications by status."""
    data = load_applications()
    return [app for app in data["applications"] if app["status"] == status]


def get_stats():
    """Get application statistics."""
    data = load_applications()
    return data.get("stats", {})


def list_applications(filter_status=None, limit=10):
    """List recent applications."""
    data = load_applications()
    apps = data.get("applications", [])
    
    if filter_status:
        apps = [a for a in apps if a["status"] == filter_status]
    
    apps = sorted(apps, key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    if not apps:
        terminal_ui.print_warning("No applications found.")
        return []
    
    print()
    terminal_ui.print_info(f"Showing {len(apps)} recent applications:")
    print()
    
    for app in apps:
        status_emoji = {
            "applied": "○",
            "interview": "◐",
            "rejected": "✗",
            "offer": "✓"
        }.get(app["status"], "○")
        
        print(f"{status_emoji} #{app['id']} | {app['company']} | {app['position'][:30]}")
        print(f"   Status: {app['status']} | Date: {app['timestamp'][:10]}")
        print()
    
    return apps


def export_csv(filepath):
    """Export applications to CSV."""
    data = load_applications()
    apps = data.get("applications", [])
    
    if not apps:
        terminal_ui.print_warning("No applications to export.")
        return False
    
    import csv
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Company", "Position", "Status", "Date", "Post URL"])
        
        for app in apps:
            writer.writerow([
                app["id"],
                app["company"],
                app["position"],
                app["status"],
                app["timestamp"],
                app["post_url"]
            ])
    
    terminal_ui.print_success(f"Exported to {filepath}")
    return True


def get_summary():
    """Get application summary for terminal display."""
    data = load_applications()
    stats = data.get("stats", {})
    
    summary = {
        "total": stats.get("total", 0),
        "applied": stats.get("applied", 0),
        "interview": stats.get("interview", 0),
        "rejected": stats.get("rejected", 0),
        "offer": stats.get("offer", 0),
    }
    
    return summary


def main():
    """CLI for application tracker."""
    import sys
    
    if len(sys.argv) < 2:
        list_applications()
        return
    
    cmd = sys.argv[1]
    
    if cmd == "--list":
        status_filter = sys.argv[2] if len(sys.argv) > 2 else None
        list_applications(status_filter)
    elif cmd == "--stats":
        stats = get_stats()
        print(f"Total: {stats.get('total', 0)}")
        print(f"Applied: {stats.get('applied', 0)}")
        print(f"Interview: {stats.get('interview', 0)}")
        print(f"Rejected: {stats.get('rejected', 0)}")
        print(f"Offer: {stats.get('offer', 0)}")
    elif cmd == "--update":
        if len(sys.argv) < 4:
            print("Usage: python application_tracker.py --update <id> <status>")
            return
        try:
            app_id = int(sys.argv[2])
            new_status = sys.argv[3]
            update_status(app_id, new_status)
        except ValueError:
            print("Invalid application ID")
    elif cmd == "--export":
        export_csv("applications.csv")
    else:
        print("Usage: python application_tracker.py [--list|--stats|--update <id> <status>|--export]")


if __name__ == "__main__":
    main()