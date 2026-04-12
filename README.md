# 🚀 Job Autopilot — Claude Agent Edition

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT-0](https://img.shields.io/badge/License-MIT--0-yellow.svg)](https://opensource.org/licenses/MIT-0)
[![Powered by Claude SDK](https://img.shields.io/badge/Powered%20by-Claude%20Agent%20SDK-purple.svg)](https://github.com/anthropics/claude-agent-sdk)

An intelligent AI agent that searches for jobs, critically rewrites your resume, and submits applications automatically — end-to-end.

**It doesn't just blindly apply to jobs — it understands you first, and gets smarter every time it runs.**

![Pipeline running — search, tailor, and submit in parallel](assets/screenshot.png)

---

## ✨ Why this is different from a simple script

1. **It understands you first.**
   Before doing anything, it reads your master resume to build a real candidate profile (skills, titles, seniority).
   - **Search** uses this profile to filter roles and skip obvious mismatches.
   - **Tailoring** uses your existing bullets, metrics, and tool names as raw material to rewrite for each specific role. _Zero hallucinations, nothing invented._

2. **It remembers what it learns (The Compounding Advantage).**
   Every run writes back into a self-updating knowledge base. The next time it hits the same company or form system, it already knows the traps.
   - _4 companies in:_ It knows Capital One's Workday tenant has an anti-bot overlay.
   - _10 companies in:_ It knows BuiltIn's autocomplete doesn't accept "Computational Finance" but accepts "Finance".
   - _Ask it to check your inbox:_ It reads every email body (not just subject lines), flags OA deadlines and interview invites, and updates the tracker automatically — no OAuth, no MCP setup needed.
   - **The pipeline gets faster and more reliable without any manual tuning.**

---

## 🚦 Usage

Job Autopilot uses a natural language CLI.

```bash
source ~/.jobautopilot/config.sh

# Run individual stages (browser window shown by default)
jobautopilot "Search for quant developer jobs in New York"
jobautopilot "Tailor resumes for shortlisted jobs"
jobautopilot "Submit all resume_ready applications"

# Check your inbox and update tracker automatically
jobautopilot "Check my email for anything job-related I need to handle"

# Or let the orchestrator run everything
jobautopilot "Run the full pipeline"

# Hide the browser window
jobautopilot --headless "Run the full pipeline"
```

---

## 🧠 Architecture

Three specialized subagents coordinated by an orchestrator run concurrently like a conveyor belt:

| Agent                | Responsibility                                                                                                                                                  |
| :------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 🔍 **job-search**    | Reads your profile to drive keyword selection. Searches LinkedIn, Indeed, Glassdoor, ZipRecruiter, and company pages. Updates the tracker.                      |
| ✍️ **resume-tailor** | Fetches shortlisted job descriptions, rewrites your real resume bullets to match, and generates a tailored `.docx` + cover letter.                              |
| 🤖 **job-submitter** | Fills fields, uploads documents, and submits. Handles login walls autonomously (saved credentials, Forgot Password flows via webmail, or new account creation). |

Real-time progress appears inline in the terminal, including which company and round the submitter is on.

---

## 🛠 Setup

```bash
git clone https://github.com/jerronl/jobautopilot-claude
cd jobautopilot-claude
./setup.sh
```

`setup.sh` will ask for your personal info, then install dependencies and Playwright browsers.

**Requirements:**
- **Python 3.11+**
- **Node.js** (for Playwright browser automation)
- **Auth:** [Claude CLI](https://claude.ai/code) (already logged in) OR an [Anthropic API key](https://console.anthropic.com/)

## 📂 Resume Pool

After setup, put your resume in the directory you configured (default: `~/Documents/jobs/`):

```
~/Documents/jobs/
└── Resume_2026.docx          # master resume — full history, even items normally cut
└── Resume_for_ai.docx        # tailored for your specific angle
└── Resume_for_dreaming.docx  # any tailored versions
```

That's all you need. Both agents read this file first — search to build your profile, tailor to extract raw material for rewriting.

---

## 📚 Self-Updating Knowledge Base

Agents don't re-discover the same ATS quirks on every run. The `knowledge/` tree persists what the pipeline learns:

```
knowledge/
├── sites/                   # per-company quirks (keyed by parent company, not hostname)
│   ├── stripe.md            # "Location is a react-select autocomplete — type then click [role='option']"
│   ├── capital_one.md       # Workday click_filter anti-bot overlay, wait_human_login required
│   └── ...
└── skills/
    ├── ats_playbooks/       # verified click/upload/multiselect recipes per ATS
    │   ├── workday.md       # hierarchical source multiselect, 7-step SPA
    │   ├── oracle_hcm.md    # .cx-select-pill-section native-click requirement
    │   ├── ashby.md         # agent-authored, no human involvement
    │   └── _selectors.md    # cross-ATS CSS/evaluate pitfalls
    └── dropdowns/           # canonical → variant-list mappings
        ├── degrees.md       # "MS" / "M.S." / "Master of Science" / "MSc" / ...
        ├── countries.md     # "United States" / "USA" / "United States (+1)" / ...
        └── eeoc.md, majors.md, schools.md
```

Agents read these files before round 2 of any submission, and append new variants, quirks, and recipes during a once-per-job review pass. Each run's knowledge compounds into the next.

---

## 📊 Tracker

The job tracker lives at `~/.jobautopilot/workspace/job_application_tracker.md`.

| Status          | Meaning                                                         |
| --------------- | --------------------------------------------------------------- |
| `found`         | Discovered by search, not yet screened                          |
| `screen_reject` | Filtered out (salary, location, seniority, duplicate)           |
| `user_reject`   | Skipped after user review                                       |
| `shortlist`     | Approved, waiting for resume tailoring                          |
| `tailoring`     | Resume/cover letter in progress                                 |
| `resume_ready`  | `.docx` files ready, waiting to submit                          |
| 🟢 `applied`    | Application submitted successfully                              |
| 🔴 `denied`     | Employer rejected (rejection email received)                    |
| 🗓 `interviewing` | Interview stage (scheduling link or invite received)          |
| 🎉 `offer`      | Offer extended                                                  |
| ⚠️ `blocked`    | Submitter could not complete (login wall, CAPTCHA, broken form) |
| `expired`       | Job listing no longer active                                    |
| `hold`          | Paused, revisit later                                           |
| `error`         | Something went wrong                                            |

---

## ⚙️ Reconfiguring

Re-run `./setup.sh` at any time to update your personal info or preferences. Existing tracker and resume files are not affected.

---

## 📄 License

MIT-0

## 🧋 Support

If Job Autopilot saved you time, a coffee is always appreciated ☕

[![PayPal](./assets/qr-paypal.jpg)](https://paypal.me/ZLiu308)

[paypal.me/ZLiu308](https://paypal.me/ZLiu308)
