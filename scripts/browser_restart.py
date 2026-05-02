#!/usr/bin/env python3
"""Restart the shared CDP Chromium if it is not responding.

Usage:
    python3 browser_restart.py [--profile search]

Exits 0 if browser is alive (or was successfully restarted).
Exits 1 if Chromium could not be started.
"""
import argparse
import glob
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen


PROFILE_ROOT = Path.home() / ".jobautopilot" / "browser_profiles"


def _find_chromium() -> str:
    for pattern in [
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome"),
        str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome"),
    ]:
        hits = sorted(glob.glob(pattern), reverse=True)
        if hits:
            return hits[0]
    for name in ("chromium", "chromium-browser", "google-chrome"):
        result = subprocess.run(["which", name], capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout.strip()
    raise RuntimeError("Chromium not found — run `npx playwright install chromium`")


def _alive(port: str) -> bool:
    try:
        urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2).read()
        return True
    except (URLError, OSError):
        return False


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def restart(profile: str) -> bool:
    profile_dir = PROFILE_ROOT / profile
    profile_dir.mkdir(parents=True, exist_ok=True)
    port_file = PROFILE_ROOT / f".{profile}.cdp_port"

    port = port_file.read_text().strip() if port_file.exists() else ""
    if port and _alive(port):
        print(f"✓ Browser already alive on port {port}")
        return True

    print(f"⚠️  Browser not responding on port {port or '(none)'} — restarting Chromium...")

    chrome = _find_chromium()
    port = str(_free_port())

    screen_w = int(os.environ.get("SCREEN_WIDTH", "1920"))
    screen_h = int(os.environ.get("SCREEN_HEIGHT", "1080"))
    win_w, win_h = screen_w // 2, screen_h // 2
    win_x, win_y = screen_w - win_w, screen_h - win_h

    subprocess.Popen(
        [
            chrome,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            f"--window-size={win_w},{win_h}",
            f"--window-position={win_x},{win_y}",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    for _ in range(20):
        if _alive(port):
            port_file.write_text(port)
            print(f"✓ Chromium started on port {port}")
            return True
        time.sleep(0.5)

    print(f"✗ Chromium did not respond after 10s on port {port}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="search")
    args = parser.parse_args()
    sys.exit(0 if restart(args.profile) else 1)


if __name__ == "__main__":
    main()
