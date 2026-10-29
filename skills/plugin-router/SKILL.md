---
name: plugin-router
description: >
  Route user requests to the correct plugin, skill, command, or agent from the
  installed marketplace catalog. Use when the user asks to perform a development
  task — writing code, reviewing, testing, debugging, planning, researching,
  designing, reverse-engineering, low-level programming, security work — and you
  need to decide which capability to invoke. Also use when the user asks "what
  skill should I use", "route this", "what marketplaces do I need". Provides
  deterministic routing tables and a parallel-split safety rubric. Works on
  Claude Code CLI and Claude Desktop (Cowork/Code) — reads installed plugin state
  from `~/.claude/plugins/installed_plugins.json` when CLI commands are unavailable.
metadata:
  executor: false
---

# Plugin Router

Deterministic routing for dev build-phase work. Reads the catalog in
`skills/plugin-router/references/catalog.md` and matches requests to capabilities using the routing
tables below.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `claude plugin list` for catalog refresh |
| Claude Desktop (Cowork) | Read `installed_plugins.json` directly |
| Claude Desktop (Code) | Read `installed_plugins.json` directly |
| 3P CLI/Desktop | Same as official surface |

## When to invoke

Activate plugin-router **only** for development work or explicit routing questions.

| User request type | What to do |
|---|---|
| Code, review, test, debug, plan, design, reverse-engineer, security work, low-level/systems programming | Use plugin-router tables |
| "what skill should I use", "route this", "what marketplaces do I need" | Use plugin-router tables |
| General conversation, chitchat, opinions, brainstorming that is not a specific dev task | Answer normally. Do NOT route. |
| "Give me a name for my startup" | Answer normally. Do NOT invoke plugin-router. |

If you are not sure whether to route, answer the user directly and optionally add
a brief note about which capability could help if they want to proceed as a dev task.

plugin-router is **not** for these task types — route them directly instead:

| Task type | Route to |
|---|---|
| Word / PDF / document conversion or merging | `docx`, `pdf` document skills |
| Spreadsheet manipulation | `xlsx` skill |
| Presentation generation | `pptx` skill |
| Image editing / conversion | image skills |
| General file I/O outside dev workflows | `Read`/`Write` tools directly |

When a request is clearly document work, do not walk the domain routing tables — just name the document skill and explain why it is outside plugin-router's scope.

## How to route

1. **Identify the domain and dev-lifecycle stage** (see §Domain Routing Tables).
2. **Match the request against the tables.** Prefer exact matches; fall back to
   keyword search in `skills/plugin-router/references/catalog-index.md` (or the
   full `catalog.md` for scripts).
3. **If no match**, state explicitly: "No matching capability in the current catalog."
   Then propose the closest alternative — or propose a marketplace to install from
   `skills/plugin-router/references/marketplace-wishlist.md`.
4. **Deduplicate**: if multiple marketplaces have the same capability, prefer
   `claude-plugins-official` > `anthropic-agent-skills` > community.
   Always mention this order when comparing or recommending multiple marketplaces.
   **Exception**: if the user's task needs a specific feature only available in a
   community plugin (e.g., a niche framework integration), say so explicitly and
   explain why you are deviating from the default preference order.
5. **Announce your route**: "Routing to `<plugin>:<skill>` because <reason>."
   The `because` clause must use one of the enumerated reasons shared with
   `skill-admin:intake`: `exact-table-match`, `keyword-fallback`,
   `catalog-gap-fallback`, or `user-specified`. Any other phrasing is invalid —
   this makes announcements diffable and testable.
6. **Human-in-the-loop gate**: before recommending any install, destructive action,
   or adversarial/exploit activity, pose an explicit y/n question and wait for the
   user's answer. Never proceed without approval.

### Alias / conflict rule

When two or more capabilities match the same trigger, emit **one** recommendation
and list the others as aliases with a one-line "prefer X when …" clause:

```
Routing to `plugin-a:capability` (aliases: `plugin-b:capability`, `plugin-c:capability`)
because exact-table-match. Prefer `plugin-a` when …; prefer `plugin-b` when …
```

Never emit N competing top-level recommendations for one intent — the reader should
get a single decision plus the disambiguating note. Aliases also count as coverage
for the drift-checker; a capability referenced only as an alias is still "covered".

### Wishlist / marketplace bootstrapping

When the user asks what marketplaces they need, or no installed capability matches
their domain, recommend marketplaces from `skills/plugin-router/references/marketplace-wishlist.md`.
Use the **Ranking engine** below and quote the dedup preference order explicitly.

