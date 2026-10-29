---
name: steering-writer
description: >
  Create and edit AI steering files for Claude Code projects. Use when the user
  says "write a CLAUDE.md", "set up my AGENTS.md", "create project instructions",
  "document my project context", or "update my steering files". This skill writes
  to CLAUDE.md, AGENTS.md, .cursor/rules, and .windsurf instructions. It does not
  install plugins or route tasks.
metadata:
  executor: true
---

# Steering Writer

Creates and edits AI steering files for projects. **This skill writes files; it
does not analyze projects or install plugins.** All file writes require explicit
user confirmation.

## Surface Execution

| Surface | Path |
|---|---|
| Claude Code CLI | `Write`/`Edit` tools for file operations |
| Claude Desktop (Cowork) | `Write`/`Edit` tools — same as CLI |
| Claude Desktop (Code) | `Write`/`Edit` tools — same as CLI |
| 3P CLI/Desktop | `Write`/`Edit` tools for `.cursor/rules`, `.windsurf` |

## What this skill does

| Action | Scope |
|---|---|
| **Create** | Generate new steering files from templates or project context |
| **Edit** | Update existing steering files with new rules or context |
| **Refactor** | Split oversized files into smaller focused files |
| **Verify** | Check that files follow Anthropic conventions |

## Supported files

| File | Purpose |
|---|---|
| `CLAUDE.md` | Project-level instructions for Claude Code |
| `AGENTS.md` | Agent definitions and role descriptions |
| `.cursor/rules` | Cursor IDE rules |
| `.windsurf` | Windsurf IDE instructions |

## Inputs

| Input | Description |
|---|---|
| Project context | Tech stack, conventions, architecture |
| Existing steering files | Files to update or replace |
| User requirements | What the AI should know/do |

## Workflow

### Step 1 — Determine intent

Is the user creating a new file or editing an existing one?

### Step 2 — Read existing files

If editing, read the current file first. Never overwrite without showing the diff.

### Step 3 — Generate content

For `CLAUDE.md`:

```markdown
# Project Name

Brief description of the project.

## Tech stack

- Language / framework
- Package manager
- Testing framework

## How Claude should work with this repo

1. Step one
2. Step two
3. Step three

## Conventions

- Code style rules
- Naming conventions
- Testing expectations

## Commands

| Command | Purpose |
|---|---|
| `npm test` | Run tests |
| `npm run build` | Build project |
```

For `AGENTS.md`:

```markdown
# Agents

## Code Reviewer

- Focuses on correctness, performance, and security
- Does not implement changes

## Test Writer

- Writes unit tests and integration tests
- Follows existing test patterns
```

### Step 4 — Confirm before writing

Show the user:
- File path
- Summary of changes
- Full content (for new files) or diff (for edits)

Ask for confirmation before writing.

### Step 5 — Write the file

Use `Write` tool for new files, `Edit` tool for changes.

### Step 6 — Verify

Check:
- File parses as valid Markdown
- Frontmatter is valid (if present)
- No broken internal links
- File size is reasonable (< 2000 lines)

## Templates

### CLAUDE.md template

```markdown
# {project-name}

{one-line description}

## Tech stack

{stack}

## How Claude should work with this repo

{numbered instructions}

## Conventions

{bullets}

## Commands

| Command | Purpose |
|---|---|
```

### AGENTS.md template

```markdown
# Agents

{agent definitions}
```

## What this skill does NOT do

- This skill does not install or remove plugins
- This skill does not route tasks to capabilities
- This skill does not audit plugins or marketplaces
- This skill does not modify source code

## Error handling

| Error | Response |
|---|---|
| File already exists | Show diff, ask whether to overwrite or append |
| Invalid frontmatter | Fix or warn before writing |
| File too large | Propose splitting into multiple files |

## Surfaces

| Surface | Behavior |
|---|---|
| **Claude Code CLI** | Full support. Uses `Write`/`Edit` tools for file operations. |
| **Claude Desktop (Cowork)** | Full support. Same `Write`/`Edit` tools — pauses for confirmation before any write. |
| **Claude Desktop (Code)** | Full support. Project-scoped plugins honored. |
| **3P CLI/Desktop** | Full support. Emits `.cursor/rules` and `.windsurf` files for these surfaces. |

All skills default to `Read`, `Grep`, `Glob` only. Executor skills add `Write`/`Edit` only after explicit user confirmation — on every surface.
