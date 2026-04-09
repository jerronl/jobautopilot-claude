#!/bin/bash
# Job Autopilot — example configuration (reference only)
# Run ./setup.sh to generate ~/.jobautopilot/config.sh interactively.

# ── Anthropic API ─────────────────────────────────────────────────────
export ANTHROPIC_API_KEY="sk-ant-..."

# ── Search ────────────────────────────────────────────────────────────
export JOB_SEARCH_KEYWORDS="python developer quant"
export JOB_SEARCH_LOCATION="New York City"
export JOB_SEARCH_MIN_SALARY=150000       # optional
export JOB_SEARCH_MAX_AGE_DAYS=90

# ── Resume pool ───────────────────────────────────────────────────────
export RESUME_DIR="$HOME/Documents/jobs/"
export RESUME_OUTPUT_DIR="$HOME/Documents/jobs/tailored/"

# ── Personal info ─────────────────────────────────────────────────────
export USER_FIRST_NAME="Your"
export USER_LAST_NAME="Name"
export USER_EMAIL="your@email.com"
export USER_PHONE="+1-555-000-0000"
export USER_LINKEDIN="https://linkedin.com/in/yourprofile"

# ── EEOC (US job applications) ────────────────────────────────────────
export USER_GENDER="Prefer not to say"
export USER_RACE="Prefer not to say"
export USER_HISPANIC="No"
export USER_VETERAN="I have no military service"
export USER_DISABILITY="No"
export USER_WORK_AUTH="Yes"
export USER_NEED_SPONSOR="No"
export USER_NON_COMPETE="No"
