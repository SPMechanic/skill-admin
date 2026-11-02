# Completion Contract

The contract is written **before** any edit. It is the only document that can
authorize the word "complete" later, so it must be checkable by someone who was
not in the session.

## Shape

```markdown
## Slice

<unit kind: module | feature | vertical slice | bounded context | endpoint |
 UI flow | migration | other — say which and why>

## Acceptance criteria

| # | Criterion | Verified by | Status |
|---|---|---|---|
| AC-1 | <observable behavior> | <gate id from discovery, or `manual: <procedure>`> | NOT RUN |
| AC-2 | <observable behavior> | <gate id from discovery> | NOT RUN |

A "gate id" is the id `discover_gates.py` emitted for that gate (for example
`npm:test`, `make:lint`, or the workflow job name). A criterion no discovered
gate can verify gets `manual: <procedure>` naming the exact steps and what a
pass looks like — never a bare description. If neither applies, the criterion is
not yet verifiable and the contract is not ready (see Step 2).

## Layer applicability

| Layer | Applicable | Reason |
|---|---|---|
| domain | | |
| application / use case | | |
| infrastructure / database | | |
| API / middleware | | |
| authentication / authorization | | |
| frontend / UI | | |
| integration | | |
| observability / audit | | |
| documentation | | |
| deployment / operations | | |

## Topology and infrastructure assumptions

| Assumption | Required by | If unavailable |
|---|---|---|
| <e.g. clustered database> | AC-<n> | BLOCKED, name it |
| <e.g. browser runner> | AC-<n> | NOT RUN, name it |

## Out of scope

- <explicitly excluded, with the reason>
```

## Rules

1. **Every criterion is observable.** "Implement password reset" is not a
   criterion. "A reset request for a known address returns 202 and writes one
   audit row; for an unknown address it returns 202 and writes none" is.
2. **Every layer row is filled.** Applicable, or not applicable with a reason.
   A blank row makes the contract invalid; do not proceed past it.
3. **Not applicable needs a reason the project would accept.** "No UI in this
   repository" is a reason. "We didn't get to it" is not.
4. **Topology assumptions are named, not implied.** A criterion that only means
   something on a multi-node deployment says so, and its gate is separate from
   the single-node gate.
5. **Out-of-scope items are written down.** Otherwise they silently become
   "unfinished" or, worse, silently become "done".
6. **Criteria come from the request and the project.** Never invent product
   behavior to make a contract fillable. If the request cannot produce a
   criterion, stop and ask.
7. **Imported criteria enter as `NOT RUN`.** Criteria taken from `--contract`,
   a prior audit document, or a recalled transcript carry their source in the
   criterion row and status `NOT RUN`. A prior `PASS` is a claim about a tree
   that no longer exists; Step 5 re-verifies it with a real gate run.

## Seeding from a prior audit

`--contract <path>` and `recall_audit.py` exist so a repeat audit does not pay
for the same discovery twice. Both are inputs to this step, never substitutes
for it.

| Source | What to carry | What to redo |
|---|---|---|
| `--contract <path>` | criteria text, layer rows, topology assumptions | status of every criterion |
| Recalled transcript | candidate criteria, prior statuses as claims | the criteria themselves, if the slice was re-scoped |
| Neither | — | derive from the request and the project |

Keep the source path in the contract. A criterion whose origin is unrecorded
cannot be audited later by someone who was not in the session.

Rules 1–5 still apply unchanged to imported criteria: an imported line that is
not observable gets rewritten, not accepted because a prior session wrote it.

## Layer prompt

For each layer, ask what "done" means *there*, and skip the layer only if the
answer is genuinely "nothing belongs here".

| Layer | Typical evidence |
|---|---|
| domain | invariant tests, value-object/aggregate behavior, no persistence leakage |
| application / use case | a use case or handler exercised through its public entry point |
| infrastructure / database | migration applied and reversed, constraints enforced by the real engine |
| API / middleware | status codes, contract shape, error envelope, auth middleware ordering |
| authentication / authorization | allow case **and** deny case, fail-closed on missing identity |
| frontend / UI | the flow driven the way a user drives it; empty, error, and slow states |
| integration | the real adapter against the real dependency, or an explicitly named substitute |
| observability / audit | the event is actually emitted, with the fields consumers rely on |
| documentation | the doc a maintainer would read reflects what shipped |
| deployment / operations | the artifact builds and starts under the project's own procedure |

## Scoping

The smallest complete slice is the one that satisfies the contract with no
applicable layer skipped. It is not the smallest diff. If a layer must be
deferred, move its criterion to out-of-scope with a reason and an owner — do not
leave a green gate standing in for it.
