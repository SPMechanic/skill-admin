#!/usr/bin/env python3
"""
Read-only recall of audit work from prior session transcripts.

Claude Code stores each session as JSONL under `~/.claude/projects/<slug>/`.
When a user says "we already audited this", re-deriving the completion contract
burns tokens on work that is already on disk. This script extracts candidate
acceptance criteria, statuses, and evidence lines from those transcripts.

It reports *candidates*, never conclusions. An imported finding is a claim: a
prior `PASS` says only that something once looked done, in a session whose
working tree, dependencies, and gates may all have changed since. The caller
re-verifies every imported criterion with a real gate run before it can appear
in a report as anything other than NOT RUN.

Local transcript store only. Nothing is read from or sent to the network.

Usage:
    uv run skills/force-complete-slice/scripts/recall_audit.py [ROOT] \
        [--slice TEXT] [--limit N] [--max-bytes N] [--json]

Exit code:
    0 — recall completed (zero matches is still a successful run)
    2 — root does not exist, or is not a directory
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

AC_RE = re.compile(r"\bAC-(\d{1,3})\b")
STATUSES = ("PARTIAL", "BLOCKED", "NOT RUN", "NOT APPLICABLE", "PASS", "FAIL")
STATUS_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in STATUSES) + r")\b"
)
# Lines worth keeping as candidate evidence rather than whole turns.
EVIDENCE_RE = re.compile(
    r"\b(passed|failed|failing|error|assert|traceback|exit code|"
    r"no tests ran|collected \d+)\b",
    re.IGNORECASE,
)

STOPWORDS = {
    "the", "a", "an", "and", "or", "for", "with", "this", "that", "from",
    "into", "when", "then", "than", "have", "has", "was", "were", "are",
    "add", "fix", "make", "use", "our", "its", "it's", "not", "but", "all",
    "slice", "feature", "repo", "code", "work", "need", "want", "please",
}

SKIP_KEYS = {"queue-operation", "attachment", "file-history-snapshot",
             "file-history-delta", "atis-latch", "custom-title", "agent-name",
             "last-prompt", "api-request-shape", "api-request"}


def project_slug(root: Path) -> str:
    """Claude Code's project-slug convention: absolute path, separators -> '-'."""
    p = str(root.resolve()).replace("\\", "/")
    p = re.sub(r"^([A-Za-z]):", r"\1-", p)
    return p.replace("/", "-")


def keywords(text: str | None) -> set[str]:
    if not text:
        return set()
    words = re.findall(r"[a-z0-9]{3,}", text.lower())
    return {w for w in words if w not in STOPWORDS}


def iter_records(path: Path):
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except (ValueError, TypeError):
                    continue
    except OSError:
        return


def text_of(record: dict) -> str:
    """Flatten the human-readable text of one transcript record."""
    parts: list[str] = []

    def walk(node):
        if isinstance(node, str):
            parts.append(node)
        elif isinstance(node, dict):
            for k, v in node.items():
                if k in ("type", "uuid", "parentUuid", "sessionId", "todos"):
                    continue
                if k == "content":
                    walk(v)
                elif isinstance(v, (dict, list)):
                    walk(v)
                elif isinstance(v, str) and len(v) > 20:
                    parts.append(v)
        elif isinstance(node, list):
            for item in node:
                walk(item)

    walk(record.get("content"))
    msg = record.get("message")
    if isinstance(msg, dict):
        walk(msg.get("content"))
    return "\n".join(parts)


def trim(text: str, limit: int = 300) -> str:
    text = re.sub(r"^(?:[-*•]+|\d+[.)])\s*", "", " ".join(text.split()))
    return text if len(text) <= limit else text[: limit - 1] + "…"