Steps:
1. Identify project domains from the request or repo signals.
2. Read `skills/plugin-router/references/marketplace-wishlist.md` and rank relevant marketplaces by
   reputation and fit.
3. If appropriate, mention the helper script:
   ```
   uv run python skills/plugin-router/scripts/recommend.py "<space-separated domains>"
   ```
   You do not need to execute the script if it is unavailable, but you should
   reference it as the canonical way to get ranked recommendations.
4. Before any install or destructive action, pose an explicit y/n question.

## Ranking engine

When multiple capabilities match a request, first **identify project domains**
(e.g., "web-backend, python, web-frontend, typescript"), then score each
candidate:

| Signal | Weight | How to evaluate |
|---|---|---|
| Domain fit | 40% | Does the capability's description cover the task domain? |
| Reputation | 20% | Marketplace reputation from `skills/plugin-router/references/marketplace-wishlist.md` |
| Official | 10% | Anthropic-official capability (prefer over community) |
| Type fit | 15% | Skill > Command > Agent > Plugin |
| Specificity | 10% | Longer/more specific description = better match |
| Penalty: no overlap | -60% | If capability domains don't overlap with project domains, cap at 20 |

**Formula**: `score = domain_fit * 40 + rep * 0.2 + official * 10 + type * 15 + specificity * 10`, capped at 100.

Run the mechanical filter:
```
uv run python skills/plugin-router/scripts/recommend.py "<project requirement>"
```

Then pick the best-fit capability from the top 5 using semantic judgment.

## Workflows

For multi-step orchestration that spans skills, use the named workflows in
`workflows/` at the plugin root. The Workflow tool is the canonical way to run them.

| Workflow | Trigger phrase | What it does |
|---|---|---|
| `skill-admin.bootstrap-project` | "bootstrap this project", "set up this repo", "recommend skills for this codebase" | Runs project-atlas → marketplace-optimizer → plugin-router to produce a routing plan. |
| `skill-admin.marketplace-scout` | "find me a skill for X", "search external marketplaces for X", "what plugins can do X" | Searches skills.sh, GitHub, and skillsdirectory.com in parallel, scores results, then presents a ranked recommendation with a y/n install gate. |

These workflows are orchestration glue only — they do not replace single-turn routing tables. If the user's request fits one row in the Domain Routing Tables, route directly and do not spawn a workflow.

---

## Parallel split safety rubric

### Orchestration modes

| Mode | When to use |
|---|---|
| **Mode A — Sequential** | All 4 axes are "sequential" or any ambiguity exists. Default safe choice. |
| **Mode B — Parallel fan-out** | All 4 axes are "safe". Fan out multiple agents, then merge results. |
| **Mode C — Hybrid** | Some axes safe, some ambiguous. Parallelize the safe subset, keep ambiguous steps sequential. |

Before recommending parallel execution, score ALL four axes:

| Axis | Safe to parallelize | Must stay sequential |
|---|---|---|
| Shared files | Disjoint files | Same file/dir written |
| Shared state | Read-only / idempotent | Shared DB, config, globals mutated |
| Ordering deps | No output dependency | Step N+1 needs Step N's result |
| Destructive potential | Reversible / additive | Deletes, force-push, schema drops |

**Rule**: ALL 4 must be "safe" → Mode B. Any "sequential" → Mode A. Any
ambiguity → Mode C or A (safe default).

Always offer the user a choice between at least Mode B and Mode C before
recommending parallel execution. Never silently parallelize.

---

## Domain Routing Tables

### Core Software Development

| User says | Route to |
|---|---|
| "understand this codebase", "analyze this repo" | `analyze-codebase` or `Explore` agent |
| "brainstorm", "I have an idea" | `compound-engineering-plugin` brainstorm |
| "research X", "find docs", "library docs" | `deep-research` + Exa + Context7 |
| "create a plan", "break this down" | `feature-dev` or `Plan` agent |
| "build this feature", "implement X" | `feature-dev` or `full-stack-orchestration` |
| "scaffold", "boilerplate", "app starter" | `app-starter` |
| "write tests", "unit tests" | `unit-testing` or `tdd-workflows` |
| "TDD", "red green refactor" | `tdd-workflows` |
| "review this code", "check my PR" | `code-review` or `/code-review` |
| "simplify", "clean up" | `code-simplifier` or `/simplify` |
| "commit", "create PR" | `commit-commands` or `git-pr-workflows` |
| "deploy", "ship", "release" | `operating-kit` or `b2b-project-shipper` |

