---
name: marketplace-bootstrapper
description: >
  Bootstrap a fresh Claude Code environment with recommended marketplaces,
  plugins, and configuration. Works on Claude Code CLI and Claude Desktop / Cowork
  Surface via direct file operations. Use when the user says "set up a new
  machine", "bootstrap my environment", "fresh install of Claude Code", "set up
  my dev machine", or "initialize my Claude environment". This skill installs
  marketplaces and configures settings. It does not audit existing plugins or
  route tasks.
metadata:
  executor: true
---

# Marketplace Bootstrapper

Sets up a fresh Claude Code environment with recommended marketplaces and
plugins. **This skill installs and configures; it does not audit or repair.**
All install operations require explicit user confirmation.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `claude plugin` / `claude marketplace` commands |
| Claude Desktop (Cowork) | Direct file operations on `~/.claude/` |
| Claude Desktop (Code) | Direct file operations on `~/.claude/` |
| 3P CLI/Desktop | Same as official surface |

## What this skill does

| Action | Scope |
|---|---|
| **Bootstrap** | Install recommended marketplaces on a fresh machine |
| **Configure** | Set up basic Claude Code settings |
| **Seed** | Install a starter set of plugins |
| **Verify** | Confirm the environment is ready |

## Bootstrap profiles

| Profile | Description | Installs |
|---|---|---|
| **minimal** | Just the essentials | claude-plugins-official, anthropic-agent-skills |
| **full** | Everything the curated stack recommends | All marketplaces in the wishlist |
| **custom** | User picks from a menu | User-selected marketplaces |

## Workflow

### Step 1 — Detect environment

| Check | Command |
|---|---|
| Claude Code installed? | `claude --version` |
| Existing marketplaces? | List `~/.claude/plugins/marketplaces/` |
| Existing config? | Check `~/.claude/settings.json` |

### Step 2 — Choose profile

Ask user: minimal, full, or custom?

### Step 3 — Read the wishlist

```
Read skills/plugin-router/references/marketplace-wishlist.md
```

Select marketplaces matching the profile.

### Step 4 — Present install plan

```markdown
## Bootstrap Plan

**Profile**: minimal
**Marketplaces to install**: 4

| # | Marketplace | Description | Plugins |
|---|---|---|---|
| 1 | claude-plugins-official | Official Anthropic plugins | 12 |
| 2 | anthropic-agent-skills | Official agent skills | 8 |
| 3 | awesome-claude-code-plugins | Community-proven utilities | 15 |
| 4 | langchain-ai-skills | LangChain ecosystem | 5 |

### After install
1. Refresh catalog: `uv run skills/plugin-router/scripts/refresh_catalog.py`
2. Run `project-atlas` to map your project
3. Run `marketplace-optimizer` to audit the stack
```

### Step 5 — Execute installs

Only after user confirms. For each marketplace:

**CLI:**
```bash
claude marketplace add <marketplace-name>
```

**Desktop / Cowork:**
1. Read `~/.claude/plugins/known_marketplaces.json` → check if marketplace exists
2. If missing:
   - Append to `~/.claude/settings.json` → `extraKnownMarketplaces`:
     ```json
     { "<name>": { "source": { "source": "git", "url": "<url>" } } }
     ```
   - `git clone <url> ~/.claude/plugins/marketplaces/<name>/`
   - Append to `~/.claude/plugins/known_marketplaces.json`: name, source, installLocation, lastUpdated (ISO-8601)

### Step 6 — Seed plugins

For minimal profile, install only core plugins. For full profile, install all.

**CLI:**
```bash
claude plugin add <plugin-id>
```

**Desktop / Cowork:**
Use plugin-manager install-from-plan pattern (read marketplace plugin.json → copy to cache → update installed_plugins.json → set enabledPlugins)

### Step 7 — Configure

Create or update `~/.claude/settings.json`:

```json
{
  "plugins": {
    "auto-load": true
  }
}
```

### Step 8 — Verify

**CLI:**
```bash
claude plugin list
claude marketplace list
```

**Desktop / Cowork:**
1. Read `~/.claude/plugins/installed_plugins.json` → confirm plugins present
2. Read `~/.claude/settings.json` → confirm `enabledPlugins` has keys
3. Read `~/.claude/plugins/known_marketplaces.json` → confirm marketplaces present

### Step 9 — Report

```markdown
## Bootstrap Report

**Profile**: minimal
**Marketplaces installed**: 4
**Plugins installed**: 35
**Config created**: yes

### Ready
Your Claude Code environment is set up. Next steps:
1. Refresh catalog: `uv run skills/plugin-router/scripts/refresh_catalog.py`
2. Run `project-atlas` to analyze your project
3. Run `marketplace-optimizer` to audit your plugin stack
```

## What this skill does NOT do

- This skill does not audit or score existing plugins
- This skill does not repair broken plugins
- This skill does not route tasks to capabilities
- This skill does not write project steering files

- This skill does not write to `feedbacks/` (use `plugin-feedback` for that)

## Error handling

| Error | Response |
|---|---|
| Claude Code not installed | Instruct user to install first (CLI only; Desktop/Cowork always available) |
| Marketplace already exists | Skip and note in report |
| Network failure | Report and retry once if user confirms |
| Partial install | List what succeeded, what failed |
| settings.json corrupted | Recommend `plugin-doctor` to repair before proceeding |

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `claude plugin` / `claude marketplace` commands. |
| **Claude Desktop (Cowork)** | Full support. File-based operations. Executor skills pause for confirmation before any write or install. |
| **Claude Desktop (Code)** | Full support. File-based operations. |
| **3P CLI/Desktop** | Same as official surface. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
