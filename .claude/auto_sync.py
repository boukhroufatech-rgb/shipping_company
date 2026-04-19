#!/usr/bin/env python3
"""
Auto-Sync Script - Git synchronization automation
Pulls updates before starting and pushes after finishing

Usage:
    python auto_sync.py pull      # Pull updates
    python auto_sync.py push      # Push updates
    python auto_sync.py sync      # Pull and push
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def run_git_command(cmd):
    """Execute git command and return result and message"""
    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def git_pull():
    """Pull updates from GitHub"""
    print("[{}] Pulling updates from GitHub...".format(datetime.now().strftime('%H:%M:%S')))
    success, msg = run_git_command(['git', 'pull', 'origin', 'main'])

    if success:
        if "Already up to date" in msg:
            print("[OK] Repository is up to date")
        else:
            print("[OK] Pull successful\n{}".format(msg))
    else:
        print("[ERROR] Pull failed:\n{}".format(msg))

    return success

def git_push():
    """Push updates to GitHub"""
    print("[{}] Pushing updates to GitHub...".format(datetime.now().strftime('%H:%M:%S')))

    # Check for changes
    success, status = run_git_command(['git', 'status', '--short'])
    if success and not status.strip():
        print("[OK] No changes to push")
        return True

    # Push
    success, msg = run_git_command(['git', 'push', 'origin', 'main'])

    if success:
        print("[OK] Push successful")
        if msg:
            print(msg)
    else:
        print("[ERROR] Push failed:\n{}".format(msg))

    return success

def git_status():
    """Show current git status"""
    success, msg = run_git_command(['git', 'status'])
    return msg if success else "[ERROR] Failed to get status"

def main():
    if len(sys.argv) < 2:
        action = "sync"
    else:
        action = sys.argv[1].lower()

    print("Git Auto-Sync [{}]".format(action.upper()))
    print("=" * 60)

    if action == "pull":
        git_pull()
    elif action == "push":
        git_push()
    elif action == "sync":
        print("\nStep 1: Pulling updates...")
        git_pull()
        print("\nStep 2: Pushing updates...")
        git_push()
    elif action == "status":
        print(git_status())
    else:
        print("[ERROR] Unknown command: {}".format(action))
        print("Available commands: pull | push | sync | status")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("[OK] Sync complete")

if __name__ == "__main__":
    main()
