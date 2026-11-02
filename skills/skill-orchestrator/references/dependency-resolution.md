# Dependency resolution for slice fan-out

How the orchestrator turns "implement the dashboard module" into waves of
independent slices it can fan out safely. The resolver classifies and orders;
[force-complete-slice](../../force-complete-slice/SKILL.md) verifies. The
orchestrator may trust a prior `PASS` for *scheduling*; only the verification
skill may trust it for *evidence*. Those are different currencies — never
exchange them.

## Slice artifacts

A slice's state on disk is read from its audit artifacts, never inferred from
how the code looks. For a slice slug `<slice>`:

| Artifact | Meaning |
|---|---|
| `<root>/.audit/<slice>/acceptance.tsv` | The completion contract for that slice |
| `<root>/.audit/<slice>/status.json` | Last recorded state, written by the slice's controller |
| `baseline.json` `blocked: [...]` | Prerequisite slice slugs the controller recorded |

`status.json` states like `WAITING FOR DEPENDENCY` and `blocked` lists are
inputs to resolution, not problems to work around — another tool's state machine
is authoritative over this skill's guesses.

## Classification

For each slice the plan needs, classify from artifacts only:

| Class | Test | Consequence |
|---|---|---|
| **Complete** | `acceptance.tsv` exists and every row is `PASS` | Skip. Reuse; do not re-verify here. The verification skill re-verifies anything it imports for its own report. |
| **Partial** | `acceptance.tsv` exists with any row not `PASS` | Queue as *complete the slice* — never rebuild. The skill seeds from the existing contract. |
| **Missing** | No `acceptance.tsv` | Queue as a new slice; the skill derives a fresh contract. |
| **Blocked** | `status.json` or `baseline.json` lists unmet `blocked` prerequisites | Do not queue yet. The unmet prerequisites are queued first; this slice re-classifies when they complete. |

Fuzzy matching is forbidden: "is the student module implemented?" is not a
test. A slice is Complete only if its artifacts say so — otherwise a false
"completed" verdict gets scheduled on top of and poisons every wave after it.

## The stop condition

A request that decomposes into "rewrite the stack" has left the slice scale.
Apply two limits:

- **Depth budget**: default 3 — a slice's transitive prerequisites may be
  decomposed at most 3 levels below the request. The user can raise it; the
  orchestrator must state the budget before starting.
- **Foundation rule**: anything below the repo's existing foundation layer
  (build tooling, migrations framework, base platform module) is not decomposed.
  It is reported `BLOCKED` — on the user, not silently skipped. This mirrors the
  verification skill's rule that a missing user decision is `BLOCKED`, never
  quietly dropped.

If either limit trips, present the boundary to the user: "dashboard needs
access, student, lecturer; student needs person-registry; person-registry sits
below the foundation rule. Build the first wave and stop, or authorize deeper?"
Decomposition proceeds only on an answer.

## Waves

Build the DAG from the `blocked` lists and classification, then:

1. Topologically order. Ties (independent slices at the same depth) may share a
   wave.
2. Wave *n* starts only when every slice in waves < n is Complete or its
   contract is satisfied. A failed or `BLOCKED` slice freezes its dependents —
   they are reported `WAITING FOR DEPENDENCY`, matching the controller's own
   vocabulary.
3. Within a wave, apply the five-axis rubric below. Only slices that pass may
   fan out; the rest run sequentially in Mode C.

Cycles mean a plan error: report and stop (the existing error-handling row).

## The fifth rubric axis

The four-axis safety rubric in SKILL.md governs *how* parallel slices run. The
resolver adds the precondition that governs *which* slices may sit in one wave:

| # | Axis | Safe condition |
|---|---|---|
| 5 | Prerequisites | No two slices in the same wave share an unmet prerequisite, and no slice's prerequisite is being built in the same wave |

Axis 5 fails when two slices both need the mailer and neither wave has built
it — the exact failure where two agents each build their own version and the
merge costs more than serial work. Failing axis 5 demotes the wave to Mode C;
it does not cancel it.

## Fan-out and model pairing

Each slice in a wave runs as its own background agent, running
[force-complete-slice](../../force-complete-slice/SKILL.md) on that slice alone —
one agent, one slice, its own mirrored copy of the skill. The orchestrator picks
the model per slice before launch:

| Slice character | Model pair (worker / reviewer) | Rationale |
|---|---|---|
| Mechanical — migrations, CRUD scaffolding, schema plumbing from an existing contract | Fast worker, standard reviewer | The contract already decided the design; throughput is the constraint |
| Design-heavy — new module boundary, API shape, auth flows | Strong worker, strong reviewer | Both halves of the pair need judgment; a cheap reviewer is a rubber stamp |
| Verification-only — completing a Partial slice | Standard worker, strong reviewer | Re-verification is mechanical, but reading prior evidence is not |

State the pair per slice in the plan, so the report shows not just what ran but
on what. When the surface offers no model choice, fan out anyway and note that
pairing was unavailable — model selection is an optimization, not a gate.

## Reporting resolution

The orchestration report gains a resolution table:

```markdown
### Dependency resolution
| Slice | Class | Wave | Model pair | Result |
|---|---|---|---|---|
| access | Partial (3 of 7 NOT RUN) | 1 | fast/standard | PASS |
| student | Missing | 1 | strong/strong | BLOCKED — user decision |
| lecturer | Missing | 1 | standard/strong | PASS |
| dashboard | Blocked → re-classified | 2 | strong/strong | PASS |
```

A slice the stop condition turned away is reported `BLOCKED` with the user
question, not omitted — an absent row reads as "nothing was needed," which is a
false green at the plan level.
