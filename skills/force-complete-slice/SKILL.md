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
| Claude Desktop (Code) | Same capabilities as Cowork, and the shell is normally available; fall back only if a `Bash` call actually fails |
| 3P CLI/Desktop | Same as the equivalent official surface |

Do not guess which surface you are on by name — test it. Attempt the `Bash` call;
if it is refused or unavailable, that run is a shell-less run and the fallback
applies. Assuming a shell exists wastes a run on a failed call; assuming it does
not exist silently downgrades every gate to `NOT RUN` and understates work that
was actually possible.

### When the shell is unavailable

Both scripts are conveniences, not the contract. On a surface without a shell,
do the same work with files and the rule table:

- **Discovery** — reproduce `discover_gates.py` by reading the repo directly:
  `Glob` for `package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`,
  `Makefile`, `.github/workflows/*`, `docker-compose.y*ml`, `Dockerfile*`,
  `*.sln`, `*.csproj`, `*.fsproj`, `*.vbproj`, `*.vcxproj`, and lockfiles;
  `Grep` for `scripts` blocks and CI `run:` steps; `Read` the instruction files
  (`CLAUDE.md`, `AGENTS.md`, `README.md`, `DEFINITION_OF_DONE.md`, `DOD.md`,
  `docs/ARCHITECTURE.md`).
- **Discovery warnings** — the script's `warnings` and `evidence_gaps` are the
  honesty mechanism, not decoration. Reproduce them yourself: call out a missing
  lockfile ("dependency state is unverifiable") and a missing instruction file
  ("ask the user for conventions") in the report. A by-hand run that drops these
  looks cleaner than a script run and is less true.
- **Status derivation** — the precedence rules are implemented in
  `completion_status.py`, not fully written out in the matrix. Apply this order
  by hand: any applicable `FAIL` → `FAIL`; else any `BLOCKED` → `BLOCKED`; else
  any `NOT RUN` → `NOT RUN`; else any `PARTIAL` → `PARTIAL`; else no passing
  check at all → `NOT APPLICABLE`; else all applicable `PASS` → `PASS`; else
  `PARTIAL`. Then apply the invalid-combination table in
  [references/verification-matrix.md](references/verification-matrix.md), and the
  coverage rule: a `PASS` with coverage not confirmed becomes `PARTIAL`. State
  that you derived it by hand.
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

