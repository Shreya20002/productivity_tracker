"""
Tracker Module
Core tracking logic for monitoring application usage.
Handles session management, idle detection, and activity recording.
"""

import time
import threading
import signal
import sys
from datetime import datetime
from typing import Optional, Callable

from .window_detector import get_active_window, extract_app_name
from .storage import (
    create_activity_entry,
    append_activity_entry,
    load_activity_log,
    save_activity_log
)


class ActivityTracker:
    """
    Main activity tracker class.
    Monitors active windows and records usage sessions.
    """
    
    # Configuration
    POLL_INTERVAL = 2  # seconds between window checks
    IDLE_THRESHOLD = 300  # 5 minutes of no change = idle
    MIN_SESSION_DURATION = 3  # minimum seconds to record a session
    
    def __init__(self):
        self.is_tracking = False
        self.is_paused = False
        self._tracking_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Current session data
        self.current_app: Optional[str] = None
        self.session_start: Optional[datetime] = None
        self.last_activity_time: Optional[datetime] = None
        
        # Idle tracking
        self.idle_start: Optional[datetime] = None
        self.is_idle = False
        
        # Callbacks
        self.on_app_change: Optional[Callable] = None
        self.on_idle_start: Optional[Callable] = None
        self.on_idle_end: Optional[Callable] = None
        self.on_session_saved: Optional[Callable] = None
        
        # Statistics
        self.sessions_recorded = 0
        self.total_tracked_time = 0
        
        # Setup signal handlers for graceful shutdown
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup handlers for graceful shutdown on signals."""
        def signal_handler(signum, frame):
            self.stop_tracking()
            sys.exit(0)
        
        try:
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
        except (ValueError, OSError):
            # Signal handling may not work in all contexts
            pass
    
    def start_tracking(self) -> bool:
        """
        Start tracking application usage.
        
        Returns:
            bool: True if tracking started successfully
        """
        if self.is_tracking:
            return False
        
        self.is_tracking = True
        self.is_paused = False
        self._stop_event.clear()
        
        # Initialize session
        self.current_app = None
        self.session_start = None
        self.last_activity_time = datetime.now()
        self.is_idle = False
        self.idle_start = None
        
        # Start tracking thread
        self._tracking_thread = threading.Thread(
            target=self._tracking_loop,
            daemon=True
        )
        self._tracking_thread.start()
        
        return True
    
    def stop_tracking(self) -> bool:
        """
        Stop tracking and save current session.
        
        Returns:
            bool: True if tracking stopped successfully
        """
        if not self.is_tracking:
            return False
        
        # Signal thread to stop
        self._stop_event.set()
        
        # Save current session before stopping
        self._save_current_session()
        
        # Wait for thread to finish
        if self._tracking_thread and self._tracking_thread.is_alive():
            self._tracking_thread.join(timeout=5)
        
        self.is_tracking = False
        self.is_paused = False
        self.current_app = None
        self.session_start = None
        
        return True
    
    def pause_tracking(self):
        """Pause tracking without saving session."""
        if self.is_tracking and not self.is_paused:
            self.is_paused = True
            self._save_current_session()
    
    def resume_tracking(self):
        """Resume tracking after pause."""
        if self.is_tracking and self.is_paused:
            self.is_paused = False
            self.current_app = None
            self.session_start = None
            self.last_activity_time = datetime.now()
    
    def _tracking_loop(self):
        """Main tracking loop running in separate thread."""
        while not self._stop_event.is_set():
            if not self.is_paused:
                self._check_activity()
            
            # Wait for next poll interval or stop event
            self._stop_event.wait(timeout=self.POLL_INTERVAL)
    
    def _check_activity(self):
        """Check current active window and handle changes."""
        now = datetime.now()
        
        # Get current active window
        window_title = get_active_window()
        
        if window_title is None:
            # Could not detect window - might be idle or error
            self._handle_no_window(now)
            return
        
        app_name = extract_app_name(window_title)
        
        # Check for idle (same window for too long might indicate idle)
        if self.current_app == app_name:
            time_since_last = (now - self.last_activity_time).total_seconds()
            if time_since_last >= self.IDLE_THRESHOLD and not self.is_idle:
                self._enter_idle_state(now)
        else:
            # Activity detected - window changed
            if self.is_idle:
                self._exit_idle_state(now)
            
            self._handle_app_change(app_name, now)
        
        self.last_activity_time = now
    
    def _handle_no_window(self, now: datetime):
        """Handle case when no window is detected."""
        if not self.is_idle:
            time_since_last = (now - self.last_activity_time).total_seconds() if self.last_activity_time else 0
            if time_since_last >= self.IDLE_THRESHOLD:
                self._enter_idle_state(now)
    
    def _handle_app_change(self, new_app: str, now: datetime):
        """Handle application change."""
        # Save previous session
        if self.current_app and self.session_start:
            self._save_current_session()
        
        # Start new session
        self.current_app = new_app
        self.session_start = now
        
        # Callback
        if self.on_app_change:
            self.on_app_change(new_app)
    
    def _enter_idle_state(self, now: datetime):
        """Enter idle state."""
        self.is_idle = True
        self.idle_start = now
        
        # Save current session before going idle
        self._save_current_session()
        
        # Callback
        if self.on_idle_start:
            self.on_idle_start()
    
    def _exit_idle_state(self, now: datetime):
        """Exit idle state."""
        self.is_idle = False
        self.idle_start = None
        
        # Callback
        if self.on_idle_end:
            self.on_idle_end()
    
    def _save_current_session(self):
        """Save the current session to storage."""
        if not self.current_app or not self.session_start:
            return
        
        now = datetime.now()
        duration = int((now - self.session_start).total_seconds())
        
        # Only save if session is long enough
        if duration < self.MIN_SESSION_DURATION:
            return
        
        # Create and save entry
        entry = create_activity_entry(
            app_name=self.current_app,
            start_time=self.session_start,
            end_time=now,
            duration_seconds=duration
        )
        
        success = append_activity_entry(entry)
        
        if success:
            self.sessions_recorded += 1
            self.total_tracked_time += duration
            
            # Callback
            if self.on_session_saved:
                self.on_session_saved(entry)
        
        # Reset session
        self.current_app = None
        self.session_start = None
    
    def get_status(self) -> dict:
        """
        Get current tracker status.
        
        Returns:
            dict: Status information
        """
        status = {
            'is_tracking': self.is_tracking,
            'is_paused': self.is_paused,
            'is_idle': self.is_idle,
            'current_app': self.current_app,
            'sessions_recorded': self.sessions_recorded,
            'total_tracked_time': self.total_tracked_time
        }
        
        if self.session_start:
            current_duration = int((datetime.now() - self.session_start).total_seconds())
            status['current_session_duration'] = current_duration
        else:
            status['current_session_duration'] = 0
        
        return status


# Global tracker instance
_tracker_instance: Optional[ActivityTracker] = None


def get_tracker() -> ActivityTracker:
    """Get or create the global tracker instance."""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = ActivityTracker()
    return _tracker_instance


if __name__ == "__main__":
    # Test the tracker
    print("Testing Activity Tracker...")
    
    tracker = get_tracker()
    
    def on_change(app):
        print(f"App changed to: {app}")
    
    def on_idle():
        print("Entered idle state")
    
    def on_active():
        print("Exited idle state")
    
    def on_saved(entry):
        print(f"Session saved: {entry['app_name']} - {entry['duration_seconds']}s")
    
    tracker.on_app_change = on_change
    tracker.on_idle_start = on_idle
    tracker.on_idle_end = on_active
    tracker.on_session_saved = on_saved
    
    print("Starting tracker... Press Ctrl+C to stop")
    tracker.start_tracking()
    
    try:
        while tracker.is_tracking:
            time.sleep(1)
            status = tracker.get_status()
            if status['current_app']:
                print(f"\rTracking: {status['current_app']} ({status['current_session_duration']}s)", end='', flush=True)
    except KeyboardInterrupt:
        print("\nStopping tracker...")
        tracker.stop_tracking()
        print("Tracker stopped.")
