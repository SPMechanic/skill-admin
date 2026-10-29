---
name: project-atlas
description: >
  Generate a project atlas map that connects any project's AI-steering files
  (CLAUDE.md, AGENTS.md) and prompt context to a curated plugin/skill stack.
  Use when the user asks to "analyze my project", "what plugins do I need for
  this project", "set up my project for AI orchestration", "create a routing
  map", "what skills should I use for backend/testing/UI/security". This skill
  parses steering files, infers the tech stack, and maps dev phases to
  capabilities. It reports — it does not create or modify files.
executor: false
---

# Project Atlas

Generates a routing map connecting project context to the curated plugin/skill
stack. **This skill maps; it does not execute.** All installs, file writes, and
init phases require separate user approval.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `claude plugin list --json` for plugin discovery |
| Claude Desktop (Cowork) | Read `installed_plugins.json` + `settings.json` |
| Claude Desktop (Code) | Read `installed_plugins.json` + `settings.json` |
| 3P CLI/Desktop | Same as official surface |

## What this skill does

| Action | Scope |
|---|---|
| **Parse** | Read steering files and project manifests |
| **Infer** | Extract tech stack, frameworks, testing, deploy, security |
| **Map** | Connect each dev phase to specific capabilities |
| **Report** | Output gaps, conflicts, and a routing table |

## Inputs

