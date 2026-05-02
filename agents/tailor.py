"""Tailor subagent definition."""
from claude_agent_sdk import AgentDefinition
from .base import load_skill_prompt, playwright_mcp_shared, SKILLS_DIR

MD_TO_DOCX = SKILLS_DIR / "tailor" / "scripts" / "md_to_docx.py"
TEMPLATE = SKILLS_DIR / "tailor" / "scripts" / "sample_placeholders.docx"

HEADER = f"""\
You are a resume tailoring agent. Your ONLY output is .md files.

## ⚠️ STEP ZERO — read the real job description in the browser FIRST

Before you write a single line of resume or cover letter, for EACH job:

1. `mcp__playwright__browser_navigate(url)` — open the tracker URL
2. `mcp__playwright__browser_snapshot()` — read the actual posting: title, team, required skills, tech stack, seniority, location, responsibilities
3. Only AFTER you have the real page content, start tailoring

Do NOT tailor from the tracker's one-line summary alone — it's lossy. The searcher wrote
a short reason, but the posting itself has the keywords, the required years, the tech
stack, and the team context you need to produce a believable resume. If the page fails
to load or is behind login, stop on that job, write `tailor_blocked` with the reason,
and move on to the next — do NOT fabricate details from the summary.

## Your job
Write tailored resume and cover letter as .md files.
That is all. Do not create .docx files. Do not run any conversion scripts.
The orchestrator will handle .docx conversion after you finish.

## Resume .md format  (NOT standard Markdown — no #, ##, **, ---, tables)

Line 1: Full Name
Line 2: email | phone | linkedin_url | City, ST   ← no zip codes, no street address
(blank line)
SUMMARY
Summary text here.
(blank line)
CORE SKILLS
Skill1, Skill2 | Domain1 | Domain2
(blank line)
EXPERIENCE   ← REVERSE CHRONOLOGICAL — most recent job FIRST
Most Recent Title — Company Name | City, ST | Jan 2022 – Present
• Bullet one
• Bullet two
(blank line)
Previous Title — Company Name | City, ST | Jun 2019 – Dec 2021
• Bullet
(blank line)
EARLIER EXPERIENCE   ← ONE LINE PER ENTRY ONLY — no bullets, no descriptions, no second line
Role — Company, Year–Year
Another Role — Company, Year–Year
⛔ NEVER add "- did X" or any bullet under EARLIER EXPERIENCE. One line = the whole entry.
(blank line)
EDUCATION
University — Degree (Year)

Rules: section headers ALL CAPS, no ## prefix. Job header uses em dash (—) and pipes.
Bullets start with • or -. No bold, no horizontal rules, no Markdown headings.
EARLIER EXPERIENCE must be plain one-liners only — never add bullets or descriptions there.

## Cover letter .md format
Plain paragraphs, no special formatting needed.

## Browser access
  browser_navigate(url)    — open the job posting URL
  browser_snapshot()       — read the page content

## File access
Use Read/Write/Edit tools. Save files to $RESUME_OUTPUT_DIR.

---
"""


def definition(headed: bool = False, model: str | None = None) -> AgentDefinition:
    return AgentDefinition(
        description=(
            "Tailors resumes and cover letters for shortlisted jobs. "
            "Fetches each job description, rewrites resume bullets to match, "
            "and produces .docx files. Run after the search agent."
        ),
        model=model or "opus",
        prompt=HEADER + load_skill_prompt("tailor"),
        tools=[
            "Bash", "Read", "Write", "Edit", "Glob", "WebSearch", "WebFetch",
            "mcp__playwright__browser_navigate",
            "mcp__playwright__browser_snapshot",
            "mcp__playwright__browser_click",
            "mcp__playwright__browser_type",
            "mcp__playwright__browser_fill_form",
            "mcp__playwright__browser_press_key",
            "mcp__playwright__browser_select_option",
            "mcp__playwright__browser_hover",
            "mcp__playwright__browser_evaluate",
            "mcp__playwright__browser_wait_for",
            "mcp__playwright__browser_take_screenshot",
            "mcp__playwright__browser_tabs",
            "mcp__playwright__browser_navigate_back",
            "mcp__playwright__browser_close",
            "mcp__playwright__browser_resize",
            "mcp__playwright__browser_handle_dialog",
            "mcp__playwright__browser_file_upload",
            "mcp__playwright__browser_drag",
            "mcp__playwright__browser_run_code",
        ],
        mcpServers=[{"playwright": playwright_mcp_shared(headed, "search")}],
    )
