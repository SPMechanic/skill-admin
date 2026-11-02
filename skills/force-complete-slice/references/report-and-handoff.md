# Report and Handoff

## Completion report

Write this at the end of every run. It is the deliverable; the code is evidence
for it.

```markdown
## Completion report — <slice>

**Requested slice**: <one sentence>
**Unit kind**: module | feature | vertical slice | bounded context | endpoint |
 UI flow | migration | other
**Repository root**: <path>
**Revision**: <commit sha, or "uncommitted working tree">
**Contract**: <path or "inline, below">

### Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| AC-1 | <criterion> | PASS | `<command>` exit 0, <n> tests |
| AC-2 | <criterion> | NOT RUN | no UI runner available |

### Applied layers

| Layer | Applicable | Status | Reason / evidence |
|---|---|---|---|
| domain | yes | PASS | <evidence> |
| deployment / operations | no | NOT APPLICABLE | <reason> |

### Commands executed

| # | Command | Exit | Result |
|---|---|---|---|
| 1 | `<command>` | 0 | <n> passed, <n> skipped |

### Not run, blocked, or unavailable

| Check | Status | Why | What unblocks it |
|---|---|---|---|
| <gate> | BLOCKED | <missing dependency> | <action> |

### Two claims

1. All applicable checks passed: **<yes / no>**
2. All intended product coverage exists: **<yes / no>** — <reason>

### Overall status

**<PASS | PARTIAL | FAIL | BLOCKED | NOT RUN>**

### Remaining risks and infrastructure gaps

- <risk, and what it would take to close>

### Files changed

| File | Change |
|---|---|

### Repository state

| Question | Answer |
|---|---|
| Committed? | no — working tree only |
| Pushed? | no |
| CI executed? | no |
| Handoff needed? | <yes/no and why> |

### Recommended next slice

<only if the user supplied enough product direction; otherwise "undefined —
awaiting product direction">
```

### Report rules

- The overall status is derived, never chosen. It comes from the per-check
  statuses by the rules in [verification-matrix.md](verification-matrix.md).
- Do not write "100% complete". Write the two claims and let the reader see the
  evidence behind each.
- Every row in "not run, blocked, or unavailable" names what would unblock it.
  A gap with no path forward is a decision for the user, and the report says so.
- Test counts appear only with the command that produced them. A count read from
  documentation is labeled `inferred`.
- Changed files are listed, not summarized as "various".

## Portable handoff

Use the installed handoff skill when one exists. Otherwise emit this. It must
read standalone, in a fresh session, with no access to the original chat.

```markdown
## Handoff — <slice>

**Repository**: <path>
**Revision**: <sha or "uncommitted working tree">
**Date**: <iso-8601>

### Current state

<what is true right now, in three sentences or fewer>

### Completed work

| Item | Evidence |
|---|---|

### Unresolved gaps

| Gap | Status | Unblocks with |
|---|---|---|

### Known limitations

- <constraint a successor would otherwise rediscover>

### Changed files

| File | Change |
|---|---|

### Commands run

| Command | Exit | Result |
|---|---|---|

### Exact next action

<one action, specific enough to start without asking a question>
```

## Next-slice planning

Propose a next slice only when all three hold:

1. The current slice has no `FAIL` or `BLOCKED` check affecting it.
2. The user described enough product direction to state acceptance criteria.
3. The proposed slice is independent of open decisions in the report.

Otherwise write "undefined — awaiting product direction" and list the open
questions. Inventing a slice to look productive is worse than an empty section,
because it converts an unanswered product question into unrequested work.

## Learning capture

Capture a learning only when the work produced a non-obvious, verified lesson
that is not already visible in the code, tests, or existing docs. Route it
through whatever knowledge workflow the environment offers; if there is none,
say so and continue.

Do not capture: routine implementation detail, anything the diff already says,
or project-specific content that belongs in the target repository rather than
here.
