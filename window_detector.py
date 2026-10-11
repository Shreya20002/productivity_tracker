"""
Window Detector Module
Detects the currently active window/application using system tools.
Works on Linux, macOS, and Windows using only Python standard library.
"""

import subprocess
import platform
import re


def get_active_window_linux():
    """Get active window name on Linux using xdotool or xprop."""
    try:
        # Try xdotool first (most reliable)
        result = subprocess.run(
            ['xdotool', 'getactivewindow', 'getwindowname'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Fallback to xprop
        # Get active window ID
        result = subprocess.run(
            ['xprop', '-root', '_NET_ACTIVE_WINDOW'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            match = re.search(r'window id # (0x[0-9a-fA-F]+)', result.stdout)
            if match:
                window_id = match.group(1)
                # Get window name
                result = subprocess.run(
                    ['xprop', '-id', window_id, 'WM_NAME'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    match = re.search(r'WM_NAME\(\w+\) = "(.+)"', result.stdout)
                    if match:
                        return match.group(1)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Another fallback using wmctrl
        result = subprocess.run(
            ['wmctrl', '-a', ':ACTIVE:'],
            capture_output=True,
            text=True,
            timeout=5
        )
        # wmctrl doesn't return window name directly, try xdotool again
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def get_active_window_macos():
    """Get active window name on macOS using AppleScript."""
    try:
        script = '''
        tell application "System Events"
            set frontApp to name of first application process whose frontmost is true
        end tell
        return frontApp
        '''
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def get_active_window_windows():
    """Get active window name on Windows using PowerShell."""
    try:
        # PowerShell command to get active window title
        script = '''
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class User32 {
            [DllImport("user32.dll")]
            public static extern IntPtr GetForegroundWindow();
            [DllImport("user32.dll")]
            public static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);
        }
"@
        $hwnd = [User32]::GetForegroundWindow()
        $title = New-Object System.Text.StringBuilder 256
        [User32]::GetWindowText($hwnd, $title, 256)
        $title.ToString()
        '''
        result = subprocess.run(
            ['powershell', '-Command', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    try:
        # Simpler fallback using tasklist
        result = subprocess.run(
            ['powershell', '-Command', 
             '(Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -First 1).MainWindowTitle'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    return None


def get_active_window():
    """
    Get the currently active window/application name.
    Automatically detects the operating system and uses appropriate method.
    
    Returns:
        str: Name of the active window/application, or None if detection fails.
    """
    system = platform.system().lower()
    
    if system == 'linux':
        return get_active_window_linux()
    elif system == 'darwin':
        return get_active_window_macos()
    elif system == 'windows':
        return get_active_window_windows()
    else:
        return None


def extract_app_name(window_title):
    """
    Extract a clean application name from window title.
    
    Args:
        window_title: Full window title string
        
    Returns:
        str: Cleaned application name
    """
    if not window_title:
        return "Unknown"
    
    # Common patterns to extract app name
    # Pattern: "Document - Application"
    if ' - ' in window_title:
        parts = window_title.split(' - ')
        # Usually the app name is the last part
        return parts[-1].strip()
    
    # Pattern: "Application: Document"
    if ': ' in window_title:
        parts = window_title.split(': ')
        return parts[0].strip()
    
    # Return as-is if no pattern matches
    return window_title.strip()


def is_window_detector_available():
    """
    Check if window detection is available on this system.
    
    Returns:
        tuple: (bool, str) - (is_available, message)
    """
    system = platform.system().lower()
    
    if system == 'linux':
        # Check for xdotool
        try:
            result = subprocess.run(
                ['which', 'xdotool'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, "xdotool is available"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Check for xprop
        try:
            result = subprocess.run(
                ['which', 'xprop'],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                return True, "xprop is available"
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return False, "Install xdotool: sudo apt install xdotool"
    
    elif system == 'darwin':
        # osascript is always available on macOS
        return True, "AppleScript is available"
    
    elif system == 'windows':
        # PowerShell is always available on modern Windows
        return True, "PowerShell is available"
    
    return False, f"Unsupported operating system: {system}"


if __name__ == "__main__":
    # Test the window detector
    available, message = is_window_detector_available()
    print(f"Window detector available: {available}")
    print(f"Message: {message}")
    
    if available:
        window = get_active_window()
        print(f"Active window: {window}")
        if window:
            app_name = extract_app_name(window)
            print(f"App name: {app_name}")
