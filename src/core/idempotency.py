import os
import json
from datetime import datetime

HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "run_history.json"
)

def _init_history():
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    if not os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "w") as f:
            json.dump({"runs": []}, f, indent=2)

def is_week_processed(iso_week: str) -> bool:
    """
    Checks if a given ISO week (format: YYYY-Wxx) has already been processed and saved.
    """
    _init_history()
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        runs = history.get("runs", [])
        for run in runs:
            if run.get("iso_week") == iso_week:
                return True
    except Exception as e:
        print(f"Error reading history log: {e}")
    return False

def record_run(iso_week: str, doc_id: str, section_id: str = None, email_status: str = "DRAFT"):
    """
    Records a successful run to avoid duplicates.
    """
    _init_history()
    try:
        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
            
        history["runs"].append({
            "iso_week": iso_week,
            "doc_id": doc_id,
            "section_id": section_id,
            "email_status": email_status,
            "timestamp": datetime.now().isoformat()
        })
        
        with open(HISTORY_FILE, "w") as f:
            json.dump(history, f, indent=2)
    except Exception as e:
        print(f"Error writing to history log: {e}")
