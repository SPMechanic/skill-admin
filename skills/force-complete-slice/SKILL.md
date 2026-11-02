---
name: force-complete-slice
description: >
  Drive one software slice to an evidence-backed completion state. Use when the
  user says "finish this feature end to end", "force complete this", "is this
  slice done", "complete this module", "what is left before we can ship it", or
  when a change spans several layers (domain, application, data, API, UI,
  integration, docs) and completion must be proven rather than assumed.
  Discovers the project's own commands and gates, writes a completion contract,
  verifies with real evidence, and reports PASS / PARTIAL / FAIL / BLOCKED /
  NOT RUN / NOT APPLICABLE with provenance. When blocked it escalates rather
  than quitting: local evidence, installed capabilities, real execution,
  external research, minimal reproduction, then an independent verdict from a
  strongest-model subagent. Does not commit, push, deploy, or touch production
  unless the user explicitly asks.
metadata:
  executor: true
---

# Force Complete Slice

Drives a single slice to a state that can be *defended with evidence*.
**"Force" means force evidence, not force activity.** Writing code, passing a
subset of tests, or a green single-node run is never completion on its own.

Three rules carry the whole skill:

1. **Discover before deciding.** Read the project's own instructions, commands,
   and gates. Its conventions outrank yours.
2. **Push until it is genuinely done.** A block is a hypothesis, not a verdict.
   Work the escalation ladder — local evidence, installed capabilities, real
   execution, external research, a different approach — before concluding
   anything is impossible. See
   [references/escalation-and-persistence.md](references/escalation-and-persistence.md).
3. **Never lower the bar to exit the loop.** The effort is unbounded; the
   evidence bar is fixed. When they conflict, the bar wins and the report says
   `BLOCKED`. A true `PARTIAL` is a success of this skill; a fabricated `PASS`
   is its only real failure.

This skill writes to the target project only. It never edits plugin state under
`~/.claude/` and never modifies this repository.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | Full path: `Bash` runs `discover_gates.py` and `completion_status.py`; `Bash` executes the project's gates; `Write`/`Edit` for slice changes |
| Claude Desktop (Cowork) | `Write`/`Edit` work; **shell may be unavailable** — see fallback below |
| Claude Desktop (Code) | Same as Cowork; same fallback |
| 3P CLI/Desktop | Same as the equivalent official surface |

### When the shell is unavailable

Both scripts are conveniences, not the contract. On a surface without a shell,
do the same work with files and the rule table:

- **Discovery** — reproduce `discover_gates.py` by reading the repo directly:
  `Glob` for `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`,
  `Makefile`, `justfile`, `.github/workflows/*`, `docker-compose.y*ml`,
  `Dockerfile*`, `*.sln`, lockfiles; `Grep` for `scripts` blocks and CI `run:`
  steps; `Read` the instruction files (`CLAUDE.md`, `AGENTS.md`, `README.md`).
- **Status derivation** — apply the invalid-combination table in
  [references/verification-matrix.md](references/verification-matrix.md) by hand,
  and state that you did so.
- **Gate execution** — you cannot run the project's gates. Every check whose
  evidence would have come from an executed run is `NOT RUN`, not `PASS`.
  This is the honest outcome, not a failure of the skill.

Never silently upgrade a check because you could not execute it. A surface
without a shell produces `NOT RUN` and a report that says why; that report is
more useful than a fabricated `PASS`.

## What this skill does

| Action | Scope |
|---|---|
| **Discover** | Locate repo root, instructions, commands, CI, and optional infrastructure |
| **Contract** | Turn the request into acceptance criteria and a layer applicability table |
| **Inspect** | Find analogous slices, existing contracts, and false-green hazards |
| **Implement** | Build the smallest end-to-end slice through applicable layers |
| **Verify** | Run the project's real gates and record provenance per result |
| **Report** | Emit a completion report with an explicit, derived status |
| **Hand off** | Produce a portable handoff and, only when justified, a next slice |

## When to use

- A request names a feature, module, endpoint, UI flow, migration, or bounded context
- The user asks whether something is "done" or "100% complete"
- A change must reach every layer the project has, not just the code layer
- Prior work reported success but the user wants that claim checked

## When not to use

- A one-file change with an obvious test — just make it and run the test
- Pure exploration or planning with no implementation requested — use a planning skill
- The user only wants a review of existing code — use a review skill

## Invocation

```
skill-admin:force-complete-slice "add password reset: request, e-mail token, confirm, audit"
skill-admin:force-complete-slice "finish the invoice export slice in this repo"
skill-admin:force-complete-slice "verify whether the payments slice is actually complete"
```

Arguments: the slice description first, then optional `--repo <path>` and
`--dry-run` (discovery + contract only, no writes).

## Procedure

### Step 1 — Discover project context (read-only)

Determine the repository root, then run:

```
uv run skills/force-complete-slice/scripts/discover_gates.py <root> --json
```

