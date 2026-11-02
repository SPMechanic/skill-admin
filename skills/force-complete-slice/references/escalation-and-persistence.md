# Escalation and Persistence

A slice is rarely stopped by something that is genuinely impossible. It is
stopped by the first obstacle that looks expensive. This file defines the
persistence doctrine: how hard to push, what order to try things in, which
shortcuts are forbidden, and how to stop without lying.

The doctrine has one non-negotiable shape:

**The effort is unbounded. The evidence bar is fixed.**

You may try any number of avenues. You may not lower the bar to exit the loop.
When those two rules conflict, the bar wins and the report says `BLOCKED`.

## The escalation ladder

Work top to bottom. Do not skip a rung because a lower one feels more exciting.
Record which rungs you used in the report.

| # | Rung | Cost | What it answers |
|---|---|---|---|
| 1 | **Re-read the local evidence** | Minutes | Most blocks are a missed file: an instruction doc, an existing analogous slice, a Makefile target, a CI step, a config default. Look again before escalating. |
| 2 | **Training knowledge, as hypothesis** | Free | Narrows the search and tells you what to look for. Never evidence. A memory of an API is a claim to verify, not a fact to assert. |
| 3 | **Installed skills, plugins, agents** | Low | The ecosystem may already contain the capability. Check what is installed before concluding a tool does not exist. |
| 4 | **Local execution** | Low–medium | Run the gate. Read the error. The error text is usually the answer. |
| 5 | **External research via connectors or MCP** | Medium | Upstream documentation, changelogs, issue trackers, reference implementations. See the tool table below. |
| 6 | **Construct a minimal reproduction** | Medium | Reduce the failure to the smallest failing case. A five-line repro beats a page of reasoning. |
| 7 | **Delegate for an independent verdict** | Medium–high | A fresh agent on the strongest model, given the problem and the evidence but not your diagnosis, tells you whether you are right and what it would do. |
| 8 | **Change approach, not standard** | High | A different design, library, or layer boundary that satisfies the same criterion. The criterion is fixed; the route is not. |
| 9 | **Ask the user** | Blocks | Only for a decision that no amount of research can settle — product intent, an unavailable credential, a scope call. |

Rungs 1–4 solve most problems. Reaching rung 5 is normal, not a failure.
Rung 7 is the one most often skipped and most often decisive. Reaching rung 9 is
legitimate but must be specific: name the decision, the options, and your
recommendation. "I am stuck" is not a question.

### Delegating for a verdict

When you are blocked, delegation is not politeness — it is the cheapest way to
break fixation, because you are the least reliable judge of your own dead end.
Delegate on the **strongest model available**, and give it the problem, not your
conclusion.

| Bad delegation | Good delegation |
|---|---|
| "I'm stuck on the migration test, can you help?" | "This migration test fails with `<full error>`. Here is the schema, the migration, and the test. Is the test wrong, the migration wrong, or the assertion wrong? Give a verdict and the smallest fix." |
| "Fix this for me." | "Independently diagnose this. Do not assume my approach is correct." |
| Sending your diagnosis as fact | Sending your diagnosis as *a hypothesis to attack* |

**Rules for delegation:**

- **Strongest model, for the verdict.** Diagnosis is high-stakes and
  irreversible; do not spend a fast model on it.
- **Withhold your conclusion when you want an independent read.** Handing over
  your answer gets it confirmed, not checked.
- **Parallelize genuinely independent questions.** Different hypotheses, or
  research versus diagnosis, run concurrently.
- **Send the raw evidence** — full error text, the failing input, the diff — not
  a summary that may have already lost the clue.
- **Verify the verdict.** A subagent's confident answer is `inferred` until you
  execute it. It is a strong hypothesis from a strong model, not evidence. Run
  what it proposes and record what actually happened.
- **Run the checking work here.** Delegation produces a verdict and a plan; the
  gate execution and the report stay with you.

If the delegated verdict contradicts yours, that is the point. Try theirs
before defending yours.

### Research tools

Capability first, product second. Prefer whichever tool the environment
actually provides; never assume one is installed.

