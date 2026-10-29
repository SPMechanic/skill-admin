---
name: plugin-doctor
description: >
  Diagnose and repair broken Claude Code plugins, stale manifests, orphaned skills,
  and invalid plugin.json files. Use when the user says "fix my plugins", "this
  plugin is broken", "repair my setup", "diagnose plugin errors", or a plugin
  fails to load. This skill finds and fixes problems. It does not install new
  plugins or audit the stack.
executor: true
---

# Plugin Doctor

Diagnoses and repairs broken Claude Code plugins and marketplaces. **This skill
executes repairs; it does not audit or install.** All repairs require explicit
user confirmation before execution.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `claude plugin list` for verification |
| Claude Desktop (Cowork) | File-level checks on `~/.claude/` |
| Claude Desktop (Code) | File-level checks on `~/.claude/` |
| 3P CLI/Desktop | Same as official surface |

## What this skill does

| Action | Scope |
|---|---|
| **Diagnose** | Scan plugins for broken entrypoints, invalid JSON, missing files |
| **Repair** | Fix identified problems with minimal changes |
| **Verify** | Confirm the plugin loads correctly after repair |

## Common problems detected

| Problem | Symptoms | Repair approach |
|---|---|---|
| Invalid `plugin.json` | Plugin won't load, JSON parse error | Fix syntax, add missing required fields |
| Missing `SKILL.md` | Skill not triggered, empty description | Restore from backup or template |
| Orphaned skill | Skill in plugin but not listed in `skills` array | Add to plugin.json `skills` |
| Stale manifest | Plugin metadata out of sync with files | Regenerate plugin.json from disk |
| Broken entrypoint | Plugin fails to load entrypoint | Fix path or restore file |
| Wrong `entrypoint` field | Plugin loads but doesn't start | Correct the entrypoint path |
| settings.json corrupted | Claude fails to start, settings unreadable | Restore from `~/.claude/settings.json.backup` |

## How to run

### Step 1 — Scan

**Surface selection rule:** apply the Desktop/Cowork scan path whenever the
session has no Bash/shell access (Claude Desktop, Cowork, 3P connectors) —
regardless of which surface name the user claims. Never run
`claude plugin list` on a surface without shell access.

**CLI:**
```bash
claude plugin list
```

**Desktop / Cowork:**
1. Read `~/.claude/plugins/installed_plugins.json` → get all installed plugins
   and their `installPath`. **State explicitly in your response that you are
   reading this file.**
2. Read `~/.claude/settings.json` → `enabledPlugins` → map each plugin id to
   its enabled/disabled state. **State explicitly in your response that you are
   reading this file.**

For each plugin, verify:
1. `plugin.json` exists at `<installPath>/.claude-plugin/plugin.json` and parses as valid JSON
2. `plugin.json` has required fields: `name`, `version`, `description`, `author`, `license`, `keywords`, `category`, `required_version`
3. Every path in `skills` array exists on disk
4. Every `SKILL.md` has valid frontmatter (`name`, `description`)
5. Entrypoint file exists if specified
6. For Desktop/Cowork: `~/.claude/settings.json` → `enabledPlugins` has a key for this plugin

Also check — and state the outcome of each check in your response, with the filename:
- `~/.claude/settings.json` parses as valid JSON → if it fails, say **"settings.json corruption detected"**
- `~/.claude/plugins/known_marketplaces.json` parses as valid JSON
- `~/.claude/plugins/installed_plugins.json` parses as valid JSON

When `settings.json` corruption is detected, the **diagnosis report itself is
read-only and does not require confirmation** — proceed to restore and verify
within the same response. State that you are restoring from
`~/.claude/settings.json.backup`, report the **restoration result** (restored /
backup missing / restore failed), and list, per plugin, whether the restored
file's `enabledPlugins` map has a key for it — naming the plugins that have keys.

### Step 2 — Report findings

```markdown
## Plugin Doctor Report

**Plugins scanned**: 15
**Healthy**: 12
**Issues found**: 3

### Issues

| Plugin | Problem | Severity | Repairable |
|---|---|---|---|
| my-plugin | Missing description field | High | Yes |
| stale-tool | plugin.json out of sync with disk | Medium | Yes |
| broken-helper | SKILL.md missing | Critical | Partial (need template) |

### Recommended repairs

1. Fix `my-plugin/plugin.json` — add `description` field
2. Regenerate `stale-tool/plugin.json` from disk scan
3. Create `broken-helper/skills/SKILL.md` from template
```

### Step 3 — Repair

Only after user confirms. For each repair:

1. Read the broken file
2. Apply the minimal fix
3. Write the corrected file
4. Verify the fix

### Step 4 — Verify

**CLI:**
```bash
claude plugin list
```

**Desktop / Cowork:**
1. Re-read `~/.claude/plugins/installed_plugins.json` → confirm all plugins still present
2. Re-read `~/.claude/settings.json` → confirm all repaired plugins have `enabledPlugins` keys
3. Re-read repaired `plugin.json` files → confirm valid JSON

**Final report must list, per plugin: which plugins had `enabledPlugins` keys
in `settings.json` (enabled/disabled) and which had none (never enabled).**
Also state which repaired plugins were re-keyed into `enabledPlugins`.

Confirm all previously broken plugins now load.

## Repair templates

### plugin.json template

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Short description",
  "author": "Author Name",
  "license": "MIT",
  "keywords": ["claude", "plugin"],
  "category": "dev-tools",
  "required_version": ">=1.0.0",
  "skills": ["./skills/SKILL.md"]
}
```

### SKILL.md template

```markdown
---
name: skill-name
description: |-
  One-line description of what this skill does.
---

# Skill Name

Instructions for the skill.
```

## What this skill does NOT do

- This skill does not install new plugins
- This skill does not audit or score plugins
- This skill does not remove plugins
- This skill does not modify plugin logic or behavior
- This skill does not write to `feedbacks/` (use `plugin-feedback` for that)

## Error handling

| Error | Response |
|---|---|
| Cannot determine plugin root | Ask user for path |
| plugin.json unparseable | Restore from backup if available, else use template |
| SKILL.md missing | Offer to create from template |
| Repair fails | Report error, suggest manual fix |
| settings.json corrupted | Restore from `~/.claude/settings.json.backup` if present |

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `claude plugin list` for verification. |
| **Claude Desktop (Cowork)** | Full support. File-level checks. Executor skills pause for explicit user confirmation before any write or repair. |
| **Claude Desktop (Code)** | Full support. File-level checks. Same boundary contract as CLI. |
| **3P CLI/Desktop (3rd-party gateway)** | Same as official surface. Anthropic-compatible manifest. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
