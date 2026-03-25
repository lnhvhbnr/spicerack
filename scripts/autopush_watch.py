#!/usr/bin/env python3
import os
import subprocess
import sys
import time
from pathlib import Path


REPO_DIR = Path(__file__).resolve().parents[1]
WATCH_FILE = REPO_DIR / "spicerack_app.html"
POLL_SECONDS = 2
DEBOUNCE_SECONDS = 4
COMMIT_MESSAGE = "Auto-sync spicerack_app.html"


def run_git(*args):
    return subprocess.run(
        ["git", *args],
        cwd=REPO_DIR,
        text=True,
        capture_output=True,
    )


def file_signature(path):
    stat = path.stat()
    return (stat.st_mtime_ns, stat.st_size)


def tracked_file_changed():
    result = run_git("status", "--porcelain", "--", str(WATCH_FILE.name))
    return bool(result.stdout.strip())


def sync_file():
    add_result = run_git("add", WATCH_FILE.name)
    if add_result.returncode != 0:
        print(add_result.stderr.strip(), flush=True)
        return False

    commit_result = run_git("commit", "-m", COMMIT_MESSAGE)
    if commit_result.returncode != 0:
        stderr = commit_result.stderr.strip()
        stdout = commit_result.stdout.strip()
        combined = "\n".join(part for part in [stdout, stderr] if part)
        if "nothing to commit" in combined.lower():
            return True
        print(combined, flush=True)
        return False

    print(commit_result.stdout.strip(), flush=True)
    push_result = run_git("push")
    if push_result.returncode != 0:
        combined = "\n".join(
            part for part in [push_result.stdout.strip(), push_result.stderr.strip()] if part
        )
        print(combined, flush=True)
        return False

    print(push_result.stdout.strip(), flush=True)
    return True


def main():
    if not WATCH_FILE.exists():
        print(f"Watch file not found: {WATCH_FILE}", flush=True)
        return 1

    print(f"Watching {WATCH_FILE}", flush=True)
    last_seen = file_signature(WATCH_FILE)
    pending_since = None

    while True:
        try:
            current = file_signature(WATCH_FILE)
        except FileNotFoundError:
            time.sleep(POLL_SECONDS)
            continue

        if current != last_seen:
            last_seen = current
            pending_since = time.time()
            print("Detected change in spicerack_app.html", flush=True)

        if pending_since and (time.time() - pending_since) >= DEBOUNCE_SECONDS:
            pending_since = None
            if tracked_file_changed():
                print("Syncing latest change to GitHub...", flush=True)
                sync_file()

        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    sys.exit(main())