### Design & Visual Work

| User says | Route to |
|---|---|
| "design the UI", "visual direction", "make this look good" | `frontend-design` |
| "brand guidelines", "brand identity" | `brand-guardian` or `brand-guidelines` |
| "poster", "visual art", "canvas design" | `canvas-design` |
| "design system", "component library" | `frontend-design` + `web-artifacts-builder` |
| "color palette", "theme", "design tokens" | `frontend-design` + `web-artifacts-builder` |
| "Figma", "mockup", "wireframe" | `frontend-design` + `web-artifacts-builder` |
| "typography", "font pairing" | `frontend-design` |
| "chart", "data viz", "dashboard" | `web-artifacts-builder` or `xlsx` (if spreadsheet) |
| "redesign", "rebrand" | `frontend-design` + `brand-guardian` |
| "image generation" | `generate-image` or `algorithmic-art` |
| "dark mode", "responsive design" | `frontend-design` |

### Debugging & Diagnosis

| User says | Route to |
|---|---|
| "debug this", "find the bug", "why is it broken" | `bug-detective` or `debugging-toolkit` |
| "stack trace", "error message", "exception" | `debugging-toolkit` |
| "memory leak", "performance issue", "slow" | `debugging-toolkit` + `code-review --perf` |
| "race condition", "deadlock" | `architect` agent |
| "flaky test", "intermittent failure" | `tdd-workflows` + `debugging-toolkit` |
| "regression", "broke after change" | `code-review` (diff-focused) |
| "crash dump", "core dump" | `debugging-toolkit` or `analyze-codebase` |
| "profiling", "hot path", "bottleneck" | `code-review --perf` or `aws-cost-saver` |
| "trace this", "follow the flow" | `analyze-codebase` |

**Rule for this table**: Route to the closest match listed above. Do not invent
alternative capabilities that are not in the installed catalog.

### Reverse Engineering & Binary Analysis

| User says | Route to |
|---|---|
| "reverse engineer", "decompile", "unpack" | Install RE marketplace (see wishlist) |
| "understand this binary" | RE marketplace (ghidra/radare2 skills) |
| "analyze malware", "is this a virus" | Security marketplace + RE skills |
| "extract strings", "static analysis" | RE marketplace |
| "disassemble", "assembly code" | RE marketplace |
| "firmware analysis", "embedded firmware" | RE marketplace + `arm-cortex-expert` or `firmware-analyst` agent |
| "protocol analysis", "packet" | Security marketplace + `deep-research` |
| "obfuscated code", "deobfuscation" | RE marketplace |

> **Note**: Reverse-engineering capabilities are sparse in current marketplaces.
> Check `skills/plugin-router/references/marketplace-wishlist.md` for RE marketplace recommendations.

### Low-Level & Systems Programming

| User says | Route to |
|---|---|
| "C code", "C++", "Rust", "systems programming" | `code-review` + `commit-commands` |
| "kernel", "driver", "embedded C" | RE marketplace + security marketplace |
| "memory management", "allocator" | `architect` agent |
| "assembly", "inline asm", "SIMD" | RE marketplace |
| "compiler", "interpreter" | `analyze-codebase` + `architect` |
| "firmware", "device driver" | RE marketplace |
| "performance optimization" | `code-review --perf` + `architect` |
| "unsafe code", "FFI" | `architect` + `code-review` |

> **Note**: Low-level/systems capabilities are underrepresented. Check
> `skills/plugin-router/references/marketplace-wishlist.md` for low-level marketplace recommendations.

### Brownfield Discovery — inferring stack from files

When a repo has no `CLAUDE.md`, `AGENTS.md`, or `README`, infer the stack from
file signals and route accordingly:

| File signals | Likely stack | Route to |
|---|---|---|
| `*.py` + `requirements.txt` | Python (Flask/FastAPI/Django) | `analyze-codebase` or `feature-dev` |
| `*.py` + `pyproject.toml` | Modern Python (Poetry/PDM) | `analyze-codebase` or `feature-dev` |
| `package.json` + `*.ts`/`*.tsx` | TypeScript/Node.js | `analyze-codebase` or `frontend-design` |
| `go.mod` + `*.go` | Go | `analyze-codebase` or `gopls-lsp` |
| `Cargo.toml` + `*.rs` | Rust | `analyze-codebase` or `code-review` |
| `pom.xml` or `build.gradle` | Java/Kotlin | `analyze-codebase` or `java-pro` agent |
| `*.csproj` or `*.sln` | C#/.NET | `analyze-codebase` or `code-review` |
| `Gemfile` + `*.rb` | Ruby/Rails | `analyze-codebase` or `code-review` |

