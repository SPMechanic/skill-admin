#!/usr/bin/env python3
"""
Classify slices from their audit artifacts and build dependency waves.

This implements only the rules that are pure file inspection. Hollow
classification, decomposition quality, and the foundation boundary stay prose
in references/dependency-resolution.md — a checker for them would launder
judgment into a green mark.

Classification, from <root>/.audit/<slice>/acceptance.tsv:
    no directory            -> Missing
    every row PASS          -> Complete
    any row not PASS        -> Partial

A row is PASS when its status cell, trimmed and case-folded, is "pass". A file
with a header and no data rows is treated as Missing rather than Complete: an
empty contract proves nothing.

Waves come from inter-slice "depends_on" edges declared in <root>/.audit/
<slices.json> as {"edges": {"<slice>": ["<prerequisite>", ...]}}. A prerequisite
that is not in the slice set is reported as an external dependency and does not
participate in ordering. A cycle is an error, never a wave.

Usage:
    uv run skills/skill-orchestrator/scripts/classify_slices.py <root>
    uv run skills/skill-orchestrator/scripts/classify_slices.py <root> --slice a --slice b
    uv run skills/skill-orchestrator/scripts/classify_slices.py <root> --json

Exit code:
    0 — classified (even when some slices are Missing or Partial)
    2 — root unreadable, or the dependency graph has a cycle
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PASS = "PASS"


def read_acceptance(path: Path) -> list[dict]:
    """Rows of an acceptance.tsv, minus the header. Missing file -> []."""
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return [row for row in reader if any((v or "").strip() for v in row.values())]


def classify(root: Path, slug: str) -> dict:
    file = root / ".audit" / slug / "acceptance.tsv"
    if not file.is_file():
        return {"slice": slug, "class": "Missing", "rows": 0, "not_pass": []}

    rows = read_acceptance(file)
    if not rows:
        return {"slice": slug, "class": "Missing", "rows": 0, "not_pass": []}

    def status_of(row: dict) -> str:
        return str(row.get("status", "")).strip().casefold()

    not_pass = [
        {"criterion": row.get("criterion", ""), "status": (row.get("status") or "").strip()}
        for row in rows
        if status_of(row) != "pass"
    ]
    return {
        "slice": slug,
        "class": "Complete" if not not_pass else "Partial",
        "rows": len(rows),
        "not_pass": not_pass,
        "path": str(file),
    }


def load_edges(root: Path) -> dict[str, list[str]]:
    path = root / ".audit" / "slices.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    edges = data.get("edges", {}) if isinstance(data, dict) else {}
    if not isinstance(edges, dict):
        raise ValueError("'edges' must be an object of slice -> prerequisites")
    out: dict[str, list[str]] = {}
    for slug, prereqs in edges.items():
        if isinstance(prereqs, str) or not isinstance(prereqs, list):
            raise ValueError(f"edges for {slug!r} must be a list of slice names")
        out[slug] = [str(p) for p in prereqs]
    return out


def waves(slugs: list[str], edges: dict[str, list[str]]) -> tuple[list[list[str]], list[dict]]:
    """Topological waves. Returns (waves, external prereqs); raises on a cycle."""
    known = set(slugs)
    internal = {s: [p for p in edges.get(s, []) if p in known] for s in slugs}
    external = [
        {"slice": s, "prerequisite": p}
        for s in slugs
        for p in edges.get(s, [])
        if p not in known
    ]

    placed: set[str] = set()
    out: list[list[str]] = []
    remaining = list(slugs)
    while remaining:
        ready = sorted(s for s in remaining if all(p in placed for p in internal[s]))
        if not ready:
            raise ValueError(
                "dependency cycle among slices: " + ", ".join(sorted(remaining))
            )
        out.append(ready)
        placed.update(ready)
        remaining = [s for s in remaining if s not in placed]
    return out, external


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Classify slices and build waves.")
    parser.add_argument("root", help="repository root containing .audit/")
    parser.add_argument("--slice", action="append", dest="slices", help="slice slug; repeatable")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2

    slugs = args.slices
    if not slugs:
        try:
            declared = set(load_edges(root))
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        # A slice named only in slices.json still has to appear: an absent row
        # reads as "nothing was needed", which is a false green at plan level.
        slugs = sorted(
            {p.parent.name for p in (root / ".audit").glob("*/acceptance.tsv")} | declared
        )
    if not slugs:
        print(f"error: no slices found under {root / '.audit'}", file=sys.stderr)
        return 2

    results = [classify(root, slug) for slug in slugs]

    try:
        edges = load_edges(root)
        wave_list, external = waves(slugs, edges)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(
            json.dumps(
                {"slices": results, "waves": wave_list, "external_prerequisites": external},
                indent=2,
            )
        )
        return 0

    for w, members in enumerate(wave_list, start=1):
        print(f"wave {w}: {', '.join(members)}")
    print()
    by_slug = {r["slice"]: r for r in results}
    for slug in slugs:
        r = by_slug[slug]
        detail = "" if r["class"] != "Partial" else f" ({len(r['not_pass'])} of {r['rows']} not PASS)"
        print(f"  {slug}: {r['class']}{detail}")
    if external:
        print()
        for e in external:
            print(f"  external: {e['slice']} depends on {e['prerequisite']} (not in this set)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
