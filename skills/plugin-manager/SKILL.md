---
name: plugin-manager
description: >
  Install, remove, upgrade, and enable/disable Claude Code plugins and marketplaces.
  Works on Claude Code CLI and Claude Desktop / Cowork Surface via direct file
  operations. Use when the user says "install this plugin", "remove X", "uninstall Y",
  "upgrade Z", "add a marketplace", "enable plugin X", "disable plugin Y", or
  "manage my plugins". This skill performs package manager operations safely and
  reports results. It does not audit, route, or repair plugins.
metadata:
  executor: true
---

# Plugin Manager

Performs install/remove/upgrade/enable/disable operations on Claude Code plugins
and marketplaces. **This skill executes; it does not audit or repair.** All
operations require explicit user confirmation.

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
| **Install** | Add a plugin from a marketplace, local path, or URL |
| **Remove** | Uninstall a plugin and remove its files |
| **Upgrade** | Update an installed plugin to the latest version |
| **Enable/Disable** | Toggle a plugin on/off without uninstalling |
| **Install from plan** | Execute a routing plan from `plugin-router` |
| **Verify** | Check that an operation succeeded |

## Inputs

| Input | Description |
|---|---|
| Plugin name or ID | e.g. `mattpocock/ts-reset` |
| Marketplace source | Marketplace name, local path, or git URL |
| Version (optional) | Specific version or latest |

## Operations

### List installed plugins

**CLI:**
```bash
claude plugin list
```

**Desktop / Cowork:**
Read `~/.claude/plugins/installed_plugins.json` — returns all plugins with `scope`, `version`, `installPath`, `gitCommitSha`, `installedAt`.

### List known marketplaces

**CLI:**
```bash
claude marketplace list
```

**Desktop / Cowork:**
Read `~/.claude/plugins/known_marketplaces.json` — returns marketplace names, git URLs, `installLocation`.

### Install

**CLI:**
```bash
claude plugin add <plugin-id>
```

**Desktop / Cowork:**
1. Read `~/.claude/plugins/known_marketplaces.json` → get marketplace `installLocation`
2. Read `<installLocation>/<plugin>/.claude-plugin/plugin.json` → get version + metadata
3. Copy plugin files to cache: `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`
4. Append entry to `~/.claude/plugins/installed_plugins.json` under key `"<plugin>@<marketplace>"`:
   ```json
   {
     "scope": "user",
     "installPath": "~/.claude/plugins/cache/<marketplace>/<plugin>/<version>",
     "version": "<version>",
     "gitCommitSha": "<sha>",
     "installedAt": "<ISO-8601>"
   }
   ```
5. Set `"<plugin>@<marketplace>": true` in `~/.claude/settings.json` → `enabledPlugins`

### Remove

**CLI:**
```bash
claude plugin remove <plugin-id>
```

**Desktop / Cowork:**
1. Remove entry from `~/.claude/plugins/installed_plugins.json`
2. Delete cache directory: `~/.claude/plugins/cache/<marketplace>/<plugin>/`
3. Set `"<plugin>@<marketplace>": false` in `~/.claude/settings.json` → `enabledPlugins` (keep key for audit)

### Upgrade

**CLI:**
```bash
claude plugin update <plugin-id>
```

**Desktop / Cowork:**
1. Run `git pull` in `~/.claude/plugins/marketplaces/<marketplace>/`
2. Copy updated plugin files to new version cache directory
3. Update `installed_plugins.json` entry with new `version`, `gitCommitSha`, `lastUpdated`

### Enable/Disable

**Desktop / Cowork:**
Edit `~/.claude/settings.json` → `enabledPlugins`:
- **Enable** — set `"<plugin-id>": true`
- **Disable** — set `"<plugin-id>": false` (files stay on disk; plugin is inactive)

**HITL gate (both enable and disable):** show the exact `enabledPlugins` diff
(`"id": false → true`) and **pause for explicit user confirmation before writing**.
Do not present the toggle as already done until the user confirms.

