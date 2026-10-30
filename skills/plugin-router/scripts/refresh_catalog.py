#!/usr/bin/env python3
"""
Refresh the plugin-router catalog from the installed marketplaces under
~/.claude/plugins/marketplaces/.

Writes:
  - SQLite DB at ~/.skill-admin/plugin-router/catalog.sqlite (runtime source
    of truth, never shipped in the repo).
  - Markdown files skills/plugin-router/references/catalog.md and
    catalog-index.md (human-readable, git-diffable artifacts regenerated
    from the same collected data).

Usage:
    uv run skills/plugin-router/scripts/refresh_catalog.py            # refresh only if stale
    uv run skills/plugin-router/scripts/refresh_catalog.py --force    # always rebuild
    uv run skills/plugin-router/scripts/refresh_catalog.py --check    # report fresh/stale, exit 0/1
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).parent.resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import catalog_db

MARKETPLACES_DIR = Path.home() / ".claude" / "plugins" / "marketplaces"
OUTPUT_FILE = SCRIPT_DIR.parent / "references" / "catalog.md"
INDEX_FILE = SCRIPT_DIR.parent / "references" / "catalog-index.md"


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse simple YAML-like frontmatter delimited by ---."""
    if not text.startswith("---"):
        return {}
    _, rest = text.split("---", 1)
    parts = rest.split("---", 1)
    if len(parts) != 2:
        return {}
    fm_text = parts[0].strip()
    body = parts[1].strip()

    data: dict[str, Any] = {"_body": body}
    current_key: str | None = None
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_key, current_lines
        if current_key is None:
            return
        value = "\n".join(current_lines).strip()
        # Remove leading '>' or '|' used in folded/literal YAML blocks
        if value.startswith(">"):
            value = "\n".join(line.lstrip() for line in value.splitlines()[1:]).strip()
        elif value.startswith("|"):
            value = "\n".join(line for line in value.splitlines()[1:]).strip()
        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        data[current_key] = value
        current_key = None
        current_lines = []

    for raw_line in fm_text.splitlines():
        line = raw_line.rstrip()
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            flush()
            current_key = match.group(1)
            current_lines.append(match.group(2))
        elif current_key is not None:
            current_lines.append(line)
    flush()
    return data