| Capability | Typical tools | Use for | Does not establish |
|---|---|---|---|
| Version-accurate library docs | Context7 | Current API surface, deprecations, migration steps | That your code calls it correctly |
| Semantic and code search | Exa | Reference implementations, prior art, how others solved it | That the solution fits this repository |
| Live web and page fetch | TinyFish, web search, fetch | Release notes, issue threads, standards, vendor behavior | That the page is current or authoritative |
| Formal verification | Lean (Microsoft Research), TLA+, Alloy, Z3 | Proving an invariant or a state-machine property outright | Runtime behavior under real inputs |

**Research is discovery, not evidence.** A documentation page tells you what
the library promises; only execution tells you what your program does. Cite what
you learned and where it came from, then verify it locally. A `PASS` whose only
support is a documentation page is `PARTIAL` with provenance `inferred`.

Formal verification is the one exception that can outrank test evidence — see
`formal` provenance in the verification matrix. A proved invariant is stronger
than a thousand passing examples. It is not stronger than the invariant being
the wrong one, so state what was proved in plain language.

## Model pairing

Capability should follow difficulty. Running the strongest model on file listing
wastes budget; running a fast model on the completion contract produces a
confident wrong answer.

| Work | Model tier | Why |
|---|---|---|
| Breadth scan — locating files, finding analogous slices, grepping for hazards | Fast, cheap | High volume, low ambiguity, easy to verify |
| Gate execution and log triage | Fast, cheap | Mechanical; the exit code is the answer |
| Contract design, acceptance criteria, layer applicability | Strongest available | This is where an error poisons everything downstream |
| Architecture and cross-layer design decisions | Strongest available | Irreversible choices |
| Adversarial review of the evidence | Strongest available, ideally a *different* model than the one that did the work | A model reviewing its own work shares its blind spots |
| Second opinion when blocked | Strongest available, independent | Re-deriving from scratch breaks fixation on a wrong diagnosis |

Use the pairing the environment offers. When only one tier is available, do the
high-stakes steps first while attention is fresh, and say in the report that no
independent reviewer was used.

## Forbidden shortcuts

Each of these makes a slice *look* complete. All are defects, not optimizations.

| Shortcut | Why it is forbidden | What to do instead |
|---|---|---|
| Marking `PASS` to end the loop | Inverts the whole purpose of the skill | Report the true status; a true `PARTIAL` is a success of the skill |
| Swapping a real adapter for a fake to get green | The fake satisfies the fake | `PARTIAL`, naming the substitute |
| `skip`, `xfail`, quarantine, or a disabled test marker | Removes the evidence instead of producing it | Fix it, or report `NOT RUN` with the reason |
| Broad `except`/`catch` that swallows the failure | Converts a failure into silence | Handle the specific case or let it fail loudly |
| A test that asserts nothing | Inflates the count without evidence | Assert the behavior; an empty test is `FAIL` |
| Repeating a failed command unchanged | Burns time, produces nothing | Escalate a rung; change something each attempt |
| Deleting or weakening the assertion to match the bug | Makes the code the spec | Fix the code, or report the criterion as unmet |
| Citing a doc as proof of behavior | It is a promise, not an observation | `PARTIAL` with provenance `inferred` |
| Narrating progress as progress | Activity is not evidence | Only executed results change a status |
| Unbounded silent retry | Hides a systemic failure | Two attempts, then escalate and say so |

**The distinction that matters:** trying a different approach is persistence;
lowering the bar is a shortcut. Refactoring, rewriting, swapping libraries, and
redesigning a layer are all legitimate. Declaring victory is not.

## Termination

You stop for exactly three reasons. Each has a required report entry.

| Reason | Condition | Status it maps to | Report must contain |
|---|---|---|---|
| **Verified** | Every applicable criterion is `PASS` with real provenance | `PASS` | The evidence table |
| **Blocked on the user** | A decision, credential, or access only the user can supply | `BLOCKED` | The specific ask, the options, your recommendation, and what you already ruled out |
| **Exhausted** | The ladder was climbed at least once, each avenue recorded, and none resolved it — and rung 9 was either not reached or was answered | `NOT RUN` for that criterion (never `BLOCKED`, which implies an open user ask) | Every avenue tried, what each ruled out, and the narrowest remaining unknown |