def scan_file(path: Path, slice_keys: set[str], cap: int) -> list[dict]:
    found: list[dict] = []
    by_ac: dict[str, dict] = {}
    budget = cap

    for record in iter_records(path):
        if record.get("type") in SKIP_KEYS:
            continue
        if budget <= 0:
            break
        text = text_of(record)
        if not text:
            continue
        budget -= len(text)

        # Match at record level as well as line level: a record about this
        # slice often states its criteria on lines that never repeat the
        # keywords, and line-only matching silently loses them.
        record_hits = slice_keys.intersection(keywords(text)) if slice_keys else set()
        if slice_keys and not record_hits:
            continue

        ts = record.get("timestamp") or ""
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            ac_ids = AC_RE.findall(line)
            if not ac_ids:
                continue
            hits = slice_keys.intersection(keywords(line)) or record_hits
            status = STATUS_RE.search(line)
            for num in ac_ids:
                key = f"AC-{num}"
                entry = by_ac.get(key)
                if entry is None:
                    entry = by_ac[key] = {
                        "id": key,
                        "file": path.name,
                        "latest_timestamp": ts,
                        "statements": [],
                        "statuses": [],
                        "keyword_hits": sorted(hits),
                    }
                    found.append(entry)
                if ts and ts > entry["latest_timestamp"]:
                    entry["latest_timestamp"] = ts
                if status and status.group(1) not in entry["statuses"]:
                    entry["statuses"].append(status.group(1))
                if len(entry["statements"]) < 6 and EVIDENCE_RE.search(line):
                    line_s = trim(line)
                    if line_s not in entry["statements"]:
                        entry["statements"].append(line_s)
    return found


def score(entry: dict, slice_keys: set[str]) -> tuple:
    hits = len(entry["keyword_hits"])
    return (hits, entry["latest_timestamp"], -int(entry["id"].split("-")[1]))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("root", nargs="?", default=".", help="repository root")
    ap.add_argument("--slice", default="", help="slice keywords to match")
    ap.add_argument("--limit", type=int, default=25, help="max groups to report")
    ap.add_argument("--max-bytes", type=int, default=2_000_000,
                    help="character budget per transcript file")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    root = Path(args.root)
    if not root.exists() or not root.is_dir():
        print(f"error: root is not a directory: {root}", file=sys.stderr)
        return 2
    root = root.resolve()

    base = Path.home() / ".claude" / "projects"
    slug = project_slug(root)
    session_dir = base / slug

    keys = keywords(args.slice)

    if not session_dir.is_dir():
        payload = {
            "root": str(root),
            "project_slug": slug,
            "session_dir": str(session_dir),
            "session_dir_found": False,
            "files_scanned": 0,
            "criteria": [],
            "note": "no transcript store for this project; nothing to recall",
        }
        if args.json:
            print(json.dumps(payload, indent=2))
        else:
            print(f"No transcripts at {session_dir}")
            print("Nothing to recall; derive the contract normally.")
        return 0

    files = sorted(
        session_dir.rglob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    merged: dict[str, dict] = {}
    for path in files:
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size == 0:
            continue
        for entry in scan_file(path, keys, args.max_bytes):
            prev = merged.get(entry["id"])
            if prev is None:
                merged[entry["id"]] = entry
                continue
            if entry["latest_timestamp"] > prev["latest_timestamp"]:
                merged[entry["id"]] = entry
            else:
                for s in entry["statuses"]:
                    if s not in prev["statuses"]:
                        prev["statuses"].append(s)

    criteria = sorted(merged.values(), key=lambda e: score(e, keys), reverse=True)
    criteria = criteria[: args.limit]

    payload = {
        "root": str(root),
        "project_slug": slug,
        "session_dir": str(session_dir),
        "session_dir_found": True,
        "files_scanned": len(files),
        "slice_keywords": sorted(keys),
        "criteria": criteria,
        "note": (
            "Imported findings are claims, not evidence. Re-verify every "
            "criterion with a real gate run; never carry a prior PASS forward."
        ),
    }

    if args.json:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Project: {slug}")
    print(f"Sessions: {len(files)} file(s) under {session_dir}")
    print(f"Slice keywords: {', '.join(sorted(keys)) or '(none)'}")
    print()
    if not criteria:
        print("No matching acceptance criteria found in transcripts.")
        print("Derive the contract normally.")
        return 0

    print(f"{len(criteria)} candidate criterion/criteria (claims, not evidence):")
    for e in criteria:
        status = ", ".join(e["statuses"]) or "no status seen"
        print(f"\n  {e['id']}  [{status}]  {e['latest_timestamp'] or 'unknown time'}")
        print(f"    source: {e['file']}")
        if e["keyword_hits"]:
            print(f"    matched: {', '.join(e['keyword_hits'])}")
        for s in e["statements"]:
            print(f"    - {s}")
    print("\nAll of the above enter the contract as NOT RUN until re-verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
