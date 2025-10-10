from datetime import datetime
from zoneinfo import ZoneInfo

def append_remarks(existing_remarks: str, new_remark: str, username: str) -> str:
    """Append new remark to existing remarks with timestamp and user"""
    timestamp = datetime.now(ZoneInfo('Asia/Kolkata')).strftime('%Y-%m-%d %H:%M')
    new_entry = f"{timestamp} [{username}]: {new_remark}"
    
    if existing_remarks and existing_remarks.strip():
        return f"{existing_remarks}\n{new_entry}"
    return new_entry