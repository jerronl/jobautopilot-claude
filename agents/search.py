"""Search subagent definition."""
from claude_agent_sdk import AgentDefinition
from .base import load_skill_prompt, playwright_mcp_with_profile

HEADER = """\
You are a job search automation agent.

## Browser access
You control a persistent browser via Playwright MCP tools. Your browser profile
saves cookies so login sessions survive across runs.

  browser_navigate(url)               — navigate to a URL
  browser_snapshot()                  — get the page accessibility tree
  browser_screenshot()                — take a screenshot
  browser_click(element, ref)         — click an element
  browser_fill(element, ref, value)   — fill a text input
  browser_tab_new()                   — open a new tab
  browser_tab_list()                  — list open tabs
  browser_tab_close(index)            — close a tab

## Login check — do this FIRST before any searching

1. browser_navigate("https://www.linkedin.com/feed/")
2. browser_snapshot() — look for a login/sign-in form
3. If NOT logged in:
   - Print: [Search] ⚠️  Not logged in to LinkedIn — browser is open, please log in
   - Keep calling browser_snapshot() (up to 30 times, ~10s apart) until the feed loads
   - Once logged in: print [Search] ✓ LinkedIn login confirmed — starting search
4. Repeat for any other site you plan to search (eFinancialCareers, Indeed, etc.)

## Progress log — write a line for every significant event

Append to `$SEARCH_PROGRESS_LOG` (set by orchestrator) so the user sees real-time
progress. Use Bash:

```bash
echo "$(date +%H:%M:%S) 🔍 <message>" >> "$SEARCH_PROGRESS_LOG"
```

Write a line for:
- Starting each platform (LinkedIn, eFinancialCareers, Indeed, …)
- Each job found: `✓ Company — Role (status; reason)`
- Each job rejected: `✗ Company — Role (screen_reject; reason)`
- Login waits, errors, or anything else notable

## File access
Use Read/Write/Edit/Bash tools for the tracker, handoff files, and progress log.

---
"""


def definition(headed: bool = False) -> AgentDefinition:
    return AgentDefinition(
        description=(
            "Searches LinkedIn and other job boards for roles matching the candidate profile. "
            "Reads the resume pool to build keywords, applies hard filters, and writes results "
            "to the job tracker. Use this agent first in the pipeline."
        ),
        prompt=HEADER + load_skill_prompt("search"),
        tools=["Read", "Write", "Edit", "Glob", "WebSearch", "WebFetch"],
        mcpServers={"playwright": playwright_mcp_with_profile(headed, "search")},
    )
