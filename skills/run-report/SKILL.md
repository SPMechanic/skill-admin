---
name: run-report
description: >
  Render the skill-admin activity ledger (.audit/activity.jsonl) as a run
  report: what scripts ran, when, from which skill, with exit codes and
  durations — grouped by session. Use when the user asks "what did the
  plugin actually run", "show me the activity report", "what happened in
  that session", or wants evidence that narrated steps really executed.
  This skill reads the ledger and renders it; it never runs skill scripts
  and never writes to the ledger.
executor: false
---

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `uv run skills/run-report/scripts/render_report.py` (text tree) |
| Claude Desktop (Cowork) | `--html PATH` then send the file to the user |
| Claude Desktop (Code) | `--html PATH` then send the file to the user |
| 3P CLI/Desktop | Same as official surface |


### Step visibility

On start, materialize this skill's step sequence as a task list through the
surface's task tool — `TodoWrite` in Claude Code CLI, the plan widget on
Desktop — before the first action. Advance exactly one entry per step
transition; a list that jumps from all-pending to all-done is a progress
false-green, the same defect as an unexecuted `PASS`. On a surface with no
task tool, print a compact markdown checklist at each phase boundary instead.
Narrate each boundary with facts, not progress phrases. Before an action,
name the artifact — `activity.jsonl`, `render_report.py --html`, never
"the file". After it, state the result: counts, exit code, verdict, key
finding. "Progressing...", "executing read on...", and any line that could
describe any project are noise. A boundary line passes only if the user can
follow the run without expanding the tool call.

## What this skill does

Turns the executed-evidence ledger into something a human can read. The
ledger (written by the hooks/log_activity.py hook pair) records every
`skills/*/scripts/` invocation with timestamp, skill, script, command, exit
code, and paired duration. This skill renders it two ways:

1. **Text tree** — default. One block per session: invocation count, total
   wall time, verdict (OK / PARTIAL / FAIL), then one line per invocation
   with status marker, skill/script, duration, exit code, time, and the
   full command. Works on every surface, including plain terminals.
2. **HTML report** — `--html PATH`. Self-contained page with collapsible
   per-invocation nodes; each node shows a duration bar scaled against the
   longest step in its run, the full command, and the working directory.
   The interactive drill-down view; open it in a browser or send it on
   Desktop surfaces.

## Inputs

| Input | Where | Default |
|---|---|---|
| Ledger | `--ledger PATH` or `<project>/.audit/activity.jsonl` | `.audit/activity.jsonl` |
| One session only | `--session ID` | all sessions |
| Last N entries | `--limit N` | all |

## How to run

```bash
# Text tree of everything recorded
uv run skills/run-report/scripts/render_report.py

# Interactive HTML report
uv run skills/run-report/scripts/render_report.py --html .audit/report.html

# Just the last session's evidence
uv run skills/run-report/scripts/render_report.py --session "$(tail -1 .audit/activity.jsonl | jq -r .session_id)"
```

### Step 1 — Locate the ledger

Check `<project>/.audit/activity.jsonl` exists and is non-empty. An empty
or missing ledger is a finding, not an error: report that no skill-script
activity has been recorded (which may itself mean the hooks are not yet
active in the current session — they load at session start).

### Step 2 — Render

Run `render_report.py`. For CLI surfaces, the text tree is the deliverable.
For Desktop surfaces, prefer `--html` and send the file, since the text tree
loses its alignment in proportional fonts.

### Step 3 — Report to user

State the verdict per session and surface the failures first: which script,
which skill, what exit code. `duration_ms: null` entries mean the Pre event
was never seen (hook installed mid-run or session restart) — say so rather
than presenting them as measured timings.

## What this skill does NOT do

- Does not run any `skills/*/scripts/` tool besides its own renderer
- Does not write to the ledger or modify hook state
- Does not infer intent — it reports what ran, not why
