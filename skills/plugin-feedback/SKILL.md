---
name: plugin-feedback
description: >
  Capture routing misses, bad recommendations, and skill feedback to improve
  skill-admin's routing quality. Use when the user says "log this miss",
  "report bad routing", "skill-admin missed", "this recommendation was wrong",
  "feedback", or "improve routing". This skill writes feedback to local files
  that marketplace-optimizer reads during gap analysis. It does not modify
  plugins or routing tables.
metadata:
  executor: false
---

# Plugin Feedback

Captures routing feedback to improve skill-admin's recommendation quality.
**This skill writes feedback; it does not modify plugins.** All writes require
explicit user confirmation.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `Write`/`Edit` tools to append to `feedbacks/feedback-<YYYY-MM-DD>.md` |
| Claude Desktop (Cowork) | `Write`/`Edit` tools — same as CLI |
| Claude Desktop (Code) | `Write`/`Edit` tools — same as CLI |
| 3P CLI/Desktop | `Write`/`Edit` tools — same as CLI |

## What this skill does

| Action | Scope |
|---|---|
| **Capture** | Record a routing miss or bad recommendation |
| **Classify** | Tag feedback by severity and type |
| **Store** | Write to `feedbacks/feedback-<YYYY-MM-DD>.md` (gitignored) |

## When to use

- User says "this recommendation was wrong"
- User says "skill-admin missed X"
- User says "you should have routed to Y"
- User says "log this as feedback"
- User says "improve routing"

## Feedback schema

Each entry is a markdown section:

```markdown
## Feedback — <ISO-8601 timestamp>

| Field | Value |
|---|---|
| Triggering skill | plugin-router / project-atlas / intake / etc. |
| User intent | <what the user actually wanted> |
| Expected capability | <what should have been recommended> |
| Actual result | <what was actually recommended> |
| Suggested fix | <routing table update, new keyword, etc.> |
| Severity | critical / high / medium / low |
```

## How to run

### Step 1 — Identify the feedback

Determine: what was the user's intent, what was recommended, what should have been recommended, and what's the severity?

### Step 2 — Present for confirmation

Show the **full feedback entry table** from the schema above, including all fields: Triggering skill, User intent, Expected capability, Actual result, Suggested fix, Severity.

Mention the target file: "Write this to `feedbacks/feedback-<YYYY-MM-DD>.md`?"

Ask: "Write this feedback?"

### Step 3 — Write

Append to `feedbacks/feedback-<YYYY-MM-DD>.md`. Create directory if needed.

### Step 4 — Confirm

Report: "Feedback recorded at `feedbacks/feedback-<YYYY-MM-DD>.md`. marketplace-optimizer will read this during gap analysis."

## What this skill does NOT do

- Does not modify routing tables
- Does not modify plugin.json or marketplace.json
- Does not install or remove plugins
- Does not write to any file outside `feedbacks/`

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `Write`/`Edit` tools to append feedback files. |
| **Claude Desktop (Cowork)** | Full support. Same `Write`/`Edit` tools — pauses for confirmation. |
| **Claude Desktop (Code)** | Full support. Same `Write`/`Edit` tools. |
| **3P CLI/Desktop** | Full support. Same `Write`/`Edit` tools. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
