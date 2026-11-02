# Verification Matrix

Verification exists to produce evidence, not activity. Every check carries a
status and a provenance, and some combinations are invalid by construction.

## What the script enforces, and what it cannot

`completion_status.py` implements the mechanically checkable rows below:
provenance validity, `PASS` from `inferred`, empty and fully-skipped suites, an
unstated test count, the `formal_property` requirement, substitute markers in
evidence, a browser gate without browser evidence, xfail markers, topology, and
the refusal to demote a `FAIL` or `BLOCKED` into `NOT APPLICABLE`.

It cannot check honesty. Whether `executed` really ran, whether a mock is hidden
somewhere the evidence string does not mention, whether a migration's rollback
was genuinely exercised, whether a feature flag is off by default in the shipped
configuration — these are judgements the rows below require of *you*. Do not
treat a green script run as having applied them. When a row describes something
the script cannot see, apply it by reading the code and the configuration.

## Status

| Status | Use when |
|---|---|
| `PASS` | Executed, and the output matched the criterion |
| `PARTIAL` | Something ran and was correct, but at least one aspect of the criterion is unmet or unverified |
| `FAIL` | Executed, and the output contradicted the criterion |
| `BLOCKED` | Applicable, but a required dependency, service, credential, environment, or user decision is absent — including a rung-9 question that was asked and not yet answered |
| `NOT RUN` | Applicable, but nothing was executed — including a suite that discovered zero tests |
| `NOT APPLICABLE` | Out of scope for this slice, with a stated reason |

## Provenance

| Provenance | Meaning |
|---|---|
| `executed` | This session ran it and observed the result |
| `ci` | A CI run for this commit reported it |
| `formal` | A machine-checked proof establishes it (Lean, TLA+, Alloy, Z3); the proven statement must be quoted in plain language |
| `working-tree` | True of uncommitted local files only |
| `head` | True of the committed revision, not necessarily of the working tree |
| `inferred` | Read from source or documentation, not executed |

`formal` is the one provenance that can outrank test evidence, because a proved
invariant holds for every input rather than the ones a suite happened to try. It
is not stronger than the invariant being the *right* one: a proof of the wrong
property is worthless, so any `formal` result names the property it proved in
one sentence a reviewer can check.

Provenance is not a formality. Working-tree behavior, committed behavior, and
CI behavior are three different claims, and a report that conflates them is
wrong even when every individual statement is true.

## Invalid combinations

| Claim | Why it is invalid | Correct handling |
|---|---|---|
| `PASS` with provenance `inferred` | Nothing ran | `PARTIAL` |
| `PASS` with an unrecognised provenance value | Not a stronger claim than `inferred`, just an unchecked one | `PARTIAL` |
| `PASS` for a test gate with zero tests collected | An empty suite proves nothing | `NOT RUN` |
| `PASS` for a test gate with no `tests_collected` stated | The empty-suite rule cannot be applied | `PARTIAL` |
| `PASS` for a test gate where every collected test was skipped | No useful signal | `NOT RUN` |
| `PASS` for a test gate with some tests skipped | Weaker than an unqualified pass | `PARTIAL` |
| `FAIL` or `BLOCKED` re-marked `applies: false` | Erases the evidence a reader most needs | Keep `FAIL`/`BLOCKED`; a failure cannot be removed by asserting it does not apply |
| `PASS` for an integration criterion backed by a mock | The mock satisfies the mock | `PARTIAL`, name the substitute |
| `PASS` for a browser criterion backed by a unit test | Different failure surface | `NOT RUN` for the browser gate |
| `PASS` for a multi-node criterion backed by a single node | Different topology | `PARTIAL`, name the missing topology |
| `PASS` for a migration criterion with no reverse step exercised | Rollback unproven | `PARTIAL` |
| `PASS` while a required check is `BLOCKED` | A gate did not run | Overall `BLOCKED` |
| `PASS` reported as committed behavior when files are uncommitted | Provenance mismatch | Relabel `working-tree` |
| `PASS` for a CI gate from reading the workflow file | Reading is not running | `PARTIAL`, provenance `head` |
| `PASS` supported only by documentation, research, or a subagent's verdict | A promise or an opinion is not an observation | `PARTIAL`, provenance `inferred` |
| `PASS` with provenance `formal` where the proved property is unstated | An unreadable proof cannot be audited | State the property in plain language, or downgrade to `PARTIAL` |

## False-green hazards

Scan for these before trusting any pre-existing green result. They are the
usual reason a slice looks finished and is not.

| Hazard | Signal | Effect on status |
|---|---|---|
| Skipped tests | `skip`, `skipif`, `@Disabled`, `t.Skip` | Never counts as pass; count separately |
| Expected failure | `xfail`, `@ExpectedException`, quarantine markers | Never counts as pass |
| Conditional test gate | A test that returns early when an env var is unset | `PARTIAL` unless the gate ran |
| Fake or in-memory adapter | In-memory repository, fake clock, stubbed client | Insufficient for an integration criterion |
| Feature flag defaulting off | New path unreachable in the default configuration | `PARTIAL` — the shipped default does not include it |
| Placeholder body | `TODO`, `return null`, `throw new NotImplementedException` | `FAIL`, not `PASS` |
| Commented-out assertion | Assertions disabled to get green | `FAIL` |
| Test count in docs | A number with no artifact behind it | Label `inferred`; do not treat as CI evidence |
| Stale generated artifact | Committed output older than its input | Re-generate or report as stale |

## Two separate claims

Report these independently, in this order:

1. **All applicable checks passed?** Derived from the checks in the matrix.
2. **All intended product coverage exists?** A judgment about whether the
   contract's criteria are the right ones for the feature, answered yes or no
   with a reason.

A slice can honestly report **claim 1 = yes, claim 2 = no**. That is a
`PARTIAL`, and it is the most common truthful outcome. Collapsing the two into
one green word is the failure mode this skill exists to prevent.

## Execution order

Run cheap, fast, non-destructive gates first so a failure surfaces before an
expensive one wastes the session: build, then typecheck, then lint, then unit,
then integration, then acceptance, then browser, then security, then migration,
then docs. Stop the sequence at the first `FAIL` only if later gates depend on
it; otherwise record the failure and continue so the report is complete.

## Required coverage by changed area

Use as a prompt, not as a substitute for the project's own rules.

| Changed area | Minimum evidence |
|---|---|
| Domain logic | Unit tests through the public type |
| Persistence | Migration applied on the real engine, plus reversal |
| Public API | Contract test for success and at least one error shape |
| Authorization | Allow, deny, and missing-identity cases |
| UI | Project's own UI test, or `NOT RUN` naming the gap |
| Background work | At-least-once behavior, duplicate delivery, and crash mid-run |
| Configuration | Start with the new value absent, and with it wrong |
