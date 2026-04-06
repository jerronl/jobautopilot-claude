#!/usr/bin/env python3
"""Open a plain (non-automated) browser for manual login."""
import sys
import json
import time
import signal
import subprocess
from pathlib import Path
import glob


def _find_chromium() -> str:
    # Playwright's Chromium (shared cache)
    for pattern in [
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome"),
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome"),
    ]:
        hits = glob.glob(pattern)
        if hits:
            return sorted(hits)[-1]
    # System fallback
    for name in ("chromium", "chromium-browser", "google-chrome"):
        result = subprocess.run(["which", name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    raise RuntimeError("Chromium not found")


def main():
    profile_dir = sys.argv[1]
    urls        = json.loads(sys.argv[2])

    Path(profile_dir).mkdir(parents=True, exist_ok=True)

    chrome = _find_chromium()
    proc = subprocess.Popen(
        [chrome,
         f"--user-data-dir={profile_dir}",
         "--no-first-run",
         "--no-default-browser-check",
         "--no-sandbox",
         "--disable-dev-shm-usage",
         *urls],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    def _shutdown(signum, frame):
        proc.terminate()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        while proc.poll() is None:
            time.sleep(1)
    except SystemExit:
        proc.terminate()


if __name__ == "__main__":
    main()
