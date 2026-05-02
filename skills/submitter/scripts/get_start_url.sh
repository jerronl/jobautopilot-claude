#!/bin/bash
# Returns the best URL to navigate to for a blocked job.
# Usage: get_start_url.sh <job_id> <state_dir> <fallback_url>
JOB_ID="$1"
STATE_DIR="$2"
FALLBACK="$3"
LOG="$(dirname "$STATE_DIR")/submit_progress.log"

url=$(grep "$JOB_ID" "$LOG" 2>/dev/null | grep "ended on" | tail -1 | sed 's/.*ended on [^:]*: //')
[ -z "$url" ] && url=$(cat "$STATE_DIR/tab_url.txt" 2>/dev/null)
[ -z "$url" ] && url="$FALLBACK"
echo "$url"
