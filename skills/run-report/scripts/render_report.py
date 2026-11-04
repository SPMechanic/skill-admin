#!/usr/bin/env python3
"""Render the activity ledger as a run report.

Reads <project>/.audit/activity.jsonl (written by hooks/log_activity.py)
and groups entries into runs — one run per session_id, ordered by time.
Text mode prints an indented tree per run in the style of a query plan;
--html writes a self-contained page with collapsible nodes.

Report-only: this never runs skill scripts and never writes to the ledger.

Usage:
  uv run skills/run-report/scripts/render_report.py [--html PATH] [--session ID]
                                                     [--limit N] [--ledger PATH]
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

DEFAULT_LEDGER = ".audit/activity.jsonl"


def load_entries(ledger: Path, session: str | None, limit: int | None) -> list[dict]:
    if not ledger.exists():
        return []
    entries: list[dict] = []
    for line in ledger.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if session and entry.get("session_id") != session:
            continue
        entries.append(entry)
    if limit is not None:
        entries = entries[-limit:]
    return entries


def group_runs(entries: list[dict]) -> "OrderedDict[str, list[dict]]":
    runs: "OrderedDict[str, list[dict]]" = OrderedDict()
    for entry in entries:
        key = entry.get("session_id") or "(no session)"
        runs.setdefault(key, []).append(entry)
    return runs


def fmt_duration(ms) -> str:
    if ms is None:
        return "?"
    if ms < 1000:
        return f"{ms:.0f}ms"
    if ms < 60_000:
        return f"{ms / 1000:.1f}s"
    minutes, seconds = divmod(ms / 1000, 60)
    if minutes < 60:
        return f"{int(minutes)}m {seconds:.0f}s"
    hours, minutes = divmod(int(minutes), 60)
    return f"{hours}h {minutes}m"


def run_status(entries: list[dict]) -> tuple[str, int, int, float]:
    fails = sum(1 for e in entries if e.get("status") == "fail")
    unknown = sum(1 for e in entries if e.get("status") == "unknown")
    total_ms = sum(e.get("duration_ms") or 0 for e in entries)
    if fails:
        verdict = "FAIL"
    elif unknown:
        verdict = "PARTIAL"
    else:
        verdict = "OK"
    return verdict, fails, unknown, total_ms


def fmt_time(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%H:%M:%S")
    except (ValueError, TypeError):
        return "--:--:--"


def render_text(runs: "OrderedDict[str, list[dict]]") -> str:
    if not runs:
        return "No skill-script activity recorded in the ledger."
    out: list[str] = []
    for session_id, entries in runs.items():
        verdict, fails, unknown, total = run_status(entries)
        head = (
            f"session {session_id}  |  {len(entries)} invocation"
            f"{'' if len(entries) == 1 else 's'}  |  total {fmt_duration(total)}  |  {verdict}"
        )
        out.append(head)
        out.append("=" * len(head))
        for index, e in enumerate(entries, 1):
            marker = "x" if e.get("status") == "fail" else "!"
            if e.get("status") == "unknown":
                marker = "?"
            elif e.get("status") == "ok":
                marker = "+"
            stem = f"{index}."
            line = (
                f"{stem:>4} [{marker}] {e.get('skill', '?')}/{e.get('action', '?')}"
                f"  {fmt_duration(e.get('duration_ms'))}"
                f"  exit={e.get('exit') if e.get('exit') is not None else '?'}"
                f"  {fmt_time(e.get('ts', ''))}"
            )
            out.append(line)
            out.append(f"        {e.get('command', '')}")
            if e.get("cwd"):
                out.append(f"        cwd {e['cwd']}")
        notes = []
        if fails:
            notes.append(f"{fails} failed")
        if unknown:
            notes.append(f"{unknown} with unknown exit")
        if notes:
            out.append(f"  {', '.join(notes)}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>skill-admin activity report</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font: 14px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace;
         margin: 2rem auto; max-width: 60rem; padding: 0 1rem; }}
  h1 {{ font-size: 1.1rem; }}
  .run {{ border: 1px solid color-mix(in srgb, currentColor 22%, transparent);
          border-radius: 6px; margin: 1rem 0; overflow: hidden; }}
  .run > summary {{ cursor: pointer; padding: .6rem .9rem; font-weight: 600;
                    background: color-mix(in srgb, currentColor 6%, transparent); }}
  .run-body {{ padding: .2rem .9rem .7rem; }}
  .node {{ border-left: 2px solid transparent; padding: .25rem 0 .25rem .7rem; }}
  .node.ok  {{ border-left-color: #2f9e44; }}
  .node.fail{{ border-left-color: #e03131; }}
  .node.unknown {{ border-left-color: #f08c00; }}
  details > summary {{ cursor: pointer; list-style: none; }}
  details > summary::-webkit-details-marker {{ display: none; }}
  .meta {{ color: color-mix(in srgb, currentColor 62%, transparent); }}
  .detail {{ margin: .25rem 0 .25rem 1.1rem; }}
  .cmd {{ white-space: pre-wrap; word-break: break-word;
          background: color-mix(in srgb, currentColor 7%, transparent);
          padding: .4rem .6rem; border-radius: 4px; }}
  .badge {{ font-size: .75rem; padding: .05rem .4rem; border-radius: 3px;
            border: 1px solid currentColor; }}
  .bar {{ height: 4px; border-radius: 2px; background: #2f9e44; }}
</style>
</head>
<body>
<h1>skill-admin activity report</h1>
<p class="meta">{generated} &middot; {count} invocation(s) across {runs} run(s)
&middot; ledger <code>{ledger}</code></p>
{body}
</body>
</html>
"""


