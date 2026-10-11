"""
Menu Module
Terminal menu interface for the Screen Time Tracker.
Provides user interaction through a simple text-based menu.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from typing import Optional

from .tracker import get_tracker, ActivityTracker
from .storage import (
    get_entries_for_date,
    get_entries_for_date_range,
    get_usage_summary,
    format_duration,
    load_activity_log,
    clear_old_entries
)
from .window_detector import is_window_detector_available


def clear_screen():
    """Clear the terminal screen."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header():
    """Print the application header."""
    print("=" * 60)
    print("       SCREEN TIME & APP USAGE TRACKER")
    print("       File-Based Offline Tracker")
    print("=" * 60)
    print()


def print_menu():
    """Print the main menu options."""
    print("\n" + "-" * 40)
    print("  MAIN MENU")
    print("-" * 40)
    print("  [1] Start tracking")
    print("  [2] Stop tracking")
    print("  [3] View today's usage")
    print("  [4] View weekly summary")
    print("  [5] View all-time statistics")
    print("  [6] Clear old data")
    print("  [7] Check system compatibility")
    print("  [0] Exit")
    print("-" * 40)


def print_status(tracker: ActivityTracker):
    """Print current tracker status."""
    status = tracker.get_status()
    
    print("\n" + "=" * 40)
    print("  TRACKER STATUS")
    print("=" * 40)
    
    if status['is_tracking']:
        if status['is_paused']:
            print("  Status: PAUSED")
        elif status['is_idle']:
            print("  Status: IDLE (no activity detected)")
        else:
            print("  Status: TRACKING")
        
        if status['current_app']:
            print(f"  Current App: {status['current_app']}")
            print(f"  Session Duration: {format_duration(status['current_session_duration'])}")
        
        print(f"  Sessions Recorded: {status['sessions_recorded']}")
        print(f"  Total Tracked: {format_duration(status['total_tracked_time'])}")
    else:
        print("  Status: NOT TRACKING")
    
    print("=" * 40)


def view_today_usage():
    """Display today's usage statistics."""
    clear_screen()
    print_header()
    
    today = datetime.now().strftime("%Y-%m-%d")
    entries = get_entries_for_date(today)
    
    print(f"\n  TODAY'S USAGE ({today})")
    print("=" * 50)
    
    if not entries:
        print("\n  No activity recorded today.")
        print("  Start tracking to begin recording your usage.")
    else:
        summary = get_usage_summary(entries)
        total_time = sum(summary.values())
        
        print(f"\n  Total Screen Time: {format_duration(total_time)}")
        print(f"  Applications Used: {len(summary)}")
        print(f"  Sessions: {len(entries)}")
        print()
        
        # Sort by usage time (descending)
        sorted_apps = sorted(summary.items(), key=lambda x: x[1], reverse=True)
        
        print("  " + "-" * 46)
        print(f"  {'Application':<30} {'Time':>14}")
        print("  " + "-" * 46)
        
        for app_name, seconds in sorted_apps:
            # Truncate long app names
            display_name = app_name[:28] + ".." if len(app_name) > 30 else app_name
            percentage = (seconds / total_time * 100) if total_time > 0 else 0
            time_str = format_duration(seconds)
            print(f"  {display_name:<30} {time_str:>10} ({percentage:>4.1f}%)")
        
        print("  " + "-" * 46)
        
        # Show timeline
        print("\n  ACTIVITY TIMELINE")
        print("  " + "-" * 46)
        
        for entry in entries[-10:]:  # Show last 10 entries
            start = entry.get('start_time', '')[:19].replace('T', ' ')
            app = entry.get('app_name', 'Unknown')[:25]
            duration = format_duration(entry.get('duration_seconds', 0))
            print(f"  {start}  {app:<25} {duration}")
        
        if len(entries) > 10:
            print(f"  ... and {len(entries) - 10} more sessions")
    
    print()
    input("  Press Enter to continue...")


