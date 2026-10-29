---
name: marketplace-optimizer
description: >
  Audit and score your installed Claude Code plugins and marketplaces across all
  surfaces (Claude Code CLI, Claude Desktop Cowork/Code, and 3P gateway
  variants). Use when the user asks to "optimize my marketplace", "check my
  plugins", "which plugins should I keep/remove", "rate my plugins", "clean up
  my marketplaces", or wants a health report on installed capabilities. This
  skill scores every installed plugin against a deterministic reputation rubric
  (official > community-proven > experimental), detects overlaps and gaps,
  estimates per-plugin token cost, and produces a prioritized
  install/remove/disable/upgrade report. It reports — it does not modify,
  install, remove, or reconfigure.
executor: false
---

# Marketplace Optimizer

Audits your installed plugin stack. **This skill reports; it does not execute.**
All install, remove, upgrade, and configuration changes require separate user
approval through the normal HITL gates.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `claude plugin list --json` for plugin inventory |
| Claude Desktop (Cowork) | Read `~/.claude/plugins/installed_plugins.json` + `~/.claude/settings.json` directly |
| Claude Desktop (Code) | Read `~/.claude/plugins/installed_plugins.json` + `~/.claude/settings.json` directly |
| 3P CLI/Desktop (3rd-party gateway) | Same as the matching official surface |

## What this skill does

| Action | Scope |
|---|---|
| **Audit** | Inspect installed marketplaces, plugins, skills, commands, agents |
| **Grade** | Score every capability 0–100 using the reputation rubric |
| **Detect** | Find overlaps, duplicates, and gaps in dev-lifecycle coverage |
| **Report** | Output a prioritized install / remove / upgrade / keep action list |

## Inputs

| Input | Source |
|---|---|
| Installed catalog | `skills/plugin-router/references/catalog.md` (auto-generated) |
| Marketplace wishlist | `skills/plugin-router/references/marketplace-wishlist.md` |

## Audit dimensions

### 1. Reputation scoring

Score each plugin 0–100:

| Signal | Weight | Source |
|---|---|---|
| Official Anthropic | 40 | `claude-plugins-official` marketplace |
| Community proven | 30 | High adoption, active maintenance, good docs |
| Specificity | 20 | Clear trigger conditions, narrow domain focus |
| Non-overlap | 10 | Unique capability not duplicated elsewhere |

**Reputation tiers:**
- **Tier 1 (80–100)**: Official, well-maintained, high specificity
- **Tier 2 (60–79)**: Community-proven, good docs, active
- **Tier 3 (40–59)**: Experimental, niche, or poorly documented
- **Tier 4 (0–39)**: Stale, unmaintained, or redundant

### 2. Overlap detection

Flag when:
- Two skills have identical or near-identical trigger descriptions
- Two plugins cover the same domain with <20% differentiation
- A general-purpose skill duplicates a specialized one

### 3. Gap analysis

Check coverage across dev-lifecycle stages:
- Scope → Plan → Implement → Test → Review → Ship
- Missing stages = gaps

### 4. Staleness detection

- Last updated > 6 months ago
- No recent commits or releases
- Broken links or outdated dependencies

## How to run

### Step 1 — Load the catalog

```
Read skills/plugin-router/references/catalog.md
```

Parse into structured data: marketplace → plugin → skill/command/agent.

### Step 2 — Score each plugin

Apply the reputation rubric. For each plugin, output:
- Name, marketplace, tier, score
- Top 3 strengths
- Top 3 risks or gaps

### Step 3 — Detect overlaps

Cross-reference trigger descriptions. Flag pairs with >70% semantic overlap.

### Step 4 — Identify gaps

Map installed capabilities to dev-lifecycle stages. List uncovered stages.

### Step 5 — Produce recommendations

| Priority | Action | Rationale |
|---|---|---|
| P0 | Remove | Redundant or stale plugin |
| P1 | Install | Missing critical capability |
| P2 | Upgrade | Better alternative available |
| P3 | Keep | High-reputation, well-maintained |

### Step 5.5 — Token Cost Estimation

Estimate each active plugin's context-token footprint and flag bloated ones:

1. Read `~/.claude/plugins/installed_plugins.json` → for each active plugin (or run `claude plugin list --json` on CLI surface)
2. Read `<installPath>/.claude-plugin/plugin.json` → get `skills` array
3. For each skill, read the SKILL.md file → estimate token cost (`word count × 1.3` ≈ tokens)
4. Sum token costs per plugin
5. Flag plugins where:
   - Token cost > 5000 AND `lastUpdated` > 30 days ago → recommend **disable**
   - Token cost > 10000 AND `lastUpdated` > 7 days ago → recommend **disable or uninstall**
6. For flagged plugins, recommend **disable** (keep files on disk) vs **uninstall** (remove files) based on usage recency:
   - Used within 90 days → disable
   - Unused > 90 days → uninstall

Add flagged plugins to the recommendations table with priority P0/P1.

**The final report must include a dedicated "Bloat flags" section that names each
flagged plugin and quotes the exact numeric trigger it crossed** — e.g.:
"heavy-plugin: ~6,200 tokens, lastUpdated 45 days ago → crossed the
>5000-tokens + >30-days trigger → disable." This section is required even when
no plugins cross the thresholds — in that case state "No plugins crossed the
token bloat thresholds (5000+30d / 10000+7d)."

## Example output

```markdown
## Marketplace Health Report

**Overall Score**: 72/100 (Good, room for improvement)

### Executive Summary
Your plugin stack is healthy with 20 active plugins across 6 marketplaces.
Two overlaps and one gap detected. No critical issues.

### Tier Breakdown
- Tier 1 (80–100): 8 plugins — anthropic-agent-skills, claude-plugins-official, ...
- Tier 2 (60–79): 12 plugins — agent-sdk-dev, skill-creator, ...
- Tier 3 (40–59): 5 plugins — experimental-feature, niche-tool, ...
- Tier 4 (0–39): 2 plugins — stale-plugin, redundant-helper, ...

### Overlaps Detected
- `docx` (anthropic-agent-skills) overlaps with `document-generator` (community)
- `webapp-testing` overlaps with `playwright-tester` — keep one

### Gaps
- No coverage for "database schema migration"
- No "API documentation generation" capability

### Recommended Actions
1. **P0**: Remove `redundant-helper` — duplicates `claude-plugins-official` functionality
2. **P1**: Install `db-migrate` from `awesome-claude-code-plugins` — fills schema gap
3. **P2**: Upgrade `docx` to latest version — new features for table handling
4. **P3**: Keep `skill-creator` — high reputation, unique capability
```

## What this skill does NOT do

- This skill does not install or remove plugins
- This skill does not remove or disable capabilities
- This skill does not modify any files
- This skill does not change any configuration
- This skill does not write to `feedbacks/` (use `plugin-feedback` for that)

All actions from this report require separate user approval.

## Refresh the catalog

After installing/removing plugins, regenerate:

```bash
uv run skills/plugin-router/scripts/refresh_catalog.py
```

Then re-run the optimizer for updated results.

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `claude plugin list --json` for inventory when available; falls back to direct file reads. |
| **Claude Desktop (Cowork)** | Full support. File-based reads only — report-only, no writes. |
| **Claude Desktop (Code)** | Full support. File-based reads only — report-only, no writes. |
| **3P CLI/Desktop (3rd-party gateway)** | Full support. Same behavior as the matching official surface. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