def render_html(runs: "OrderedDict[str, list[dict]]", ledger: Path) -> str:
    blocks: list[str] = []
    if not runs:
        blocks.append("<p>No skill-script activity recorded in the ledger.</p>")
    for session_id, entries in runs.items():
        verdict, fails, unknown, total = run_status(entries)
        nodes: list[str] = []
        # Scale each bar against the longest step in this run.
        longest = max((e.get("duration_ms") or 0) for e in entries) or 1
        for e in entries:
            status = e.get("status") if e.get("status") in ("ok", "fail") else "unknown"
            duration = e.get("duration_ms")
            width = int(100 * (duration or 0) / longest)
            nodes.append(
                f'<div class="node {status}">'
                f"<details><summary>"
                f"<span class=\"badge\">{status}</span> "
                f"{html.escape(str(e.get('skill', '?')))}/"
                f"{html.escape(str(e.get('action', '?')))} "
                f'<span class="meta">{fmt_duration(duration)} '
                f"&middot; exit {e.get('exit') if e.get('exit') is not None else '?'} "
                f"&middot; {fmt_time(e.get('ts', ''))}</span>"
                f"</summary>"
                f'<div class="detail"><div class="bar" style="width:{width}%"></div>'
                f'<div class="cmd">{html.escape(str(e.get("command", "")))}</div>'
                f'<div class="meta">cwd {html.escape(str(e.get("cwd", "")))}</div>'
                f"</div></details></div>"
            )
        blocks.append(
            f'<details class="run" open><summary>{html.escape(session_id)} '
            f'<span class="meta">&middot; {len(entries)} invocation(s) &middot; '
            f"{fmt_duration(total)} &middot; {verdict}</span></summary>"
            f'<div class="run-body">{"".join(nodes)}</div></details>'
        )
    return HTML_TEMPLATE.format(
        generated=datetime.now().strftime("%Y-%m-%d %H:%M"),
        count=sum(len(v) for v in runs.values()),
        runs=len(runs),
        ledger=html.escape(str(ledger)),
        body="\n".join(blocks),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render the skill-admin activity ledger")
    parser.add_argument("--ledger", default=DEFAULT_LEDGER, help=f"ledger path (default {DEFAULT_LEDGER})")
    parser.add_argument("--session", default=None, help="only this session_id")
    parser.add_argument("--limit", type=int, default=None, help="last N entries only")
    parser.add_argument("--html", default=None, metavar="PATH", help="write an HTML report instead of text")
    args = parser.parse_args(argv)

    ledger = Path(args.ledger)
    entries = load_entries(ledger, args.session, args.limit)
    runs = group_runs(entries)

    if args.html:
        out = Path(args.html)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_html(runs, ledger), encoding="utf-8")
        print(f"wrote {out} ({sum(len(v) for v in runs.values())} entries, {len(runs)} runs)")
        return 0

    sys.stdout.write(render_text(runs))
    return 0


if __name__ == "__main__":
    sys.exit(main())