| Input | Source |
|---|---|
| Steering files | `CLAUDE.md`, `AGENTS.md`, `.cursor/rules/`, `.windsurf/` |
| Project manifest | `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `*.csproj` |
| Installed catalog | `skills/plugin-router/references/catalog.md` |
| Installed plugins | `~/.claude/plugins/installed_plugins.json` (Desktop/Cowork) or `claude plugin list` (CLI) |
| Enabled plugins | `~/.claude/settings.json` → `enabledPlugins` (Desktop/Cowork) |

## Atlas map phases

For each dev phase, the atlas answers: **which plugin/skill/agent to trigger, and with what safety gates.**

| Phase | Trigger examples | Atlas output |
|---|---|---|
| Scope | "build feature X", "plan sprint" | Requirements → capability gap list |
| Plan | "design API", "architect module" | Architecture → routing to design/architecture plugins |
| Implement | "write endpoint", "create component" | Code gen → routing to language-specific skills |
| Test | "add tests", "coverage report" | Test strategy → routing to test plugins |
| Review | "review this PR", "check security" | Review checklist → routing to review/security plugins |
| Ship | "deploy", "release notes" | Ship steps → routing to deploy/CI plugins |
| Debug | "fix this bug", "trace error" | Debug strategy → routing to debugging plugins |
| Security | "audit dependencies", "pentest" | Security checklist → routing to security plugins |
| Pentest | "attack surface analysis" | Pentest plan → routing to pentest plugins |

## How to run

### Step 1 — Load project context

Read steering files in this order:
1. `CLAUDE.md`
2. `AGENTS.md`
3. `.cursor/rules/*.md`
4. `.windsurf/**/*.md`
5. Any `*.md` in project root matching `*steer*`, `*rule*`, `*guide*`

Extract:
- Declared tech stack (languages, frameworks, tools)
- Explicit rules (coding standards, naming conventions, patterns)
- Referenced capabilities (plugins, skills, MCP servers)

### Step 2 — Parse project manifest

| File | Signals |
|---|---|
| `package.json` | `dependencies`, `devDependencies`, `scripts` |
| `Cargo.toml` | `[dependencies]`, `[dev-dependencies]` |
| `pyproject.toml` | `[project.dependencies]`, `[tool.*]` |
| `go.mod` | `require`, `replace` |
| `*.csproj` | `<PackageReference>`, `<TargetFramework>` |

### Step 3 — Infer tech stack

Combine steering file declarations with manifest signals. If they conflict, trust the steering file (human intent overrides machine inference).

Output a structured stack:

```json
{
  "languages": ["typescript", "python"],
  "frameworks": ["nextjs", "fastapi"],
  "testing": ["vitest", "pytest"],
  "database": ["postgres"],
  "deploy": ["vercel"],
  "security_tools": ["snyk"]
}
```

### Step 4 — Read installed plugin state

**CLI surface:**
```bash
claude plugin list --json
```

**Desktop / Cowork surface:**
1. Read `~/.claude/plugins/installed_plugins.json` → all installed plugins with `scope`, `version`, `installPath`
2. Read `~/.claude/settings.json` → `enabledPlugins` map
3. Classify each plugin:
   - **Active**: `enabledPlugins[id] === true`
   - **Installed but disabled**: `enabledPlugins[id] === false` or key missing
   - **Unknown**: not in `installed_plugins.json` (flag as anomaly)

**Required narration:** whenever plugin state is part of the atlas output, state
explicitly that you read `~/.claude/plugins/installed_plugins.json` and
`~/.claude/settings.json` → `enabledPlugins`. Do not omit these filenames even
when the scenario is hypothetical.

### Step 5 — Map to capabilities

For each inferred technology, find matching capabilities in `skills/plugin-router/references/catalog.md`:

```
typescript → mattpocock (TS patterns), javascript-typescript (general)
fastapi  → backend-dev (API design), python-dev (language)
vitest   → frontend-testing (unit), test-runner (orchestration)
postgres → database-dev (schema), db-migrate (migrations)
```

Prefer Tier 1–2 plugins when duplicates exist (check `skills/plugin-router/references/marketplace-wishlist.md` for reputation scores).

**Filter by active state**: only plugins where `enabledPlugins[id] === true` are available. Installed-but-disabled plugins are flagged as gaps with enable instructions.

### Step 6 — Identify gaps and conflicts

- **Gap**: inferred technology has no matching *active* capability → flag for install or enable
- **Conflict**: two plugins claim the same capability → flag for dedup
- **Missing**: no capability for a required phase → flag as gap
- **Disabled**: capability exists but plugin is disabled → flag for enable (not install), recommend: "run plugin-manager enable <plugin-id>"

### Step 7 — Generate atlas map

Produce a routing table with a State column:

```
| Phase       | Capability          | Plugin                  | Skill              | Trigger                    | State  |
|-------------|---------------------|-------------------------|--------------------|----------------------------|--------|
| Scope       | requirements        | skill-admin             | plugin-router      | prompt analysis            | Active |
| Plan        | architecture        | anthropic-agent-skills  | plan-review        | manual or orchestration    | Active |
| Implement   | typescript-code     | mattpocock              | ts-patterns        | prompt or file watcher     | Active |
| Test        | unit-testing        | frontend-testing        | vitest-runner      | pre-commit hook            | [DISABLED — enable via plugin-manager] |
| Review      | code-review         | code-review-plugins     | pr-reviewer        | CI trigger                 | Active |
| Security    | dependency-audit    | claude-security         | dep-check          | scheduled scan             | Active |
| Pentest     | attack-surface      | [GAP — recommend: X]    | —                  | manual trigger             | Missing |
```

### Step 7 — Report to user

Present the atlas map with a summary:
- Total capabilities mapped
- Gaps found
- Conflicts found
- Installed-but-disabled plugins found (with enable instructions)
- Recommended next steps (route to `plugin-router` for execution)

## What this skill does NOT do

- This skill does not install or remove plugins
- This skill does not create or edit steering files
- This skill does not run init or setup phases
- This skill does not modify any files
- This skill does not change any configuration
- This skill does not write to `feedbacks/` (use `plugin-feedback` for that)

All actions from this report require separate user approval.


## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `claude plugin list --json` for plugin discovery. |
| **Claude Desktop (Cowork)** | Full support. File-based plugin discovery. Report-only — no writes. |
| **Claude Desktop (Code)** | Full support. File-based plugin discovery. Same boundary contract as CLI. |
| **3P CLI/Desktop (3rd-party gateway)** | Same as official surface. Anthropic-compatible manifest. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