`Exhausted` is a valid outcome and is **not** a failure. What is never valid is
reporting `PASS` because the loop had to end.

Map `Exhausted` to `NOT RUN` at the criterion level, not to `BLOCKED`. `BLOCKED`
means the next move belongs to the user; `Exhausted` means no such move exists,
and the next engineer must know the difference or they will wait on a decision
nobody is going to make. The one exception is an unanswered rung-9 question: a
move *does* exist there, it belongs to the user, and the criterion is `BLOCKED`
(see "Asked but unanswered" below), never `Exhausted`. If some criteria passed and one is exhausted, the report
carries `NOT RUN` for that criterion and the overall status follows from the
precedence rules — usually `NOT RUN` or `PARTIAL`, never `PASS`.

Before declaring `Exhausted`, confirm you actually climbed the ladder: did you
re-read the local docs, check installed capabilities, read the full error,
search externally, and delegate for an independent verdict at least once? Most
"impossible" blocks dissolve at rung 1 or rung 4 on the second look, and a
genuine dead end is rare once rung 7 is tried.

## Effort budget

The budget is on *attempts at one rung*, not on the escalation itself. Effort is
unbounded in the sense that running out of attempts never ends the work — it
moves you up the ladder. Climbing to rung 8 and re-entering at rung 4 with a new
approach is normal, not a second attempt at the same thing.

- **Simple check** — two attempts at the current rung, then escalate a rung.
- **Complex or flaky check** — three attempts, capturing the full output of each.
- **Research** — one focused pass per rung 5 tool; stop when the answer is
  established or the sources stop adding new information.
- **Same error twice** — stop. The approach is wrong, not the attempt count.
  That is a signal to go to rung 8, not to stop working.

When you have climbed all nine rungs and none resolved the check, report it as
`Exhausted` → `NOT RUN` with the escalation trail. `BLOCKED` is reserved for a
question only the user can answer; if you have not asked them, and the answer
would unblock you, go to rung 9 first. A recorded dead end is a real result; it
saves the next person the walk.

## Asked but unanswered (rung 9)

Rung 9 is a handoff, not a session end. If you asked the user and the answer did
not arrive — they stepped away, the turn ended, the session was resumed later —
the criterion is `BLOCKED`, with the question recorded verbatim. Never degrade
it to `Exhausted`/`NOT RUN`: that says nobody can unblock it, when in fact one
person can, and silence is not a verdict.

Record with every unanswered rung-9 criterion:

- the question, worded so it can be answered without re-reading the session
- the options, with your recommendation and why
- what you already ruled out, so the answer is not "try that again"
- what each answer unblocks, so a one-word reply is sufficient

An answered question resumes at the rung its answer points to. A resumed session
picks the criterion up from here; it does not re-ask what is already written down.

## Explicit effort override

The user may authorize more effort than the attempt budget above. Honor it — the
effort bound is theirs to spend — but it changes **one** thing.

| It changes | It never changes |
|---|---|
| The attempt budget, and the number of times you may re-enter the ladder at rung 8 | What counts as evidence for `PASS` |
| How many rungs you may climb on the same criterion | The status of a criterion with no executed gate |

Before starting an overridden run, state the cost and the limit once:

> Effort override accepted for AC-&lt;n&gt;. Attempts are unbounded for this run.
> This does not make unavailable evidence available: if the ladder is exhausted,
> the result stays `Exhausted` → `NOT RUN`, and if the block needs a decision, it
> stays `BLOCKED`. Estimated cost: &lt;attempts already spent, what each further
> round will run&gt;.

Then work, and record the override in the report with who authorized it and when.
An override never authorizes a `PASS` the gates did not produce — not after the
twentieth attempt, and not because the budget was explicitly unlimited. More
persistence finds more evidence; it never substitutes for it. If the user asks
for that substitution, it is not an override, and you say so plainly.

## Non-termination is a defect

Every run ends in exactly one of the Termination table's three states. A run
that stops without recording one — because a question went unanswered, because
the turn ended mid-ladder, because context ran out — has left the work in a state
nobody can resume. Before ending any run, write the current status of every
criterion and the next specific action. That sentence is the difference between a
handoff and an abandoned task.