def view_weekly_summary():
    """Display weekly usage summary."""
    clear_screen()
    print_header()
    
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    start_date = week_ago.strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    
    entries = get_entries_for_date_range(start_date, end_date)
    
    print(f"\n  WEEKLY SUMMARY ({start_date} to {end_date})")
    print("=" * 50)
    
    if not entries:
        print("\n  No activity recorded this week.")
    else:
        summary = get_usage_summary(entries)
        total_time = sum(summary.values())
        
        print(f"\n  Total Screen Time: {format_duration(total_time)}")
        print(f"  Daily Average: {format_duration(total_time // 7)}")
        print(f"  Applications Used: {len(summary)}")
        print(f"  Total Sessions: {len(entries)}")
        print()
        
        # Daily breakdown
        print("  DAILY BREAKDOWN")
        print("  " + "-" * 46)
        
        for i in range(7):
            day = (week_ago + timedelta(days=i+1))
            day_str = day.strftime("%Y-%m-%d")
            day_name = day.strftime("%a")
            
            day_entries = [e for e in entries if e.get('date') == day_str]
            day_time = sum(e.get('duration_seconds', 0) for e in day_entries)
            
            bar_length = min(int(day_time / 3600 * 2), 20)  # 2 chars per hour, max 20
            bar = "█" * bar_length
            
            print(f"  {day_name} {day_str}  {format_duration(day_time):>10}  {bar}")
        
        print("  " + "-" * 46)
        
        # Top apps
        print("\n  TOP APPLICATIONS")
        print("  " + "-" * 46)
        
        sorted_apps = sorted(summary.items(), key=lambda x: x[1], reverse=True)[:5]
        
        for i, (app_name, seconds) in enumerate(sorted_apps, 1):
            display_name = app_name[:28] + ".." if len(app_name) > 30 else app_name
            time_str = format_duration(seconds)
            print(f"  {i}. {display_name:<30} {time_str}")
    
    print()
    input("  Press Enter to continue...")


def view_all_time_stats():
    """Display all-time statistics."""
    clear_screen()
    print_header()
    
    entries = load_activity_log()
    
    print("\n  ALL-TIME STATISTICS")
    print("=" * 50)
    
    if not entries:
        print("\n  No activity recorded yet.")
    else:
        summary = get_usage_summary(entries)
        total_time = sum(summary.values())
        
        # Get date range
        dates = sorted(set(e.get('date', '') for e in entries if e.get('date')))
        first_date = dates[0] if dates else "N/A"
        last_date = dates[-1] if dates else "N/A"
        num_days = len(dates)
        
        print(f"\n  Tracking Since: {first_date}")
        print(f"  Last Activity: {last_date}")
        print(f"  Days with Activity: {num_days}")
        print(f"\n  Total Screen Time: {format_duration(total_time)}")
        print(f"  Daily Average: {format_duration(total_time // max(num_days, 1))}")
        print(f"  Total Sessions: {len(entries)}")
        print(f"  Unique Applications: {len(summary)}")
        print()
        
        # Top 10 apps
        print("  TOP 10 APPLICATIONS (ALL TIME)")
        print("  " + "-" * 46)
        
        sorted_apps = sorted(summary.items(), key=lambda x: x[1], reverse=True)[:10]
        
        for i, (app_name, seconds) in enumerate(sorted_apps, 1):
            display_name = app_name[:26] + ".." if len(app_name) > 28 else app_name
            time_str = format_duration(seconds)
            percentage = (seconds / total_time * 100) if total_time > 0 else 0
            print(f"  {i:>2}. {display_name:<28} {time_str:>10} ({percentage:>4.1f}%)")
        
        print("  " + "-" * 46)
    
    print()
    input("  Press Enter to continue...")


def clear_old_data():
    """Clear old activity data."""
    clear_screen()
    print_header()
    
    print("\n  CLEAR OLD DATA")
    print("=" * 50)
    print("\n  This will remove activity entries older than")
    print("  the specified number of days.")
    print()
    
    try:
        days = input("  Enter days to keep (default 30): ").strip()
        days = int(days) if days else 30
        
        if days < 1:
            print("\n  Invalid number. Operation cancelled.")
        else:
            confirm = input(f"\n  Delete entries older than {days} days? (y/n): ").strip().lower()
            
            if confirm == 'y':
                removed = clear_old_entries(days)
                print(f"\n  Removed {removed} old entries.")
            else:
                print("\n  Operation cancelled.")
    except ValueError:
        print("\n  Invalid input. Operation cancelled.")
    
    print()
    input("  Press Enter to continue...")


