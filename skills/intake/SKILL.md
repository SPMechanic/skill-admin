---
name: intake
description: >
  Step 0 Intent Articulation. Consumes one raw user prompt and produces a gated
  plan table (rows = steps; columns = action, capability, reason, evidence,
  coordinates, inferred-from) before any routing or execution. Use when the
  user gives an unstructured or ambiguous request, says "plan this", "route
  this", "figure out what I need", or when skill-orchestrator Mode C receives a
  raw prompt instead of a pre-structured plan. This skill does not route, score,
  or execute — it articulates intent into a checkable plan and stops at the gate.
executor: false
---

# Intake — Step 0 Intent Articulation

The pipeline's entry point. Every other component assumes a pre-articulated plan;
intake is what produces one from a raw prompt.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `uv run skills/plugin-router/scripts/recommend.py` for mechanical scoring |
| Claude Desktop (Cowork) | Same script — works identically |
| Claude Desktop (Code) | Same script — works identically |
| 3P CLI/Desktop | Same as official surface |

## What this skill does

| Action | Scope |
|---|---|
| **Articulate** | Convert one raw prompt into domain, stage, file sets, and candidate capabilities |
| **Structure** | Emit a plan table with one row per proposed step |
| **Gate** | Pause for explicit user approval before any execution |
| **Hand off** | Pass the approved plan to `skill-admin:skill-orchestrator` or `skill-admin:plugin-router` |

## Input

A single raw prompt, e.g. *"add auth to the API"* or *"set up my project for AI
orchestration"*. Optionally a working directory.

## Output — plan table

Every row must carry all columns. A row without `coordinates` and `inferred-from`
is incomplete; the plan is not valid until every row has both.

| step | action | capability | reason | evidence / files | coordinates | inferred-from |
|---|---|---|---|---|---|---|
| 1 | analyze | `plugin-router` | exact-table-match | — | prompt: "set up … orchestration" | "set up my project for AI orchestration" |
| 2 | route | `project-atlas` | exact-table-match | CLAUDE.md, pyproject.toml | repo root | "my project" |
| 3 | install | `plugin-manager` | catalog-gap-fallback | atlas gap rows | — | (gap row name) |

### Enumerated `reason` values

The `reason` column and every announce-routing "because" clause must use exactly one of:

- `exact-table-match` — the intent appears verbatim in a plugin-router routing table
- `keyword-fallback` — matched by keyword against the catalog index
- `catalog-gap-fallback` — no installed capability fits; closest wishlist entry used
- `user-specified` — the user named the capability directly

Any other value is invalid. This makes announcements diffable and testable.

### `coordinates` column

Enough to re-run the step: file paths, repo root, the prompt fragment that triggered
the row, or a gap-row name. If a later step fails, `coordinates` is what lets an
independent branch continue without it.

## Procedure

1. Read the prompt. Extract candidate domain(s) and lifecycle stage (scope / plan /
   build / test / review / ship).
2. Run the mechanical filter:
   ```
   uv run skills/plugin-router/scripts/recommend.py "<prompt>"
   ```
   Treat its output as candidates only — never the final ranking.
3. For each step, fill one plan-table row. Prefer exact-table-match; fall back to
   keyword-fallback; use catalog-gap-fallback only when nothing installed fits and
   say which wishlist entry you'd install.
4. **Gate**: present the plan table and stop. Do not proceed until the user
   approves, edits, or rejects the plan.
5. On approval, hand the approved table to `skill-admin:skill-orchestrator`
   (Mode C for anything destructive, Mode A otherwise).

## Guardrails

- Intake never routes, never installs, never edits files. It emits the plan and
  stops at the gate.
- If the prompt is already a structured plan, pass it through unchanged — do not
  re-articulate.
- If the prompt names a capability directly (`reason: user-specified`), keep that
  row even when recommend.py ranks something else higher.
- A mid-stride pivot to a different domain or stage (greenfield ↔ brownfield,
  build ↔ migrate) is a new intake run, not a silent plan edit.

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Emits plan table in chat; gate is a chat confirmation. Uses `recommend.py` for mechanical scoring. |
| **Claude Desktop (Cowork)** | Full support. Same script works — no CLI dependency. Gate requires explicit confirmation before any executor runs. |
| **Claude Desktop (Code)** | Full support. Same boundary contract as CLI. |
| **3P CLI/Desktop** | Full support. Same as official surface. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
