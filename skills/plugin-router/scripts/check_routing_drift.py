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

SCRIPT_DIR = Path(__file__).parent.resolve()
REPO_ROOT = SCRIPT_DIR.parent.parent.parent
ROUTER_SKILL = REPO_ROOT / "skills" / "plugin-router" / "SKILL.md"
WORKFLOWS_DIR = REPO_ROOT / ".claude" / "workflows"

sys.path.insert(0, str(SCRIPT_DIR))
import catalog_db  # noqa: E402


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
    """Return skill names from the runtime DB."""
    try:
        conn = catalog_db.get_connection()
        rows = catalog_db.query_capabilities(conn, type="skill", limit=10000)
        conn.close()
        return {row["name"] for row in rows}
    except Exception:
        return set()


def all_catalog_names() -> set[str]:
    """Return all catalog names from the runtime DB (skills, agents, commands, plugins, marketplaces)."""
    names: set[str] = set()
    try:
        conn = catalog_db.get_connection()
        for row in catalog_db.query_capabilities(conn, limit=10000):
            names.add(row["name"])
        for row in conn.execute("SELECT name FROM marketplaces"):
            names.add(row[0])
        for row in conn.execute("SELECT name FROM plugins"):
            names.add(row[0])
        conn.close()
    except Exception:
        pass
    return names


def main() -> int:
    if not catalog_db.get_db_mtime():
        print("error: catalog DB not found — run refresh_catalog.py first", file=sys.stderr)
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
