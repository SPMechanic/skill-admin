---
name: skill-orchestrator
description: >
  Coordinate multiple Claude Code skills for complex tasks that require more than
  one skill. Use when the user says "run all my skills", "coordinate the pipeline",
  "run the full workflow", "orchestrate my setup", or when a task spans analysis,
  routing, and execution. This skill sequences other skills but does not route,
  audit, install, or repair.
executor: false
---

# Skill Orchestrator

Sequences multiple Claude Code skills for complex tasks. **This skill coordinates;
it does not route, audit, or execute.** All steps require user confirmation.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `claude plugin` for skill availability check |
| Claude Desktop (Cowork) | Read `installed_plugins.json` for skill availability |
| Claude Desktop (Code) | Read `installed_plugins.json` for skill availability |
| 3P CLI/Desktop | Same as official surface |

## What this skill does

| Action | Scope |
|---|---|
| **Sequence** | Define the order of skill execution |
| **Coordinate** | Pass outputs between skills |
| **Track** | Monitor progress across skills |
| **Report** | Summarize combined results |

## Orchestration modes

### Mode A — Linear

```
skill1 → skill2 → skill3
```

Use when:
- Each step depends on the previous
- No parallelization is possible

### Mode B — Parallel

```
skill1 ──┐
         ├──→ merge → skill4
skill2 ──┘
```

Use when:
- Skills touch independent files
- No shared state between them
- No ordering dependencies

### Mode C — Sequential with gates

```
skill1 → [gate: user approval] → skill2 → [gate] → skill3
```

Use when:
- Destructive operations are involved
- Each step needs explicit approval
- Compliance requires sign-off

## Parallel-split safety rubric

Before allowing any parallel fan-out, check all 4 axes:

| # | Axis | Safe condition |
|---|---|---|
| 1 | Shared | Each subtask touches a distinct file set — no overlaps |
| 2 | State | No shared mutable state (config, DB, global counters) |
| 3 | Ordering | No step's output feeds another step's input |
| 4 | Destructive | No subtask does something irreversible |

**ALL 4 must be safe to allow parallel.** Any single failure → Mode C
(sequential with HITL gate).

## Workflow

### Step 1 — Identify skills involved

Determine which skills are needed for the task. If the entry point is a raw prompt
rather than a pre-structured plan, run `skill-admin:intake` first — intake emits the
plan table and stops at its own gate; orchestration begins only from an approved plan.
If the caller already provided a structured plan, accept it as-is (pre-structured
input stays supported).

### Step 2 — Classify the pattern

| Pattern | Mode |
|---|---|
| Simple sequential | A |
| Independent tasks | B |
| Destructive or gated | C |

### Step 3 — Create a plan

```markdown
## Orchestration Plan

### Skills involved
1. project-atlas — analyze project
2. marketplace-optimizer — audit stack
3. plugin-manager — install missing
4. steering-writer — create CLAUDE.md

### Mode: C (sequential with gates)

### Steps
| # | Skill | Action | Gate? |
|---|---|---|---|
| 1 | project-atlas | Analyze project | No |
| 2 | marketplace-optimizer | Audit stack | No |
| 3 | plugin-manager | Install missing | Yes — destructive |
| 4 | steering-writer | Write CLAUDE.md | Yes — file write |

### Outputs
- atlas map
- health report
- install log
- CLAUDE.md
```

### Step 4 — Execute with gates

For Mode C, pause after each gated step for user approval.

**Gate records.** Every gate produces a machine-readable record, not just a chat
pause. Append one JSON line per gate to the run log (`.skill-admin/gates.jsonl`
in the current project, or print it when no writeable root exists):

```json
{"run_id":"<uuid>","step":3,"gate":"user approval","decision":"approved|rejected","timestamp":"<iso8601>","reason":"<one-line>"}
```

A run is auditable when the gate records for its gated steps can be re-read; a run
is resumable when the last record tells you which step to restart from.

**Per-branch continuation.** "Stop on any failure" is the default, but when a failed
step's output is not consumed by any later step (its plan row `coordinates` are not
referenced by downstream rows), the orchestrator may continue the independent
branches and report the failed branch separately. State the dependency check
explicitly before continuing.

### Step 5 — Report

```markdown
## Orchestration Report

**Task**: {description}
**Mode**: {A/B/C}
**Skills executed**: {list}

### Results
| Skill | Result | Notes |
|---|---|---|
| project-atlas | Success | Mapped 12 capabilities |
| marketplace-optimizer | Success | 2 gaps found |
| plugin-manager | Success | Installed 2 plugins |
| steering-writer | Success | Created CLAUDE.md |

### Remaining
- {follow-up actions}
```

## What this skill does NOT do

- This skill does not route tasks to capabilities
- This skill does not audit or score plugins
- This skill does not install or repair plugins
- This skill does not write steering files
- This skill does not execute skills directly — it coordinates

## Error handling

| Error | Response |
|---|---|
| Skill fails mid-pipeline | Stop, report, ask user whether to continue |
| Gate rejected | Skip step, note in report |
| Circular dependency detected | Report and stop |
| Unknown skill requested | Suggest closest match or ask user |

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `claude plugin list` to verify skill availability. |
| **Claude Desktop (Cowork)** | Full support. Reads `installed_plugins.json` directly. Executor skills pause for explicit confirmation. |
| **Claude Desktop (Code)** | Full support. Project-scoped plugins honored. |
| **3P CLI/Desktop** | Full support. Same as official surface. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