The script is project-agnostic and read-only. If it cannot run, discover by
hand with `Read`/`Glob` and say the script was unavailable — do not pretend it
ran. Record what it found and, equally, what it could not find.

Read, in this order, whatever exists: project instructions (`CLAUDE.md`,
`AGENTS.md`, `.cursor/rules`, `.windsurf`), `README`, `CONTRIBUTING`, any
definition-of-done document, the build manifest, test configuration, and CI
workflow files. Project instructions override this skill's defaults.

Classify the requested unit: module, feature, vertical slice, bounded context,
endpoint, UI flow, migration, or other. Say which, and why.

### Step 2 — Define the completion contract

Convert the request into numbered acceptance criteria that can each be marked
verified or not. Then fill the layer table from
[references/completion-contract.md](references/completion-contract.md): every
layer is either **applicable** or **not applicable with a stated reason**. A
layer may not be left blank.

Surface, before any code, the infrastructure and topology assumptions the
contract depends on (single node vs cluster, real database vs substitute,
browser vs API-only). These become named gates later; they are not footnotes.

If the contract cannot be written without guessing product intent, stop and ask.
An invented acceptance criterion produces a false completion.

### Step 3 — Inspect before editing

Find the closest analogous slice in the repository and follow its shape —
contracts, routes, handlers, repositories, migrations, components, tests, docs.
Preserving the project's existing pattern outranks introducing a cleaner one.

Before trusting any existing green result, scan for the false-green hazards
listed in [references/verification-matrix.md](references/verification-matrix.md):
skips, `xfail`, conditional test gates, in-memory fakes standing in for real
adapters, feature flags defaulting off, placeholder returns, and TODO bodies.

### Step 4 — Implement the smallest complete slice

Build end-to-end through every applicable layer. Keep the boundaries the
project already has. Preserve authorization, validation, transactional,
audit, and error-handling behavior rather than re-deriving it.

Add or update tests at the layer where each criterion actually lives. Add the
documentation or contract changes the project requires. Do not bundle unrelated
refactors — note them instead.

Every write to the target project follows that project's own instructions and
the user's request. Nothing is committed, pushed, opened as a PR, deployed, or
run against production here.

### Step 5 — Verify with evidence

Run the project's real commands: build, typecheck, lint, unit, integration,
acceptance, browser, security, migration, and docs checks, limited to the
gates that apply. For each result record the command, the exit status, the
relevant output, and its provenance — `executed`, `ci`, `working-tree`,
`head`, or `inferred`.

Verify failure paths, not only success. Where an authorization boundary moved,
verify denial and fail-closed behavior. Where persistence or migration changed,
verify rollback and idempotency. Where UI behavior changed, verify it with the
method the project actually supports; if none exists, that gate is `NOT RUN`.

### Step 6 — Enforce honest status

When a check does not pass, do not stop and do not lower the bar. Work the
escalation ladder in
[references/escalation-and-persistence.md](references/escalation-and-persistence.md):

1. Re-read the local evidence — the missed file is the usual culprit
2. Check installed skills, plugins, and agents for an existing capability
3. Run the gate and read the **full** error, not the last line
4. Research externally through whatever connectors or MCP tools are present
5. Reduce to a minimal reproduction
6. **Delegate to a subagent on the strongest model for an independent verdict**
7. Change the approach — never the criterion

When blocked, delegation is the rung most often skipped and most often
decisive, because you are the least reliable judge of your own dead end. Give
the delegate the raw evidence and ask it to attack your hypothesis; withhold
your conclusion when you want a genuinely independent read. A subagent's verdict
is a strong hypothesis, not evidence — execute it and record what happened.

Persistence is bounded by the evidence bar, not by effort. You may change the
implementation freely; you may never change what counts as proof. After the
effort budget for a check is spent, report `BLOCKED` or `PARTIAL` with the
trail of what each avenue ruled out.

Aggregate per-check results with:

```
uv run skills/force-complete-slice/scripts/completion_status.py --input results.json --json
```

The script applies the status rules deterministically and refuses to return
`PASS` for an unexecuted or inferred result. Read the rules in
[references/verification-matrix.md](references/verification-matrix.md). The
core rule is that "all applicable checks passed" and "all intended product
coverage exists" are two different claims and must be reported separately.

### Step 7 — Review and simplify

Use the repository's review workflow if one exists; otherwise review the diff
yourself against the acceptance criteria. Look for bugs, regressions, missing
tests, security gaps, duplicated logic, dead code, and architecture drift.

Apply cleanup only when it preserves verified behavior, and re-run the gates it
touched. Do not manufacture findings or edits to make the review look active.
A clean review with no changes is a valid outcome.

### Step 8 — Report, hand off, and plan the next slice

