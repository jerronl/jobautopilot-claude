"""Shared utilities for jobautopilot-claude agents."""
import os
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
WORKSPACE = Path.home() / ".jobautopilot" / "workspace"

# Playwright MCP server config — reused across all agents
def playwright_mcp(headed: bool = True) -> dict:
    args = ["@playwright/mcp@latest"]
    if not headed:
        args.append("--headless")
    return {"command": "npx", "args": args}


def playwright_mcp_with_profile(headed: bool = True, profile_name: str = "search") -> dict:
    """Playwright MCP with a persistent user-data-dir so login cookies survive across runs."""
    profile_dir = os.environ.get(
        "SEARCH_BROWSER_PROFILE_DIR",
        str(Path.home() / ".jobautopilot" / "browser_profiles" / profile_name),
    )
    Path(profile_dir).mkdir(parents=True, exist_ok=True)
    args = ["@playwright/mcp@latest", "--user-data-dir", profile_dir]
    if not headed:
        args.append("--headless")
    return {"command": "npx", "args": args}


def playwright_mcp_shared(headed: bool = True, profile_name: str = "search") -> dict:
    """Playwright MCP that connects to a long-lived shared Chromium via CDP.

    The first agent that calls this launches a detached Chromium with
    `--remote-debugging-port=N --user-data-dir=<profile>`, writes N to a port file,
    and returns an MCP server config that uses `--cdp-endpoint`. Subsequent agents
    (or reruns) reuse the same browser process. This lets multiple agents share
    the same login profile AND run concurrently — there's no user-data-dir lock
    conflict because only one Chromium process owns the dir.
    """
    import glob, socket, subprocess, time
    from urllib.request import urlopen
    from urllib.error import URLError

    profile_root = Path.home() / ".jobautopilot" / "browser_profiles"
    profile_dir  = Path(os.environ.get("SEARCH_BROWSER_PROFILE_DIR", str(profile_root / profile_name)))
    profile_dir.mkdir(parents=True, exist_ok=True)
    port_file = profile_root / f".{profile_name}.cdp_port"

    def _alive(p: str) -> bool:
        try:
            urlopen(f"http://127.0.0.1:{p}/json/version", timeout=1).read()
            return True
        except (URLError, OSError):
            return False

    def _free_port() -> int:
        with socket.socket() as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def _chromium() -> str:
        for pattern in [
            str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux64/chrome"),
            str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome"),
        ]:
            hits = sorted(glob.glob(pattern), reverse=True)
            if hits:
                return hits[0]
        raise RuntimeError("Playwright Chromium not found — run `npx playwright install chromium`")

    port = port_file.read_text().strip() if port_file.exists() else ""
    if not (port and _alive(port)):
        port = str(_free_port())
        # Quarter-screen window in bottom-right (assume 1920x1080 unless overridden)
        screen_w = int(os.environ.get("SCREEN_WIDTH",  "1920"))
        screen_h = int(os.environ.get("SCREEN_HEIGHT", "1080"))
        win_w = screen_w // 2
        win_h = screen_h // 2
        win_x = screen_w - win_w
        win_y = screen_h - win_h
        cmd = [
            _chromium(),
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--no-sandbox",
            f"--window-size={win_w},{win_h}",
            f"--window-position={win_x},{win_y}",
            "about:blank",
        ]
        if not headed:
            cmd.insert(1, "--headless=new")
        subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(30):
            if _alive(port):
                break
            time.sleep(0.5)
        port_file.write_text(port)

    return {
        "command": "npx",
        "args": ["@playwright/mcp@latest", "--cdp-endpoint", f"http://127.0.0.1:{port}"],
    }


def load_skill_prompt(skill_name: str) -> str:
    """Load SKILL.md, stripping YAML frontmatter."""
    text = (SKILLS_DIR / skill_name / "SKILL.md").read_text()
    parts = text.split("---\n", 2)
    return parts[2].strip() if len(parts) >= 3 else text.strip()


def base_env() -> dict:
    return {
        "RESUME_DIR": os.environ.get(
            "RESUME_DIR",
            str(Path.home() / "Documents" / "jobs") + "/",
        ),
        "JOB_SEARCH_TRACKER": os.environ.get(
            "JOB_SEARCH_TRACKER",
            str(WORKSPACE / "job_application_tracker.md"),
        ),
    }