Arguments: the slice description first, then optional `--repo <path>` (operate on
a repository other than the one you are in; pass it through to discovery and treat
it as the report's repository root), `--contract <path>` (seed Step 2 from an
existing audit or contract document instead of re-deriving criteria; see
[references/completion-contract.md](references/completion-contract.md)),
`--audit-dir <path>` (look for a prior contract in this directory instead of the
default `<root>/.audit/<slice>/`; see Step 2's precedence list),
`--override-effort "authorized by <user> at <time>"` (lift the attempt budget for
an explicitly authorized run; see
[references/escalation-and-persistence.md](references/escalation-and-persistence.md)),
and `--dry-run` (Steps 1–2 only: discovery, contract, and prior-evidence recall —
no writes and no implementation).

If the user asks to reuse audit work from a previous session ("we already audited
this", "use my earlier review"), run recall first — do not re-derive what a prior
session already established. Step 2 explains how.

`--dry-run` ends after Step 2 and reports the contract and the discovered gates,
with every criterion `NOT RUN`. It is the right mode when the user wants to know
*what completion would take* before agreeing to do it.

## Procedure

### Step 1 — Discover project context (read-only)

Determine the repository root, then run, from the plugin root (the scripts live
in this skill, not in the repository under inspection — substitute that path if
it differs, e.g. `${CLAUDE_PLUGIN_ROOT}`):

```
uv run "$PLUGIN_ROOT/skills/force-complete-slice/scripts/discover_gates.py" <root> --json
```

Pass `<root>` explicitly rather than changing directory, so gates are discovered
for the target repository while the script still resolves.

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

If `--contract <path>` was passed, or the user points at a prior audit, seed the
contract from that document instead of re-deriving it. Transcribe its criteria,
layers, and topology assumptions; fill only genuine gaps. Name the source path
in the contract so the report shows where the criteria came from.

**Auto-detected prior audits.** Before deriving criteria from scratch, check
whether a prior contract already exists for this slice, in this order of
precedence — the first that exists wins, and each later source is skipped:

1. `--contract <path>` — an explicit path always wins.
2. `<root>/.audit/<slice>/acceptance.tsv` — the convention this skill writes to
   and other tooling may already populate. `<slice>` is the slice slug: the
   kebab-case module/feature name, e.g. `.audit/student/acceptance.tsv`.
3. `<audit-dir>/acceptance.tsv` when `--audit-dir <path>` was passed — for
   repositories that keep audit artifacts somewhere else.
4. Nothing found — derive from scratch, and say in the report that no prior
   contract was found.

A detected `acceptance.tsv` is seeded exactly like an explicit `--contract`: its
`criterion`, `layer`, and `command` columns become criteria, and every row enters
`NOT RUN` for re-verification in this session (see the imported-findings rule
below — an imported `PASS` is a claim, never evidence). Name the detected path
in the contract. If the directory exists but the file does not, or the file is
present but has no parsable rows, say so and fall through to the next source —
a found-but-unusable audit is not evidence of anything.

A prior audit may also be **recalled from a previous session** when the user asks
for it. Transcripts live under `~/.claude/projects/<project-slug>/*.jsonl`:

```
uv run "$PLUGIN_ROOT/skills/force-complete-slice/scripts/recall_audit.py" \
  <root> --slice "<slice keywords>" --json
```

The script is read-only and extracts candidate `AC-*` criteria, statuses, and
evidence lines, ranked by recency and keyword overlap. It reads the local
transcript store only; it sends nothing anywhere.

**Imported findings are claims, not evidence.** Whatever a prior session or an
audit document asserts — including a `PASS` — enters the contract as a criterion
with status `NOT RUN` and a note naming its source. Step 5 re-verifies it with a
real gate run in this session. Never carry a prior `PASS` into the report, and
never let an imported criterion skip verification: a stale pass is the most
expensive false green there is, because it was once true.

Then convert the request into numbered acceptance criteria that can each be
marked verified or not. Fill the layer table from
[references/completion-contract.md](references/completion-contract.md): every
layer is either **applicable** or **not applicable with a stated reason**. A
layer may not be left blank.

Surface, before any code, the infrastructure and topology assumptions the
contract depends on (single node vs cluster, real database vs substitute,
browser vs API-only). Each becomes a check in `results.json` with
`requires_multinode`, `topology`, and `kind` set accordingly — an assumption that
is not a check cannot be verified and will silently become a false `PASS`.

If the contract cannot be written without guessing product intent, stop and ask.
An invented acceptance criterion produces a false completion. Asking is rung 9,
not rung 7: an independent subagent verdict settles whether a technical claim
holds, never what the product should do.

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
relevant output, and its provenance — `executed`, `ci`, `formal`, `working-tree`,
`head`, or `inferred`. These are the only accepted values; anything else is
downgraded to `PARTIAL`, because an unrecognised provenance is not a stronger
claim than `inferred`, it is an unexamined one.

Provenance is self-reported and no script can check it: a JSON file cannot prove
that a command ran. `completion_status.py` enforces only the traps it can see —
an unrecognised value, `inferred` claiming `PASS`, a formal proof with no stated
property, an empty or fully-skipped suite, a failing check reclassified as not
applicable. Honest labelling of `executed` remains yours, and it is the single
claim the whole report rests on. Likewise `all_coverage_exists` is an assertion
the script takes on trust; it is your judgement about the contract, not a
measured fact.

Verify failure paths, not only success. Where an authorization boundary moved,
verify denial and fail-closed behavior. Where persistence or migration changed,
verify rollback and idempotency. Where UI behavior changed, verify it with the
method the project actually supports; if none exists, that gate is `NOT RUN`.

### Step 6 — Enforce honest status

When a check does not pass, do not stop and do not lower the bar. Work the
escalation ladder in
[references/escalation-and-persistence.md](references/escalation-and-persistence.md):

1. Re-read the local evidence — the missed file is the usual culprit
2. Training knowledge, as a hypothesis to check — never as evidence
3. Check installed skills, plugins, and agents for an existing capability
4. Run the gate and read the **full** error, not the last line
5. Research externally through whatever connectors or MCP tools are present
6. Reduce to a minimal reproduction
7. **Delegate to a subagent on the strongest model for an independent verdict**
8. Change the approach — never the criterion
9. Ask the user — only for a decision no amount of research can settle

Record which rungs you used in the report. These nine rungs and their numbering
are identical to the ladder in the reference; cite the number from this list.

Rung 9 is a handoff, not an ending. If you ask and the answer does not come, the
criterion is `BLOCKED` with the question, the options, and your recommendation
recorded — never `NOT RUN`, because a person can still unblock it. An explicitly
authorized `--override-effort` run lifts the attempt budget and never the evidence
bar: an overridden run still cannot report `PASS` without a gate that executed.

When blocked, delegation is the rung most often skipped and most often
decisive, because you are the least reliable judge of your own dead end. Give
the delegate the raw evidence and ask it to attack your hypothesis; withhold
your conclusion when you want a genuinely independent read. A subagent's verdict
is a strong hypothesis, not evidence — execute it and record what happened.

Persistence is bounded by the evidence bar, not by effort. You may change the
implementation freely; you may never change what counts as proof. Climbing to
rung 8 and re-entering the ladder with a new approach is persistence. Reporting
`PASS` because the loop had to end is not. When all nine rungs are spent, that
criterion is `NOT RUN` with the escalation trail — reserve `BLOCKED` for a
question only the user can answer, and ask it (rung 9) before concluding you are
stuck.

Aggregate per-check results with:

```
uv run "$PLUGIN_ROOT/skills/force-complete-slice/scripts/completion_status.py" --input results.json --json
```

`results.json` holds one object per check. Only `id`, `status`, and `provenance`
are required; the rest are what make a status auditable, and omitting them
downgrades the result rather than escaping the rule:

| Field | Purpose |
|---|---|
| `id` | Criterion id from the contract (`AC-1`) |
| `status` | `pass`, `fail`, `partial`, `blocked`, `not_run`, `not_applicable` |
| `provenance` | `executed`, `ci`, `formal`, `working-tree`, `head`, `inferred` |
| `kind` | `test`, `build`, `lint`, `migration`, `browser`, `authorization`, `integration`, `deployment`, `ci`, `manual` |
| `tests_collected` | Integer. **Required for `kind: test`/`browser`/`integration`/`migration` claiming `pass`** — without it the empty-suite guard cannot run and the check drops to `PARTIAL` |
| `tests_skipped` | Integer. All skipped → `NOT RUN`; some skipped → `PARTIAL` |
| `evidence` | The observed output. A substitute marker (mock, stub, fake, in-memory, simulator) downgrades an integration/browser/deployment/migration pass |
| `requires_multinode` + `topology` | Topology claim; mismatch downgrades |
| `depends_on` | Ids that must not be `FAIL`/`BLOCKED` |
| `formal_property` | Required when `provenance` is `formal`: the proved statement, one readable sentence |
| `applies` + `reason` | `false` only with a stated reason, and never to erase a `FAIL` or `BLOCKED` |

Write the real evidence string. It is the only part of the report a reviewer can
audit, and the substitution rules read it — a vague `"tests passed"` is treated
as unexamined, not as a pass.

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
touched. **Then re-derive the overall status** — Step 7 can invalidate the status
Step 6 derived, and a report carrying a pre-review status is stale evidence.
Re-run the gates it touched, update `results.json`, and run
`completion_status.py` again so the numbers in Step 8 come from the code as it
now stands. Do not manufacture findings or edits to make the review look active.
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
| `BLOCKED` | Cannot execute because a required dependency or environment is absent, or because a rung-9 question awaits the user's answer |
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
| **Claude Desktop (Cowork)** | Full support with a known limit: shell-dependent gates degrade to `NOT RUN`. Honest `NOT RUN` is a supported outcome, not a degraded skill. |
| **Claude Desktop (Code)** | Full support. Project-scoped plugins honored; shell normally present. |
| **3P CLI/Desktop** | Supported up to the capabilities of the surface it runs on — same boundary contract, but verify shell access rather than assuming it. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add
`Write`/`Edit` only after explicit user confirmation — on every surface. The
confirmation is for the slice as agreed in Step 2, so obtain it there and record
that you have it; Step 4 proceeds on that basis rather than pausing again for
each file. A change outside the agreed contract needs a fresh confirmation.