def check_compatibility():
    """Check system compatibility for window detection."""
    clear_screen()
    print_header()
    
    print("\n  SYSTEM COMPATIBILITY CHECK")
    print("=" * 50)
    
    import platform
    print(f"\n  Operating System: {platform.system()} {platform.release()}")
    print(f"  Python Version: {platform.python_version()}")
    print()
    
    available, message = is_window_detector_available()
    
    if available:
        print("  ✓ Window detection is AVAILABLE")
        print(f"    {message}")
        
        # Test detection
        print("\n  Testing window detection...")
        from .window_detector import get_active_window
        window = get_active_window()
        
        if window:
            print(f"  ✓ Successfully detected: {window[:50]}...")
        else:
            print("  ⚠ Could not detect current window")
            print("    This might be normal if running in certain environments")
    else:
        print("  ✗ Window detection is NOT AVAILABLE")
        print(f"    {message}")
        print("\n  To enable window detection:")
        
        if platform.system().lower() == 'linux':
            print("    sudo apt install xdotool")
            print("    or")
            print("    sudo apt install x11-utils  (for xprop)")
    
    print()
    input("  Press Enter to continue...")


def start_tracking_interactive(tracker: ActivityTracker):
    """Start tracking with interactive feedback."""
    clear_screen()
    print_header()
    
    if tracker.is_tracking:
        print("\n  Tracking is already running!")
        input("  Press Enter to continue...")
        return
    
    # Check compatibility first
    available, message = is_window_detector_available()
    if not available:
        print(f"\n  ⚠ Warning: {message}")
        print("  Tracking may not work correctly.")
        confirm = input("  Continue anyway? (y/n): ").strip().lower()
        if confirm != 'y':
            return
    
    print("\n  Starting activity tracker...")
    
    # Set up callbacks for feedback
    def on_app_change(app):
        pass  # Silent in background
    
    def on_session_saved(entry):
        pass  # Silent in background
    
    tracker.on_app_change = on_app_change
    tracker.on_session_saved = on_session_saved
    
    success = tracker.start_tracking()
    
    if success:
        print("  ✓ Tracking started successfully!")
        print("\n  The tracker is now running in the background.")
        print("  Your application usage is being recorded.")
        print("\n  Return to the menu to view statistics or stop tracking.")
    else:
        print("  ✗ Failed to start tracking.")
    
    print()
    input("  Press Enter to continue...")


def stop_tracking_interactive(tracker: ActivityTracker):
    """Stop tracking with confirmation."""
    clear_screen()
    print_header()
    
    if not tracker.is_tracking:
        print("\n  Tracking is not running.")
        input("  Press Enter to continue...")
        return
    
    status = tracker.get_status()
    print(f"\n  Current session: {status['current_app'] or 'None'}")
    print(f"  Sessions recorded: {status['sessions_recorded']}")
    print(f"  Total tracked time: {format_duration(status['total_tracked_time'])}")
    
    confirm = input("\n  Stop tracking? (y/n): ").strip().lower()
    
    if confirm == 'y':
        print("\n  Stopping tracker...")
        tracker.stop_tracking()
        print("  ✓ Tracking stopped. Session data has been saved.")
    else:
        print("  Tracking continues...")
    
    print()
    input("  Press Enter to continue...")


def run_menu():
    """Run the main menu loop."""
    tracker = get_tracker()
    
    while True:
        clear_screen()
        print_header()
        print_status(tracker)
        print_menu()
        
        choice = input("\n  Enter your choice: ").strip()
        
        if choice == '1':
            start_tracking_interactive(tracker)
        elif choice == '2':
            stop_tracking_interactive(tracker)
        elif choice == '3':
            view_today_usage()
        elif choice == '4':
            view_weekly_summary()
        elif choice == '5':
            view_all_time_stats()
        elif choice == '6':
            clear_old_data()
        elif choice == '7':
            check_compatibility()
        elif choice == '0':
            if tracker.is_tracking:
                print("\n  Stopping tracker before exit...")
                tracker.stop_tracking()
            print("\n  Goodbye!")
            break
        else:
            print("\n  Invalid choice. Please try again.")
            time.sleep(1)


if __name__ == "__main__":
    run_menu()
