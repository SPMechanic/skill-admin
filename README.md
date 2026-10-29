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

## Surface compatibility

See [docs/surfaces.md](docs/surfaces.md) for the full multi-surface execution path matrix.

## Design principles

See [CLAUDE.md](CLAUDE.md) for the design principles and repo structure that Claude uses when working in this repository.

## License

MIT
