#!/usr/bin/env python3
"""
Job Autopilot — Claude Agent edition

Usage:
  python3 run.py [--headless] [--shortlist-target N] "<prompt>"

Options:
  --headless             Hide the browser window (default: show browser)
  --shortlist-target N   Stop searching after N shortlisted jobs (default: 30, persisted across runs)

Examples:
  python3 run.py "Run the full pipeline"
  python3 run.py --shortlist-target 10 "Run the full pipeline"
  python3 run.py --headless "Tailor resumes for shortlisted jobs"
  python3 run.py "Submit all resume_ready applications"
"""
import sys
import anyio


async def main():
    # Delegate all arg parsing to the same logic as the CLI entry point
    from jobautopilot_claude.cli import _parse_args, _read_config_value, _write_config_value, DEFAULT_SHORTLIST_TARGET
    import os

    headed, shortlist_target, login_timeout, prompt = _parse_args(sys.argv[1:])

    if not prompt:
        print(__doc__)
        sys.exit(1)

    if shortlist_target is not None:
        _write_config_value("JOB_SEARCH_SHORTLIST_TARGET", str(shortlist_target))
        os.environ["JOB_SEARCH_SHORTLIST_TARGET"] = str(shortlist_target)
    else:
        saved = _read_config_value("JOB_SEARCH_SHORTLIST_TARGET")
        target = saved if saved else str(DEFAULT_SHORTLIST_TARGET)
        os.environ.setdefault("JOB_SEARCH_SHORTLIST_TARGET", target)

    from agents.orchestrator import run
    await run(prompt, headed=headed)


if __name__ == "__main__":
    try:
        anyio.run(main)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