Emit the completion report from
[references/report-and-handoff.md](references/report-and-handoff.md). If a
handoff skill exists in the installed plugin ecosystem, use it; otherwise emit
the portable handoff in that same reference file. Report the absence of any
integration you relied on instead of silently substituting.

Capture a durable learning only if the work produced a non-obvious, verified
lesson not already in the project's code or docs, and only through whatever
knowledge workflow the environment provides. If there is none, say so and move
on. Never write project-specific lessons into this repository.

Propose a next slice only when the user supplied enough product direction to
define one. Otherwise state that the next slice is undefined.

## Status semantics

| Status | Meaning |
|---|---|
| `PASS` | Executed and matched the acceptance criterion |
| `PARTIAL` | Some part is executed and correct; at least one aspect is unmet or unverified |
| `FAIL` | Executed and contradicted the acceptance criterion |
| `BLOCKED` | Cannot execute because a required dependency or environment is absent |
| `NOT RUN` | Applicable, but no execution happened — including zero discovered tests |
| `NOT APPLICABLE` | Out of scope, with a stated reason |

A skipped test is not a pass. An unavailable service is not a pass. A mock is
not evidence for a real integration requirement. A unit test is not evidence
for a browser, failover, or deployment requirement.

## Required vs optional integrations

| Integration | Need | Fallback when absent |
|---|---|---|
| Shell / `Bash` | Required to run gates | Report `NOT RUN` with reason; never infer success |
| Project instructions and commands | Required | Discover by inspection; report the gap |
| Review agent or command | Optional | Do the review directly against the criteria |
| Subagent delegation | Optional | Diagnose directly; record that no independent verdict was obtained |
| Browser runner | Optional | Use the project's own UI test command; else `NOT RUN` |
| CI CLI | Optional | Inspect the committed workflow; do not claim it ran |
| Research connectors (docs, search, fetch) | Optional | Use training knowledge as hypothesis and verify locally; name what was unavailable |
| Formal verification (Lean, TLA+, Alloy, Z3) | Optional | Test evidence only; do not claim a proof |
| Knowledge workflow | Optional | Report absence; skip the learning |
| Handoff skill | Optional | Emit the portable handoff template |

Optional integrations never block the slice, but their absence changes what you
can honestly claim. Never let a missing tool silently become a downgraded
standard — name it in the report.

## Guardrails

- Never write "100% complete" without defining it for this project and showing
  evidence for every applicable criterion.
- Never describe working-tree behavior as committed or CI behavior. Uncommitted
  changes are labeled working-tree-only.
- Never upgrade a status to satisfy the user. A worse but true status wins.
- Never end the loop by lowering the bar. Change the approach, escalate a rung,
  or report `BLOCKED` — but never relax what counts as proof.
- Never treat research, training memory, or a subagent's verdict as evidence.
  They are hypotheses and discovery; only execution is proof.
- Never bypass a safeguard — no `--no-verify`, no force push, no disabled test
  marker — to make a gate pass.
- Never commit, push, open a PR, publish, delete data, or alter production
  unless the user explicitly asks and the project's rules permit it.
- Stop at the contract if it would require inventing product intent.

## Escalation and persistence

The full doctrine lives in
[references/escalation-and-persistence.md](references/escalation-and-persistence.md).
The load-bearing points:

- **The effort is unbounded; the evidence bar is fixed.** You may try any number
  of avenues. You may not lower the bar to exit the loop.
- **A block is a hypothesis, not a verdict.** Work the ladder before concluding
  anything is impossible. Most blocks dissolve at the first rung on a second look.
- **Delegate on the strongest model when blocked.** A fresh agent that did not
  watch you fail is a better diagnostician than you are. Send raw evidence, ask
  it to attack your hypothesis, then verify its verdict by executing it.
- **Trying a different approach is persistence; lowering the bar is a shortcut.**
  Refactoring, rewriting, or redesigning a layer is legitimate. Declaring victory
  is not.
- **Stop for exactly three reasons** — verified, blocked on the user, or
  exhausted with a recorded trail. Exhausted is a valid outcome; a fabricated
  `PASS` is not.

## Error handling

| Error | Response |
|---|---|
| Repository root not found | Ask for the path; do not guess a parent directory |
| No test command discovered | Record `NOT RUN` and name what is missing |
| Test command runs zero tests | Record `NOT RUN`, never `PASS` |
| Required service unavailable | Record `BLOCKED` with the missing dependency named |
| Acceptance criterion ambiguous | Pause and ask before implementing |
| Contract layer left blank | Treat the contract as incomplete; do not proceed |

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Discovers and runs the project's own commands. |
| **Claude Desktop (Cowork)** | Full support. File-based discovery; shell-dependent gates degrade to `NOT RUN`. |
| **Claude Desktop (Code)** | Full support. Project-scoped plugins honored. |
| **3P CLI/Desktop** | Full support. Same boundary contract as the official surface. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add
`Write`/`Edit` only after explicit user confirmation — on every surface.
