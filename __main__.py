"""
Screen Time & App Usage Tracker
Entry point for the application.

Run with: python -m productivity_tracker
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from productivity_tracker.menu import run_menu


def main():
    """Main entry point."""
    try:
        run_menu()
    except KeyboardInterrupt:
        print("\n\n  Interrupted. Exiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n  Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
