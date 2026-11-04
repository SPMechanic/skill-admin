# skill-admin

Multi-surface plugin and skill administration. Works on Claude Code CLI and Claude Desktop / Cowork Surface. Each skill does one job — reports never execute, executors never audit.

## Install

```bash
# CLI
/plugin marketplace add SPMechanic/skill-admin
/plugin install skill-admin@skill-admin

# Desktop / Cowork — use plugin-manager skill directly
```

## Skills

| Skill | Type | Purpose |
|---|---|---|
| `intake` | Report-only | Step 0 intent articulation — converts raw prompts into a gated plan table before any routing |
| `project-atlas` | Report-only | Parse steering files, map capabilities, report gaps (including installed-but-disabled plugins) |
| `plugin-router` | Report-only | Routing tables, ranking engine, routing rubric — does not orchestrate |
| `marketplace-optimizer` | Report-only | Reputation scoring, gap analysis, token cost audit |
| `plugin-manager` | Executor | Install, remove, upgrade, enable/disable plugins — pauses for confirmation |
| `plugin-doctor` | Executor | Diagnose and repair broken plugins — pauses for confirmation |
| `plugin-feedback` | Executor | Capture routing misses and feedback — pauses for confirmation |
| `steering-writer` | Executor | Create/edit steering files — pauses for confirmation |
| `skill-orchestrator` | Executor | Sequence skills with safety gates — never routes or installs directly |
| `marketplace-bootstrapper` | Executor | Fresh-machine setup with curated install profiles |
| `force-complete-slice` | Executor | Drive one slice to an evidence-backed completion state — discovers the project's own gates, writes a completion contract, escalates through research and strong-model delegation when blocked, reports `PASS` / `PARTIAL` / `BLOCKED` / `NOT RUN` with provenance |
| `run-report` | Report-only | Render the activity ledger as a run report — per-session text tree or interactive HTML with durations, exit codes, and drill-down into each command |

## Surface compatibility

See [docs/surfaces.md](docs/surfaces.md) for the full multi-surface execution path matrix.

## Activity ledger

The plugin ships a PostToolUse/PreToolUse hook pair that records every
`skills/*/scripts/` invocation to `<project>/.audit/activity.jsonl` — one
JSON line per completed run: timestamp, skill, script, full command, exit
code, and wall duration (Pre/Post events paired by `tool_use_id`).
Non-skill commands are never logged; a missing pair logs with
`duration_ms: null` rather than being dropped. The ledger is executed
evidence: what the plugin actually ran, independent of what was narrated.
`.audit/` is gitignored — the ledger is a local audit trail, not repo
content. `run-report` renders the ledger: text tree on any surface,
`--html` for the interactive drill-down view.

## Design principles

See [CLAUDE.md](CLAUDE.md) for the design principles and repo structure that Claude uses when working in this repository.

## License

MIT
