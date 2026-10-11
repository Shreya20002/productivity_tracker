"""
Storage Module
Handles JSON file storage for activity logs.
Implements append-safe writes to prevent data corruption.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
import tempfile
import shutil


# Default data directory and file
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
ACTIVITY_LOG_FILE = os.path.join(DATA_DIR, 'activity_log.json')


def ensure_data_directory():
    """Create data directory if it doesn't exist."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)


def load_activity_log(filepath: str = None) -> List[Dict]:
    """
    Load activity log from JSON file.
    
    Args:
        filepath: Path to the JSON file (default: activity_log.json)
        
    Returns:
        List of activity entries
    """
    if filepath is None:
        filepath = ACTIVITY_LOG_FILE
    
    ensure_data_directory()
    
    if not os.path.exists(filepath):
        return []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return []
            data = json.loads(content)
            if isinstance(data, list):
                return data
            return []
    except (json.JSONDecodeError, IOError, OSError):
        # If file is corrupted, try to recover from backup
        backup_path = filepath + '.backup'
        if os.path.exists(backup_path):
            try:
                with open(backup_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
            except (json.JSONDecodeError, IOError, OSError):
                pass
        return []


def save_activity_log(entries: List[Dict], filepath: str = None) -> bool:
    """
    Save activity log to JSON file using atomic write.
    
    Args:
        entries: List of activity entries to save
        filepath: Path to the JSON file (default: activity_log.json)
        
    Returns:
        bool: True if save was successful
    """
    if filepath is None:
        filepath = ACTIVITY_LOG_FILE
    
    ensure_data_directory()
    
    try:
        # Create backup of existing file
        if os.path.exists(filepath):
            backup_path = filepath + '.backup'
            shutil.copy2(filepath, backup_path)
        
        # Write to temporary file first (atomic write)
        dir_name = os.path.dirname(filepath)
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            dir=dir_name,
            delete=False,
            encoding='utf-8'
        ) as tmp_file:
            json.dump(entries, tmp_file, indent=2, ensure_ascii=False)
            tmp_path = tmp_file.name
        
        # Atomic rename
        shutil.move(tmp_path, filepath)
        return True
        
    except (IOError, OSError) as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return False


def append_activity_entry(entry: Dict, filepath: str = None) -> bool:
    """
    Append a single activity entry to the log file.
    
    Args:
        entry: Activity entry dictionary
        filepath: Path to the JSON file (default: activity_log.json)
        
    Returns:
        bool: True if append was successful
    """
    entries = load_activity_log(filepath)
    entries.append(entry)
    return save_activity_log(entries, filepath)


def create_activity_entry(
    app_name: str,
    start_time: datetime,
    end_time: datetime,
    duration_seconds: int = None
) -> Dict:
    """
    Create a properly formatted activity entry.
    
    Args:
        app_name: Name of the application
        start_time: Session start time
        end_time: Session end time
        duration_seconds: Duration in seconds (calculated if not provided)
        
    Returns:
        Dict: Formatted activity entry
    """
    if duration_seconds is None:
        duration_seconds = int((end_time - start_time).total_seconds())
    
    return {
        "app_name": app_name,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "duration_seconds": duration_seconds,
        "date": start_time.strftime("%Y-%m-%d")
    }


def get_entries_for_date(date: str = None, filepath: str = None) -> List[Dict]:
    """
    Get all activity entries for a specific date.
    
    Args:
        date: Date string in YYYY-MM-DD format (default: today)
        filepath: Path to the JSON file
        
    Returns:
        List of activity entries for the specified date
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    entries = load_activity_log(filepath)
    return [e for e in entries if e.get('date') == date]


def get_entries_for_date_range(
    start_date: str,
    end_date: str,
    filepath: str = None
) -> List[Dict]:
    """
    Get all activity entries within a date range.
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        filepath: Path to the JSON file
        
    Returns:
        List of activity entries within the date range
    """
    entries = load_activity_log(filepath)
    return [
        e for e in entries 
        if start_date <= e.get('date', '') <= end_date
    ]


def get_usage_summary(entries: List[Dict]) -> Dict[str, int]:
    """
    Calculate total usage time per application.
    
    Args:
        entries: List of activity entries
        
    Returns:
        Dict mapping app names to total seconds
    """
    summary = {}
    for entry in entries:
        app_name = entry.get('app_name', 'Unknown')
        duration = entry.get('duration_seconds', 0)
        summary[app_name] = summary.get(app_name, 0) + duration
    return summary


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2h 30m 15s")
    """
    if seconds < 0:
        seconds = 0
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def clear_old_entries(days_to_keep: int = 30, filepath: str = None) -> int:
    """
    Remove entries older than specified days.
    
    Args:
        days_to_keep: Number of days to keep
        filepath: Path to the JSON file
        
    Returns:
        Number of entries removed
    """
    from datetime import timedelta
    
    cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime("%Y-%m-%d")
    entries = load_activity_log(filepath)
    
    original_count = len(entries)
    filtered_entries = [e for e in entries if e.get('date', '') >= cutoff_date]
    
    if len(filtered_entries) < original_count:
        save_activity_log(filtered_entries, filepath)
    
    return original_count - len(filtered_entries)


if __name__ == "__main__":
    # Test storage functions
    print("Testing storage module...")
    
    # Create test entry
    now = datetime.now()
    entry = create_activity_entry(
        app_name="Test App",
        start_time=now,
        end_time=now,
        duration_seconds=60
    )
    print(f"Created entry: {entry}")
    
    # Test append
    success = append_activity_entry(entry)
    print(f"Append successful: {success}")
    
    # Test load
    entries = load_activity_log()
    print(f"Loaded {len(entries)} entries")
    
    # Test summary
    summary = get_usage_summary(entries)
    print(f"Usage summary: {summary}")
