# skill-admin

A reusable multi-surface plugin that routes dev build-phase requests to the best-fit
plugin, skill, command, agent, or MCP add-on — with a reputation-based ranking
engine, marketplace optimizer, and project atlas. Works on Claude Code CLI and
Claude Desktop / Cowork Surface.

## Repo structure

```
skill-admin/
├── .claude-plugin/
│   ├── plugin.json                  # Plugin manifest (Anthropic schema)
│   └── marketplace.json             # Self-host marketplace manifest
├── workflows/                       # Workflow scripts (shipped with the plugin)
│   ├── skill-admin.bootstrap-project.workflow.js  # 3-phase: atlas → optimizer → steering
│   └── skill-admin.patch-plugin.workflow.js       # Ad-hoc plugin modification
├── skills/                          # Skill definitions (SKILL.md + scripts)
│   ├── intake/                      # Step 0 intent articulation (entry point)
│   ├── plugin-router/               # Routing tables + ranking engine
│   ├── marketplace-optimizer/       # Reputation scoring, gap analysis, token audit
│   ├── project-atlas/               # Steering file parsing + capability mapping
│   ├── plugin-manager/              # Install/remove/enable/disable
│   ├── plugin-doctor/               # Diagnose + repair
│   ├── plugin-feedback/             # Feedback capture for routing misses
│   ├── steering-writer/             # Steering file creation/editing
│   ├── skill-orchestrator/          # Multi-skill sequencing with safety gates
│   └── marketplace-bootstrapper/    # Fresh-machine setup
├── scripts/                         # Utility scripts (not shipped as skills)
│   └── catalog_refresh.py           # Catalog refresh logic
├── tests/                           # Deterministic unit tests + behavior evals
│   ├── test_*.py                    # Deterministic tests (offline)
│   └── evals/                       # Behavior eval definitions + results
│       ├── evals-*.json             # Eval definitions
│       ├── results-*.json           # Eval results
│       └── runner/                  # Eval runner scripts
└── references/                      # Shared reference data
    ├── steering-file-schema.md      # Full CLAUDE.md frontmatter schema
    └── token-cost-estimation.md     # Methodology
```

## How to use skills in this repo

Each skill is self-contained in its directory. `SKILL.md` defines the skill.
Scripts live alongside in `scripts/` or `references/`.

### Step-by-step

1. **Skill definition** — read the `SKILL.md` for the skill you need.
2. **Surface selection** — read the "Surface Execution" section in the SKILL.md.
   It tells you which code path to use based on the detected surface.
3. **Execution** — follow the procedure in the SKILL.md exactly.
   All skills pause for user confirmation before any write or install.

### Design principles

- **One job per skill** — each skill has a clear purpose. Reports never execute.
  Executors never audit.
- **Surface-aware** — every skill detects the runtime surface and uses the
  appropriate mechanism (shell vs. file operations).
- **Human-in-the-loop** — all executor skills pause for confirmation before any
  write, install, or configuration change.
- **Audit-then-act** — always diagnose before repairing. Never modify a plugin
  without understanding its current state.
- **Feedback loop** — plugin-feedback captures routing misses; marketplace-optimizer
  reads them during gap analysis.

## Running tests

```bash
# Deterministic tests (offline)
uv run pytest tests/ -q

# Behavior evals (see tests/evals/ for definitions)
uv run python tests/evals/runner/run_evals.py --manifest tests/evals/evals-multisurface.json
```

## Adding a new skill

1. Create `skills/<name>/SKILL.md` with the skill definition.
2. Add a "Surface Execution" table mapping each surface to its code path.
3. Add a "How to run" section with step-by-step instructions.
4. Add tests in `tests/test_<name>_md_structure.py`.
5. Register the skill in `.claude-plugin/plugin.json`.
6. Update the skill table in `README.md`.

## Claude session rules

- Never modify files without reading them first.
- Never run `git push` without explicit user approval.
- Always use `uv run python` or `uv run pytest` for Python commands.
- Always check the "Surface Execution" section in SKILL.md before executing.

## Known gaps

See [docs/gaps.md](docs/gaps.md) for tracked gaps (roadmap, dry-run profiles, security,
steering-parser robustness, eval hardening, docs).
