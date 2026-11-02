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
| **Hollow** | Presentation exists (mockup, UI shell, prototype) but no `acceptance.tsv` and no backend/contract surface behind it | **Design-first, never implement-first.** Queue into a contract wave (below) before any implementation wave. |
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

## Hollow slices and the contract wave

A **Hollow** slice is one where presentation exists but the domain does not —
a mockup, UI shell, or prototype with no `acceptance.tsv` and no backend
surface behind it. It is the most dangerous class to schedule naively: an
implement-first agent will wire the UI to *imagined* ports, and the module
lands out of sync with the architecture as a whole.

Hollow slices enter a **contract wave** that precedes any implementation wave
for them. A contract wave is design-only: define the slice's domain ownership,
required ports, events, and read models as *contracts* — what the dashboard
will need from `inpatient`, `scheduling`, `facility calendar` — and expose
every unresolved decision as an explicit `BLOCKED` item (metric formulas, bed
source) rather than filling it with a default. Design top-down; implement
bottom-up:

1. **Contract wave (top-down design).** For each Hollow slice, produce its
   contract: ports it requires, events it publishes/consumes, read models. In
   DDD terms this is the published language and its ACLs — defined before the
   lower modules that will eventually implement them, so those modules are
   built to satisfy the contract rather than the UI bending to whatever got
   built. No implementation, no scaffolding, no mock backends that pretend the
   port exists. Unresolved business decisions become `BLOCKED` rows owned by
   the user.
2. **Ladder reconciliation.** Trace the slice's declared dependencies and the
   compiled module graph; reconcile them. The first missing prerequisite on
   the ladder defines the readiness condition for the slice. Lower modules
   implement *toward* the contracts from step 1.
3. **Implementation waves (bottom-up build).** The usual DAG waves. The Hollow
   slice implements last, against ports that now exist.

Two rules bind every contract wave:

- **Guessing is a defect.** If a design agent fills an unresolved decision with
  a plausible default (a metric formula, an enum value, a bed-source shape),
  the contract is wrong even if the code compiles. The review of a contract
  wave checks for invented decisions the same way an implementation review
  checks for invented evidence.
- **Parallel design passes over the same slice are sequential on decision
  points.** Independent design agents may explore different surfaces (domain
  shape, backend contracts, API boundary) simultaneously, but whenever two
  passes would resolve the same decision, the passes must be merged or
  sequenced — two agents inventing the same enum independently is a conflict,
  not parallelism.

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
| Slice | Class | Wave | Model pair | Scheduled as | Evidence held |
|---|---|---|---|---|---|
| access | Partial (3 of 7 NOT RUN) | 1 | fast/standard | run | re-verified this run |
| student | Missing | 1 | strong/strong | blocked — user decision | none |
| lecturer | Missing | 1 | standard/strong | run | re-verified this run |
| dashboard | Blocked → re-classified | 2 | strong/strong | run | re-verified this run |
| billing | Complete (prior run) | — | — | skipped, PASS claimed | **not re-verified** |
```

A slice the stop condition turned away is recorded `blocked` with the user
question, not omitted — an absent row reads as "nothing was needed," which is a
false green at the plan level.

The column is `Scheduled as`, not `Result`, and there is no `PASS` cell. This
skill schedules; it never verifies. A slice whose prior artifacts read all-PASS
is recorded as **`skipped, PASS claimed`** with evidence held **`not
re-verified`**, keeping the two-currency rule visible in the report rather than
only in the prose above it. An imported PASS is a claim — the same rule
force-complete-slice applies — so a reader must not be able to mistake a
scheduling decision for evidence.

## What is checked by code and what stays prose

Force-complete-slice owns the scripts; this skill has one of its own, for the
rules that are pure file inspection:

```
uv run "$PLUGIN_ROOT/skills/skill-orchestrator/scripts/classify_slices.py" <root> [--slice NAME ...]
```

It classifies each slice from `.audit/<slice>/acceptance.tsv` — every row
`PASS` → Complete, any row not `PASS` → Partial, no directory → Missing — and
builds waves from inter-slice `depends_on` edges, where a cycle is an error and
the topological order is the wave order. Classification is where a scheduling
decision is most likely to be mistaken for evidence, so it is done mechanically.

Three judgments stay prose, in this document, read by a person:

- **Hollow classification before any run exists.** Presentation with no backend
  behind it can only be inferred from a repository shape, and a script that
  guessed would turn a provisional call into a green verdict. Mark it
  provisional until a run has produced a contract, at which point
  force-complete-slice's own `hollow_warning` carries the flag.
- **Decomposition quality.** Whether a slice is too fine, too coarse, or crosses
  a foundation boundary is a judgment about the user's intent that the
  artifacts do not contain.
- **The foundation boundary itself.** How deep the ladder may be resolved is a
  decision about the user's scope, not a property of the graph.

A checker for these would launder judgment into a green mark — the exact failure
this plugin exists to prevent. Adding one later is a regression, not an
improvement.
