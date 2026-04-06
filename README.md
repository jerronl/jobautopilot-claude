# Job Autopilot — Claude Agent Edition

AI-powered job search, resume tailoring, and application pipeline built on the [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk).

Three specialized subagents coordinated by an orchestrator:

| Agent             | What it does                                                                                                                                                                                                                                                                                                |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **job-search**    | Reads your resume pool to build a candidate profile (skills, titles, seniority, industries). Uses that profile to drive keyword selection and filtering, then searches LinkedIn, Indeed, Glassdoor, ZipRecruiter, and company career pages. Writes results to a tracker.                                    |
| **resume-tailor** | Reads your resume pool to extract every bullet, metric, and tool name as raw material. Fetches each shortlisted job description, rewrites bullets to match, and produces tailored `.docx` resume + cover letter — 100% based on your real experience, nothing invented.                                     |
| **job-submitter** | Opens each application form, fills fields, uploads the tailored resume and cover letter, and submits. Handles login walls autonomously: checks saved credentials, tries Forgot Password (fetches reset link from your webmail), or creates a new account — falling back to a human pause only for CAPTCHAs. |

![Pipeline running — search, tailor, and submit in parallel](assets/screenshot.png)

## Requirements

- Python 3.11+
- Node.js (for Playwright MCP browser automation)
- Auth: [Claude CLI](https://claude.ai/code) (already logged in), or an [Anthropic API key](https://console.anthropic.com/)

## Setup

```bash
git clone https://github.com/jerronl/jobautopilot-claude
cd jobautopilot-claude
./setup.sh
```

`setup.sh` will ask for your personal info, then install dependencies and Playwright browsers.

## Resume pool

After setup, put your resume files in the directory you configured (default: `~/Documents/jobs/`):

```
~/Documents/jobs/
├── Resume_2026.docx    # master resume — full history, even items normally cut
├── skills.md           # certifications, tools, side projects, publications
└── bio.txt             # optional personal statement for cover letters
```

**Both the search and tailor agents read this pool first**, before doing anything else. The search agent builds a candidate profile from it — extracting your skills, past titles, industries, and seniority signals — and uses that profile to select keywords, set filters, and skip roles where you clearly don't meet hard requirements. The tailor agent then reads every bullet point and metric as raw material for rewriting, ensuring nothing is invented.

## Usage

```bash
source ~/.jobautopilot/config.sh

# Run individual stages (browser window shown by default)
jobautopilot "Search for quant developer jobs in New York"
jobautopilot "Tailor resumes for shortlisted jobs"
jobautopilot "Submit all resume_ready applications"

# Or let the orchestrator decide
jobautopilot "Run the full pipeline"

# Hide the browser window
jobautopilot --headless "Run the full pipeline"
```

The orchestrator runs all three stages concurrently — search, tailor, and submit overlap as a conveyor belt. Real-time progress appears inline in the terminal, including which company and round the submitter is on.

## Tracker

The job tracker lives at `~/.jobautopilot/workspace/job_application_tracker.md`.

| Status          | Meaning                                                         |
| --------------- | --------------------------------------------------------------- |
| `found`         | Discovered by search, not yet screened                          |
| `screen_reject` | Filtered out (salary, location, seniority, duplicate)           |
| `user_reject`   | Skipped after user review                                       |
| `shortlist`     | Approved, waiting for resume tailoring                          |
| `tailoring`     | Resume/cover letter in progress                                 |
| `resume_ready`  | `.docx` files ready, waiting to submit                          |
| `applied`       | Application submitted successfully                              |
| `blocked`       | Submitter could not complete (login wall, CAPTCHA, broken form) |
| `expired`       | Job listing no longer active                                    |
| `hold`          | Paused, revisit later                                           |
| `error`         | Something went wrong                                            |

## Reconfiguring

Re-run `./setup.sh` at any time to update your personal info or preferences. Existing tracker and resume files are not affected.

## License

MIT-0

## Support

If Job Autopilot saved you time, a coffee is always appreciated ☕

[![PayPal](./assets/qr-paypal.jpg)](https://paypal.me/ZLiu308)

[paypal.me/ZLiu308](https://paypal.me/ZLiu308)