### Install from plan

Given a routing plan from `plugin-router` (markdown table or JSON):

1. Parse plan → extract marketplaces + plugins
2. For each marketplace: check `known_marketplaces.json`; if missing, append to `settings.json` → `extraKnownMarketplaces` with `source.source: "git"`, `source.url`
3. For each plugin: check `installed_plugins.json`; if missing, install via Desktop/Cowork path
4. For each installed-but-disabled plugin: set `enabledPlugins[id] = true`
5. HITL gate: ask user to confirm before each install/enable

**Required narration — every step above must appear in the user-visible response**
as it executes, in this order, so the user can follow the plan:
1. State you are checking `~/.claude/plugins/known_marketplaces.json` and report whether
   each marketplace is registered or missing.
2. For each missing marketplace, state you are registering it in
   `~/.claude/settings.json` → `extraKnownMarketplaces` (with the git source URL).
3. For each plugin, state you are installing it **via file operations** (Desktop/Cowork)
   or `claude plugin install` (CLI) — name the mechanism explicitly.
4. For each installed-but-disabled plugin, state you are enabling it via
   `settings.json` → `enabledPlugins`.
5. **Pause and ask the user to confirm before each install/enable** — present the
   pending actions and wait; do not report them as complete until confirmed.

## Safety rules

1. **Confirm destructive operations** — always ask before remove/upgrade
2. **Backup before upgrade** — warn user that rollback may not be possible
3. **Resolve by source priority** — official > community-proven > experimental
4. **Fail safe** — if a command fails, stop and report; do not retry blindly
5. **Write settings.json atomically** — write to temp file, then rename to avoid corruption

## Workflow

### Step 1 — Identify the operation

Determine if the user wants install, remove, upgrade, enable, disable, or install-from-plan.

### Step 2 — Locate the source

| Source type | How to find |
|---|---|
| Marketplace plugin | `skills/plugin-router/references/catalog.md` or `skills/plugin-router/references/marketplace-wishlist.md` |
| Local plugin | User-provided absolute or relative path |
| Git URL | User-provided URL |

### Step 3 — Validate compatibility

Check:
- Required Claude Code version
- Plugin dependencies
- Conflicts with installed plugins

If conflicts exist, ask the user which to keep.

### Step 4 — Execute

For CLI surface: run the command, capture output and exit code.
For Desktop/Cowork surface: perform file operations directly.

### Step 5 — Verify

After install:
- Confirm plugin appears in `installed_plugins.json` (Desktop/Cowork) or `claude plugin list` (CLI)
- Check plugin `plugin.json` is valid
- Suggest refreshing the catalog:

```bash
uv run skills/plugin-router/scripts/refresh_catalog.py
```

### Step 6 — Report

```markdown
## Plugin Manager Report

**Operation**: Install `plugin-id` from `marketplace`
**Result**: Success
**Installed at**: `~/.claude/plugins/...`
**Next steps**:
1. Refresh catalog: `uv run skills/plugin-router/scripts/refresh_catalog.py`
2. Run `marketplace-optimizer` to audit the updated stack
```

## What this skill does NOT do

- This skill does not audit or score plugins
- This skill does not repair broken plugins
- This skill does not route tasks to capabilities
- This skill does not modify AI steering files
- This skill does not write to `feedbacks/` (use `plugin-feedback` for that)

## Error handling

| Error | Response |
|---|---|
| Plugin not found | Suggest checking spelling or searching wishlist |
| Version conflict | Ask user which version to keep |
| Network failure | Report and retry once if user confirms |
| Post-install validation fails | Recommend `plugin-doctor` |
| settings.json corrupted | Recommend `plugin-doctor` to repair before proceeding |

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `claude plugin` commands. |
| **Claude Desktop (Cowork)** | Full support. File-based operations. Executor skills pause for confirmation before any write or install. |
| **Claude Desktop (Code)** | Full support. File-based operations. |
| **3P CLI/Desktop** | Same as official surface. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
