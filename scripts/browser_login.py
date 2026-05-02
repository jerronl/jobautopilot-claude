#!/usr/bin/env python3
"""Open URLs in the existing submit browser via CDP, starting it first if needed.

Usage:
    python3 browser_login.py <profile_dir> '["url1", "url2", ...]'

Connects to the browser already managed by submit_runner.py (via CDP) and opens
each URL as a new tab. If the browser is not running, starts it via browser_restart.py
so it always has a CDP port (no profile conflicts with submit_runner.py).
"""
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


def _alive(port: str) -> bool:
    try:
        urlopen(f"http://127.0.0.1:{port}/json/version", timeout=2).read()
        return True
    except (URLError, OSError):
        return False


def _read_port(profile_dir: Path) -> str:
    port_file = profile_dir.parent / f".{profile_dir.name}.cdp_port"
    return port_file.read_text().strip() if port_file.exists() else ""


def _open_tab(port: str, url: str) -> None:
    try:
        req = Request(
            f"http://127.0.0.1:{port}/json/new?{quote(url, safe='')}",
            method="PUT",
        )
        urlopen(req, timeout=3)
    except (URLError, OSError):
        pass


def _ensure_browser(profile_dir: Path) -> str:
    """Return a live CDP port, starting the browser if needed."""
    port = _read_port(profile_dir)
    if port and _alive(port):
        return port

    restart_script = Path(
        os.environ.get("BROWSER_RESTART_SCRIPT", "")
        or Path(__file__).parent / "browser_restart.py"
    )
    subprocess.run(
        [sys.executable, str(restart_script), "--profile", profile_dir.name],
        check=False,
    )
    return _read_port(profile_dir)


def main():
    profile_dir = Path(sys.argv[1])
    urls = json.loads(sys.argv[2])

    port = _ensure_browser(profile_dir)
    if not port:
        print(f"browser_login: could not start browser for {profile_dir}", file=sys.stderr)
        sys.exit(1)

    for url in urls:
        _open_tab(port, url)


if __name__ == "__main__":
    main()