def read_skill_md(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return {}
    return parse_frontmatter(text)


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _collect_skills_recursive(skills_dir: Path) -> list[dict[str, Any]]:
    """Recursively collect skills from a directory tree.

    Handles both flat layouts (skills/name/SKILL.md) and nested
    layouts (skills/category/name/SKILL.md, or deeper).
    """
    found: list[dict[str, Any]] = []
    if not skills_dir.is_dir():
        return found

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            fm = read_skill_md(skill_md)
            found.append({
                "name": fm.get("name", skill_dir.name),
                "description": fm.get("description", ""),
            })
        else:
            # Recurse into nested category directories
            found.extend(_collect_skills_recursive(skill_dir))

    return found


def _find_plugin_manifests(plugin_dir: Path) -> dict[str, Any]:
    """Find plugin.json in standard locations within a plugin directory."""
    for candidate in [
        plugin_dir / ".claude-plugin" / "plugin.json",
        plugin_dir / "plugin.json",
        plugin_dir / ".cursor-plugin" / "plugin.json",
        plugin_dir / ".codex-plugin" / "plugin.json",
        plugin_dir / ".qoder-plugin" / "plugin.json",
    ]:
        if candidate.exists():
            return read_json(candidate)
    return {}


def collect_marketplaces() -> dict[str, dict[str, Any]]:
    marketplaces: dict[str, dict[str, Any]] = {}
    if not MARKETPLACES_DIR.exists():
        return marketplaces

    for mp_dir in sorted(MARKETPLACES_DIR.iterdir()):
        if not mp_dir.is_dir():
            continue
        if mp_dir.name.startswith("temp_git_"):
            continue

        mp_manifest_paths = [
            mp_dir / ".claude-plugin" / "marketplace.json",
            mp_dir / ".cursor-plugin" / "marketplace.json",
            mp_dir / ".grok-plugin" / "marketplace.json",
            mp_dir / ".kimi-plugin" / "marketplace.json",
        ]
        mp_info = {}
        for p in mp_manifest_paths:
            if p.exists():
                mp_info = read_json(p)
                break

        plugins: list[dict[str, Any]] = []
        skills: list[dict[str, Any]] = []
        commands: list[dict[str, Any]] = []
        agents: list[dict[str, Any]] = []

        # Top-level skills: handles both flat and nested layouts
        skills_dir = mp_dir / "skills"
        if skills_dir.is_dir():
            skills = _collect_skills_recursive(skills_dir)

        # Plugins under plugins/<plugin>/
        plugins_dir = mp_dir / "plugins"
        if plugins_dir.is_dir():
            for plugin_dir in sorted(plugins_dir.iterdir()):
                if not plugin_dir.is_dir():
                    continue

                plugin_data = _find_plugin_manifests(plugin_dir)
                plugin_name = plugin_data.get("name", plugin_dir.name)
                plugin_desc = plugin_data.get("description", "")

                plugin_skills: list[dict[str, Any]] = []
                plugin_commands: list[dict[str, Any]] = []
                plugin_agents: list[dict[str, Any]] = []

                # Plugin skills: recursive to handle nested categories
                plugin_skills_dir = plugin_dir / "skills"
                if plugin_skills_dir.is_dir():
                    plugin_skills = _collect_skills_recursive(plugin_skills_dir)

                # Single-skill plugin at root
                single_skill_md = plugin_dir / "SKILL.md"
                if single_skill_md.exists():
                    fm = read_skill_md(single_skill_md)
                    if fm.get("name") or fm.get("description"):
                        plugin_skills.append({
                            "name": fm.get("name", plugin_dir.name),
                            "description": fm.get("description", ""),
                        })

                # Commands: recursive glob
                commands_dir = plugin_dir / "commands"
                if commands_dir.is_dir():
                    for cmd_file in sorted(commands_dir.rglob("*.md")):
                        fm = read_skill_md(cmd_file)
                        cmd_name = fm.get("name", cmd_file.stem)
                        plugin_commands.append({
                            "name": cmd_name,
                            "description": fm.get("description", ""),
                        })

                # Agents: recursive glob
                agents_dir = plugin_dir / "agents"
                if agents_dir.is_dir():
                    for agent_file in sorted(agents_dir.rglob("*.md")):
                        fm = read_skill_md(agent_file)
                        agent_name = fm.get("name", agent_file.stem)
                        plugin_agents.append({
                            "name": agent_name,
                            "description": fm.get("description", ""),
                        })

                plugins.append({
                    "name": plugin_name,
                    "description": plugin_desc,
                    "skills": plugin_skills,
                    "commands": plugin_commands,
                    "agents": plugin_agents,
                })

        # ECC-style: no plugins/ dir, but top-level agents/ and commands/
        # Treat the marketplace itself as a single plugin
        if not plugins and (skills or (mp_dir / "agents").is_dir() or (mp_dir / "commands").is_dir()):
            ecc_agents: list[dict[str, Any]] = []
            ecc_commands: list[dict[str, Any]] = []

            agents_dir = mp_dir / "agents"
            if agents_dir.is_dir():
                for agent_file in sorted(agents_dir.rglob("*.md")):
                    fm = read_skill_md(agent_file)
                    agent_name = fm.get("name", agent_file.stem)
                    ecc_agents.append({
                        "name": agent_name,
                        "description": fm.get("description", ""),
                    })

            commands_dir = mp_dir / "commands"
            if commands_dir.is_dir():
                for cmd_file in sorted(commands_dir.rglob("*.md")):
                    fm = read_skill_md(cmd_file)
                    cmd_name = fm.get("name", cmd_file.stem)
                    ecc_commands.append({
                        "name": cmd_name,
                        "description": fm.get("description", ""),
                    })

            plugins.append({
                "name": mp_dir.name,
                "description": mp_info.get("description", ""),
                "skills": skills,
                "commands": ecc_commands,
                "agents": ecc_agents,
            })
            skills = []  # Moved into plugin

        marketplaces[mp_dir.name] = {
            "info": mp_info,
            "skills": skills,
            "plugins": plugins,
        }

    return marketplaces


def trigger_phrases(name: str, description: str) -> str:
    """Derive a short trigger hint from the skill/command/agent."""
    desc = (description or "").lower()
    tokens = [t for t in re.split(r"[^a-z0-9]+", (name or "").lower()) if t]
    hints = []
    if "review" in desc or "review" in tokens:
        hints.append(f"\"review {name}\"")
    if "test" in desc or "test" in tokens:
        hints.append(f"\"test {name}\"")
    if "debug" in desc or "debug" in tokens:
        hints.append(f"\"debug {name}\"")
    if "design" in desc or "design" in tokens:
        hints.append(f"\"design {name}\"")
    if not hints:
        hints.append(f"\"{name}\"")
    return ", ".join(hints[:3])


def escape_md(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def render_catalog(marketplaces: dict[str, dict[str, Any]]) -> str:
    lines: list[str] = [
        "# Installed Plugin / Skill / Agent Catalog",
        "",
        f"Generated from `{MARKETPLACES_DIR}`.",
        "Run `uv run skills/plugin-router/scripts/refresh_catalog.py` to regenerate.",
        "",
    ]

    total_plugins = 0
    total_skills = 0
    total_commands = 0
    total_agents = 0

    for mp_name, mp_data in sorted(marketplaces.items()):
        info = mp_data.get("info", {})
        mp_desc = info.get("description", "")
        lines.append(f"## Marketplace: `{mp_name}`")
        if mp_desc:
            lines.append(f"\n{mp_desc}\n")

        for skill in sorted(mp_data.get("skills", []), key=lambda x: x.get("name", "").lower()):
            name = skill.get("name", "")
            desc = skill.get("description", "")
            lines.append(f"- **Skill** `{name}` — {escape_md(desc)} — *trigger*: {trigger_phrases(name, desc)}")
            total_skills += 1

        for plugin in sorted(mp_data.get("plugins", []), key=lambda x: x.get("name", "").lower()):
            pname = plugin.get("name", "")
            pdesc = plugin.get("description", "")
            lines.append(f"\n### Plugin: `{pname}`")
            if pdesc:
                lines.append(f"{escape_md(pdesc)}")
            total_plugins += 1

            for skill in sorted(plugin.get("skills", []), key=lambda x: x.get("name", "").lower()):
                name = skill.get("name", "")
                desc = skill.get("description", "")
                lines.append(f"- **Skill** `{name}` — {escape_md(desc)} — *trigger*: {trigger_phrases(name, desc)}")
                total_skills += 1

            for cmd in sorted(plugin.get("commands", []), key=lambda x: x.get("name", "").lower()):
                name = cmd.get("name", "")
                desc = cmd.get("description", "")
                lines.append(f"- **Command** `/{name}` — {escape_md(desc)} — *trigger*: \"{name}\"")
                total_commands += 1

            for agent in sorted(plugin.get("agents", []), key=lambda x: x.get("name", "").lower()):
                name = agent.get("name", "")
                desc = agent.get("description", "")
                lines.append(f"- **Agent** `{name}` — {escape_md(desc)} — *trigger*: \"use agent {name}\"")
                total_agents += 1

        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Totals")
    lines.append(f"- Marketplaces: {len(marketplaces)}")
    lines.append(f"- Plugins: {total_plugins}")
    lines.append(f"- Skills: {total_skills}")
    lines.append(f"- Commands: {total_commands}")
    lines.append(f"- Agents: {total_agents}")
    lines.append("")

    return "\n".join(lines)


def render_index(marketplaces: dict[str, dict[str, Any]]) -> str:
    """Render a short, agent-loadable index of all skills in the catalog."""
    lines: list[str] = [
        "# Catalog Index (summary)",
        "",
        "Agent-loadable summary of `catalog.md`. Regenerate with `refresh_catalog.py`.",
        "",
        "## Skills",
    ]

    seen: set[str] = set()
    total = 0
    for mp_name, mp_data in sorted(marketplaces.items()):
        entries: list[dict[str, Any]] = []
        for skill in mp_data.get("skills", []):
            entries.append(skill)
        for plugin in mp_data.get("plugins", []):
            for skill in plugin.get("skills", []):
                entries.append(skill)
        for skill in sorted(entries, key=lambda x: x.get("name", "").lower()):
            name = skill.get("name", "")
            if not name or name in seen:
                continue
            seen.add(name)
            desc = re.sub(r"\s+", " ", skill.get("description", "").strip())[:220]
            lines.append(f"- `{name}` — {desc}")
            total += 1

    lines.append("")
    lines.append(f"_{total} unique skills in catalog_")
    return "\n".join(lines)


def count_capabilities(marketplaces: dict[str, dict[str, Any]]) -> int:
    total = 0
    for mp_data in marketplaces.values():
        total += len(mp_data.get("skills", []))
        for plugin in mp_data.get("plugins", []):
            total += len(plugin.get("skills", []))
            total += len(plugin.get("commands", []))
            total += len(plugin.get("agents", []))
    return total


def rebuild_db(marketplaces: dict[str, dict[str, Any]], source_mtime: float | None) -> None:
    """Write the SQLite catalog from collected marketplaces (full rebuild)."""
    # Delete the old DB file so every refresh starts from a clean slate.
    db_path = catalog_db.CATALOG_DB
    if db_path.exists():
        db_path.unlink()

    conn = catalog_db.get_connection(db_path)
    try:
        for mp_name, mp_data in marketplaces.items():
            info = mp_data.get("info", {})
            mp_desc = info.get("description", "")
            catalog_db.write_marketplace(conn, mp_name, mp_desc)

            for skill in mp_data.get("skills", []):
                catalog_db.write_capability(
                    conn,
                    marketplace=mp_name,
                    plugin_id=None,
                    type="skill",
                    name=skill.get("name", ""),
                    description=skill.get("description", ""),
                    domains=",".join(catalog_db.match_domains(skill.get("description", ""))),
                )

            for plugin in mp_data.get("plugins", []):
                plugin_id = catalog_db.write_plugin(
                    conn,
                    marketplace=mp_name,
                    name=plugin.get("name", ""),
                    description=plugin.get("description", ""),
                )

                for skill in plugin.get("skills", []):
                    catalog_db.write_capability(
                        conn,
                        marketplace=mp_name,
                        plugin_id=plugin_id,
                        type="skill",
                        name=skill.get("name", ""),
                        description=skill.get("description", ""),
                        domains=",".join(catalog_db.match_domains(skill.get("description", ""))),
                    )

                for cmd in plugin.get("commands", []):
                    catalog_db.write_capability(
                        conn,
                        marketplace=mp_name,
                        plugin_id=plugin_id,
                        type="command",
                        name=cmd.get("name", ""),
                        description=cmd.get("description", ""),
                        domains=",".join(catalog_db.match_domains(cmd.get("description", ""))),
                    )

                for agent in plugin.get("agents", []):
                    catalog_db.write_capability(
                        conn,
                        marketplace=mp_name,
                        plugin_id=plugin_id,
                        type="agent",
                        name=agent.get("name", ""),
                        description=agent.get("description", ""),
                        domains=",".join(catalog_db.match_domains(agent.get("description", ""))),
                    )

        catalog_db.finalize_refresh(conn, source_mtime or 0.0)
    finally:
        conn.close()


def do_refresh(force: bool = False) -> bool:
    """Rebuild the catalog. Returns True if a refresh happened."""
    if not force and not catalog_db.is_stale():
        print("Catalog DB is fresh; nothing to do. Use --force to rebuild.")
        return False

    marketplaces = collect_marketplaces()
    source_mtime = catalog_db.newest_source_mtime()

    rebuild_db(marketplaces, source_mtime)

    output = render_catalog(marketplaces)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(output, encoding="utf-8")

    index = render_index(marketplaces)
    INDEX_FILE.write_text(index + "\n", encoding="utf-8")

    n_caps = count_capabilities(marketplaces)
    print(f"Wrote {catalog_db.CATALOG_DB}")
    print(f"  Marketplaces: {len(marketplaces)}")
    print(f"  Capabilities: {n_caps}")
    print(f"Wrote {OUTPUT_FILE}")
    print(f"Wrote {INDEX_FILE}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Refresh the plugin-router catalog (SQLite + markdown)."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild even if the catalog DB is fresh.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Report fresh/stale and exit (0 = fresh, 1 = stale).",
    )
    args = parser.parse_args()

    if args.check:
        stale = catalog_db.is_stale()
        print("stale" if stale else "fresh")
        sys.exit(1 if stale else 0)

    refreshed = do_refresh(force=args.force)
    sys.exit(0 if refreshed or not catalog_db.is_stale() else 1)


if __name__ == "__main__":
    main()
