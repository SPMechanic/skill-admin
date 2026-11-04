#!/usr/bin/env python3
"""Activity ledger hook for skill-admin.

Records every skill-script invocation to <project>/.audit/activity.jsonl
so plugin activity is visible as executed evidence: what ran, when, from
which skill, exit status, and wall duration. Pairs PreToolUse (start) and
PostToolUse (end) events, correlated by tool_use_id when present, else by
command hash. Writes nothing when no skills/*/scripts/ command is seen.

Output schema (one JSON object per line):
  ts            ISO-8601 UTC timestamp of completion
  session_id    Claude session id
  cwd           project directory the hook ran in
  skill         owning skill, parsed from skills/<name>/scripts/ in the command
  action        script name (e.g. recommend.py)
  command       full command line (structure only; no secrets by design)
  exit          exit code from tool_result, null when not reported
  duration_ms   wall time between PreToolUse and PostToolUse, null when
                the start record is missing (hook installed mid-run, or
                session restart between the two events)
  status        "ok" when exit is 0, "fail" otherwise, "unknown" when null

Input: the standard hook JSON on stdin. Usage:

  echo '{"tool_name":"Bash","tool_input":{"command":"..."}}' | log_activity.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

# Match a command path segment like skills/<skill>/scripts/<script>.
# Tolerates forward and back slashes, and "uv run" wrappers.
SKILL_CMD = re.compile(
    r"skills[\\/](?P<skill>[A-Za-z0-9_-]+)[\\/]scripts[\\/](?P<script>[A-Za-z0-9_.-]+)"
)

LEDGER = ".audit/activity.jsonl"
STATE_FILE = None  # resolved per call from cwd

_MAX_COMMAND = 2000  # truncate stored command text beyond this


def _state_path() -> Path:
    return Path(tempfile.gettempdir()) / "skill-admin-activity-state.json"


def _now_ms() -> float:
    return time.time() * 1000.0


def _iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def parse_event(raw: str) -> dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def match_skill_command(command: str) -> dict | None:
    if not command:
        return None
    m = SKILL_CMD.search(command)
    if not m:
        return None
    return {"skill": m.group("skill"), "action": m.group("script")}


def _load_state() -> dict:
    p = _state_path()
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(state: dict) -> None:
    p = _state_path()
    try:
        p.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        pass


def _exit_from_result(tool_result) -> int | None:
    """Extract an exit code from a Bash tool_result if present."""
    if not isinstance(tool_result, dict):
        return None
    # Common shapes: {"exit_code": n} or stdout/stderr text mentioning a code.
    code = tool_result.get("exit_code")
    if isinstance(code, int):
        return code
    return None


def _truncate(text: str) -> str:
    return text if len(text) <= _MAX_COMMAND else text[:_MAX_COMMAND] + "..."


def handle(event: dict) -> int:
    hook_event = event.get("hook_event_name", "")
    tool_name = event.get("tool_name", "")
    if tool_name != "Bash":
        return 0

    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    match = match_skill_command(command)
    if not match:
        return 0

    session_id = event.get("session_id", "")
    cwd = event.get("cwd") or os.getcwd()
    ledger_path = Path(cwd) / LEDGER

    key = None
    tool_use_id = event.get("tool_use_id")
    if tool_use_id:
        key = f"id:{tool_use_id}"
    else:
        key = "hash:" + hashlib.sha256(command.encode("utf-8")).hexdigest()[:16]

    state = _load_state()

    if hook_event == "PreToolUse":
        state[key] = {"t0": _now_ms(), "session_id": session_id}
        _save_state(state)
        return 0

    # PostToolUse: correlate and append.
    start = state.pop(key, None)
    if start:
        _save_state(state)
    duration_ms = None
    if start and isinstance(start.get("t0"), (int, float)):
        duration_ms = round(_now_ms() - start["t0"], 1)

    exit_code = _exit_from_result(event.get("tool_result"))

    entry = {
        "ts": _iso(),
        "session_id": session_id,
        "cwd": cwd,
        "skill": match["skill"],
        "action": match["action"],
        "command": _truncate(command.strip()),
        "exit": exit_code,
        "duration_ms": duration_ms,
        "status": "ok" if exit_code == 0 else "fail" if exit_code is not None else "unknown",
    }
    try:
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with ledger_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        # Never break the tool call because logging failed.
        return 0
    return 0


def main() -> int:
    raw = sys.stdin.read()
    event = parse_event(raw)
    if not event:
        return 0
    return handle(event)


if __name__ == "__main__":
    sys.exit(main())
