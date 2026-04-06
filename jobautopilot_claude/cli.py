"""CLI entry point for jobautopilot-claude."""
import os
import re
import sys
import anyio
from pathlib import Path

CONFIG_PATH = Path.home() / ".jobautopilot" / "config.sh"
DEFAULT_SHORTLIST_TARGET = 30
DEFAULT_LOGIN_TIMEOUT    = 60   # seconds to wait for manual login before auto-proceeding


def _read_config_value(key: str) -> str | None:
    """Read a single export value from config.sh."""
    if not CONFIG_PATH.exists():
        return None
    for line in CONFIG_PATH.read_text().splitlines():
        m = re.match(rf'^export {key}="?([^"]*)"?', line)
        if m:
            return m.group(1)
    return None


def _write_config_value(key: str, value: str) -> None:
    """Update or append an export line in config.sh."""
    if not CONFIG_PATH.exists():
        return
    text = CONFIG_PATH.read_text()
    pattern = rf'^(export {key}=).*$'
    new_line = f'export {key}="{value}"'
    if re.search(pattern, text, re.MULTILINE):
        text = re.sub(pattern, new_line, text, flags=re.MULTILINE)
    else:
        text = text.rstrip("\n") + f"\n{new_line}\n"
    CONFIG_PATH.write_text(text)


def _parse_int_flag(args: list[str], flag: str) -> tuple[list[str], int | None]:
    """Extract --flag N from args, return (remaining_args, value_or_None)."""
    if flag not in args:
        return args, None
    idx = args.index(flag)
    if idx + 1 >= len(args):
        print(f"Error: {flag} requires a value")
        sys.exit(1)
    try:
        value = int(args[idx + 1])
    except ValueError:
        print(f"Error: {flag} requires an integer, got '{args[idx+1]}'")
        sys.exit(1)
    return args[:idx] + args[idx + 2:], value


def _parse_args(args: list[str]) -> tuple[bool, int | None, int | None, str]:
    """Return (headed, shortlist_target, login_timeout, prompt)."""
    headless = "--headless" in args
    args = [a for a in args if a != "--headless"]
    args, shortlist_target = _parse_int_flag(args, "--shortlist-target")
    args, login_timeout    = _parse_int_flag(args, "--login-timeout")
    return not headless, shortlist_target, login_timeout, " ".join(args)


USAGE = """\
Usage: jobautopilot [--headless] [--shortlist-target N] [--login-timeout N] "<prompt>"

Options:
  --headless             Hide the browser window (default: show browser)
  --shortlist-target N   Stop searching after N shortlisted jobs (default: {shortlist}, persisted)
  --login-timeout N      Seconds to wait for manual login before auto-trying Forgot Password
                         (default: {login}s, persisted in tracker)

Examples:
  jobautopilot "Run the full pipeline"
  jobautopilot --shortlist-target 10 "Run the full pipeline"
  jobautopilot --login-timeout 120 "Submit all blocked applications"
  jobautopilot --headless "Tailor resumes for shortlisted jobs"
""".format(shortlist=DEFAULT_SHORTLIST_TARGET, login=DEFAULT_LOGIN_TIMEOUT)


_CONFIG_PATH = Path.home() / ".jobautopilot" / "config.sh"


def _load_config() -> None:
    """Auto-source config.sh if env vars aren't already set."""
    if os.environ.get("USER_EMAIL"):
        return  # already sourced

    if not _CONFIG_PATH.exists():
        print("Error: no config found. Run setup first:")
        print(f"  cd /path/to/jobautopilot-claude && ./setup.sh")
        sys.exit(1)

    # Parse export lines from config.sh and inject into current process
    loaded = []
    for line in _CONFIG_PATH.read_text().splitlines():
        line = line.strip()
        m = re.match(r'^export ([A-Z_][A-Z0-9_]*)="?([^"]*)"?', line)
        if m:
            key, val = m.group(1), m.group(2)
            if key == "PATH":
                # expand $PATH literal that setup.sh writes
                val = val.replace("$PATH", os.environ.get("PATH", ""))
                os.environ["PATH"] = val
            else:
                os.environ.setdefault(key, val)
            loaded.append(key)

    if not os.environ.get("USER_EMAIL"):
        print("Error: config.sh exists but USER_EMAIL is missing. Re-run setup:")
        print(f"  cd /path/to/jobautopilot-claude && ./setup.sh")
        sys.exit(1)


def main():
    headed, shortlist_target, login_timeout, prompt = _parse_args(sys.argv[1:])

    if not prompt:
        print(USAGE)
        sys.exit(1)

    _load_config()

    # Resolve shortlist target: CLI arg > config > default
    if shortlist_target is not None:
        _write_config_value("JOB_SEARCH_SHORTLIST_TARGET", str(shortlist_target))
        os.environ["JOB_SEARCH_SHORTLIST_TARGET"] = str(shortlist_target)
    else:
        saved = _read_config_value("JOB_SEARCH_SHORTLIST_TARGET")
        target = saved if saved else str(DEFAULT_SHORTLIST_TARGET)
        os.environ.setdefault("JOB_SEARCH_SHORTLIST_TARGET", target)

    # Resolve login timeout: CLI arg > tracker > default  (tracker read/write in orchestrator)
    if login_timeout is not None:
        os.environ["LOGIN_HUMAN_TIMEOUT"] = str(login_timeout)
        os.environ["LOGIN_HUMAN_TIMEOUT_OVERRIDE"] = "1"  # signal to orchestrator to persist

    from agents.orchestrator import run
    try:
        anyio.run(run, prompt, True, headed)
    except KeyboardInterrupt:
        print("\nStopped.")
        sys.exit(0)
