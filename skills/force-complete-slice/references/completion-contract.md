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
| AC-1 | <observable behavior> | <gate id or manual check> | NOT RUN |
| AC-2 | <observable behavior> | <gate id> | NOT RUN |

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
