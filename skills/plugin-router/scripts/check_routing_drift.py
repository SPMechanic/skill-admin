#!/usr/bin/env python3
"""
Check plugin-router routing tables for drift vs. the installed catalog.

What it checks:
1. Every skill name in a routing-table row (targets) exists in the catalog.
2. Every skill in the catalog appears either as a table target or in an alias note.

What it ignores:
- Prose outside tables; example placeholders like `plugin-a`; reason labels like
  `exact-table-match`; marketplace / plugin / command names.

Usage:
    uv run skills/plugin-router/scripts/check_routing_drift.py

Exit code:
    0 — no errors
    1 — table references a skill not in the catalog
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CATALOG_PATH = REPO_ROOT / "skills" / "plugin-router" / "references" / "catalog.md"
ROUTER_SKILL = REPO_ROOT / "skills" / "plugin-router" / "SKILL.md"
WORKFLOWS_DIR = REPO_ROOT / ".claude" / "workflows"


def parse_table_targets(text: str) -> set[str]:
    """Extract backtick names that appear inside Markdown tables as cell values."""
    targets: set[str] = set()
    for block in re.findall(r"((?:\|.*\|\n)+)", text):
        for line in block.splitlines():
            if re.match(r"^\|?\s*:?-+:?,?\s*\|", line):
                continue  # separator line
            cells = [c.strip() for c in line.strip("|").split("|")]
            for cell in cells:
                # Capture each backtick-quoted token; a cell may be `a`, `a`/`b`
                targets.update(re.findall(r"`([a-z0-9][a-z0-9\-]*)`", cell))
    return targets


def parse_alias_names(text: str) -> set[str]:
    """Capture names referenced in alias blocks (parenthetical 'aliases: ...')."""
    names: set[str] = set()
    for m in re.finditer(r"\(aliases?:\s*([^)]+)\)", text, re.IGNORECASE):
        names.update(re.findall(r"`([a-z0-9][a-z0-9\-]*)`", m.group(1)))
    return names


def workflow_names() -> set[str]:
    names: set[str] = set()
    if WORKFLOWS_DIR.exists():
        for p in WORKFLOWS_DIR.glob("*.workflow.js"):
            names.add(p.stem.replace(".workflow", ""))
    return names


def catalog_skill_names() -> set[str]:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    return {
        m.group(1).strip()
        for m in re.finditer(r"^- \*\*Skill\*\* `([^`]+)`", text, re.MULTILINE)
    }


def all_catalog_names() -> set[str]:
    text = CATALOG_PATH.read_text(encoding="utf-8")
    names: set[str] = set()
    # list entries: - **Skill** `name` — / **Command** `/name` — / **Agent** `name`
    for m in re.finditer(
        r"^- \*\*(?:Skill|Agent)\*\* `([^`]+)`", text, re.MULTILINE
    ):
        names.add(m.group(1).strip())
    for m in re.finditer(
        r"^- \*\*Command\*\* `/([^`]+)`", text, re.MULTILINE
    ):
        names.add(m.group(1).strip())
    # plugin headings: ### Plugin: `name`
    for m in re.finditer(r"^### Plugin: `([^`]+)`", text, re.MULTILINE):
        names.add(m.group(1).strip())
    # marketplace headings: ## Marketplace: `name`
    for m in re.finditer(r"^## Marketplace: `([^`]+)`", text, re.MULTILINE):
        names.add(m.group(1).strip())
    return names


def main() -> int:
    if not CATALOG_PATH.exists():
        print(f"error: catalog not found: {CATALOG_PATH}", file=sys.stderr)
        return 1

    router_text = ROUTER_SKILL.read_text(encoding="utf-8")
    table_targets = parse_table_targets(router_text)
    alias_names = parse_alias_names(router_text)
    referenced = table_targets | alias_names

    # Workflow names are orchestration glue, not catalog entries.
    referenced -= workflow_names()

    skills = catalog_skill_names()
    all_names = all_catalog_names()

    uncovered = sorted(skills - referenced)
    # An error if a table/alias references a name not in the catalog at all.
    missing = sorted(referenced - all_names)

    print(f"catalog skills: {len(skills)}")
    print(f"covered by routing tables/aliases: {len(skills & referenced)}")
    print(f"uncovered (warning): {len(uncovered)}")
    for name in uncovered[:10]:
        print(f"  uncovered: {name}")
    if len(uncovered) > 10:
        print(f"  ... and {len(uncovered) - 10} more")
    if missing:
        print(f"missing from catalog (error): {len(missing)}")
        for name in missing:
            print(f"  missing: {name}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