If no `CLAUDE.md` exists, suggest creating one once you understand the project.

### Security

| User says | Route to |
|---|---|
| "security review", "audit security" | `security-review` or `claude-security` |
| "pentest this" | Security marketplace (install first) |
| "OWASP", "SQL injection", "XSS" | `claude-security` + `attacker` |
| "secrets in code" | `claude-security` (secrets scan) |
| "supply chain", "dependency audit" | `claude-security` (supply chain gate) |
| "harden", "is this secure" | `attacker` (adversarial self-review) |
| "web security", "CSP" | `web-security-guard` |
| "compliance", "SOC 2", "GDPR" | `enterprise-security-reviewer` |
| "API security", "auth review" | `claude-security` + `attacker` |
| "malware analysis", "forensics" | Security marketplace + RE marketplace |
| "CTF", "exploit" | Security marketplace (ethical only) |
| "cloud security", "AWS security" | `aws-cost-saver` + `claude-security` |

---

## Catalog

The full inventory of installed plugins, skills, commands, and agents lives in
`skills/plugin-router/references/catalog.md`. Read it when:
- The routing tables don't cover the request.
- The user asks what capabilities exist.
- You need to check if a specific capability is installed.

To regenerate after installing/removing plugins:
```
uv run python skills/plugin-router/scripts/refresh_catalog.py
```

## Brownfield: steering files and project context

When working in an existing (brownfield) repo, always check for steering files
before routing. These files carry project-specific conventions and override
generic defaults.

### Steering file inventory

| File | Domain it covers |
|---|---|
| `CLAUDE.md` / `AGENTS.md` | Project-wide conventions, build/test commands, architecture notes |
| `SPEC.md` / `ENGINEERING.md` | Design intent, engineering standards, API contracts |
| `docs/ARCHITECTURE.md` | System design, module boundaries, data flow |
| `.cursor/rules` / `.windsurf/rules` | Editor-specific rules (same role as CLAUDE.md) |
| `README.md` / `README` | Project overview, setup instructions |

### Discovery protocol

1. **Scan for steering files** — check the repo root, `docs/`, and `.cursor/` / `.windsurf/` directories.
2. **Map each file to a domain** — e.g., SPEC.md → feature specs, ENGINEERING.md → code standards, ARCHITECTURE.md → system design.
3. **Route based on domains** — if a file covers frontend, route frontend tasks to the skills that file names. If it covers backend, route backend tasks accordingly.
4. **Identify gaps** — if a domain (e.g., backend, testing, deployment) is not covered by any steering file, note the gap and route based on code inference (file extensions, imports, directory names) instead.
5. **Suggest adding coverage** — recommend the user add steering files for uncovered domains.

### Conflict resolution

When two steering files give conflicting instructions:

1. **Identify the conflict explicitly** — name both files and the conflicting rules.
2. **Report the conflict to the user** — do not silently pick one source.
3. **Ask which source takes precedence** — wait for user input before proceeding.
4. **Record the resolution** — once resolved, apply that precedence consistently for the rest of the session.

### Non-standard / missing steering files

If the repo has no `CLAUDE.md`, `AGENTS.md`, or `README`:

- Do not treat this as a blocker. The code is still workable.
- State that project-specific instructions are absent.
- Offer to infer structure from the codebase itself (file names, imports, tests).
- Suggest creating a `CLAUDE.md` or `README` once the project is understood.

If the repo has steering files for some domains but not others:

- Route covered domains using those files.
- Route uncovered domains by inferring from code (extensions, imports, comments).
- Recommend adding steering files for the uncovered domains.

## Marketplace wishlist

When a user's project needs capabilities not in the current catalog, read
`skills/plugin-router/references/marketplace-wishlist.md` and recommend the closest matching
marketplaces to install.

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Load skill via `plugin.json`. Use `claude plugin` / `claude marketplace` commands. |
| **Claude Desktop (Cowork)** | Report-only skills run read-only. Executor skills pause for explicit user confirmation before any write or install. |
| **Claude Desktop (Code)** | Project-scoped plugins honored. Same boundary contract as CLI. |
| **3P Desktop (Cursor, Windsurf, etc.)** | Anthropic-compatible manifest. Steering-writer emits `.cursor/rules` and `.windsurf` files for these surfaces. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
