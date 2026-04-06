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
