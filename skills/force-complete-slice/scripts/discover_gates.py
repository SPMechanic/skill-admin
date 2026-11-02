#!/usr/bin/env python3
"""
Read-only discovery of project instructions, commands, CI, and infrastructure.

This script makes no claim about what the project's authoritative test command
is. It reports *declarations found* so the agent can read them and judge. A
lockfile is evidence that a package manager is in use, not proof that any
command works.

Usage:
    uv run skills/force-complete-slice/scripts/discover_gates.py [ROOT] [--json]

Exit code:
    0 — discovery completed (findings may still be sparse)
    2 — root does not exist or is not a directory
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", ".venv", "venv", "env",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "dist", "build", "target", "bin", "obj", ".next", ".nuxt",
    ".terraform", ".tox", ".gradle", "vendor", "coverage",
}

MAX_FILES_SCANNED = 20000
MAX_DEPTH = 6

INSTRUCTION_FILES = [
    "CLAUDE.md", "AGENTS.md", "README.md", "README", "CONTRIBUTING.md",
    "DEFINITION_OF_DONE.md", "DEFINITION-OF-DONE.md", "DOD.md",
    ".cursor/rules", ".windsurfrules", ".windsurf",
    "docs/ARCHITECTURE.md", "docs/CONTRIBUTING.md",
]

MANIFEST_FILES = {
    "package.json": "node",
    "pnpm-workspace.yaml": "node-workspace",
    "pyproject.toml": "python",
    "setup.py": "python",
    "setup.cfg": "python",
    "requirements.txt": "python",
    "Pipfile": "python",
    "go.mod": "go",
    "Cargo.toml": "rust",
    "pom.xml": "jvm-maven",
    "build.gradle": "jvm-gradle",
    "build.gradle.kts": "jvm-gradle",
    "composer.json": "php",
    "Gemfile": "ruby",
    "mix.exs": "elixir",
    "CMakeLists.txt": "cmake",
    "Makefile": "make",
    "Dockerfile": "container",
}

LOCKFILES = {
    "package-lock.json": "npm",
    "yarn.lock": "yarn",
    "pnpm-lock.yaml": "pnpm",
    "bun.lockb": "bun",
    "uv.lock": "uv",
    "poetry.lock": "poetry",
    "Pipfile.lock": "pipenv",
    "go.sum": "go-modules",
    "Cargo.lock": "cargo",
    "Gemfile.lock": "bundler",
    "composer.lock": "composer",
    "packages.lock.json": "nuget-lock",
}

CI_FILES = [
    ".gitlab-ci.yml",
    ".github/workflows",
    "azure-pipelines.yml",
    "Jenkinsfile",
    ".circleci/config.yml",
    "bitbucket-pipelines.yml",
    ".buildkite",
    "cloudbuild.yaml",
]

PROJECT_FILES = re.compile(r"\.(csproj|fsproj|vbproj|sln|vcxproj)$", re.IGNORECASE)


def scan(root: Path) -> dict:
    """Walk root once, bounded, skipping vendor and build directories."""
    found: list[Path] = []
    truncated = False
    for path in root.rglob("*"):
        if len(found) >= MAX_FILES_SCANNED:
            truncated = True
            break
        try:
            rel = path.relative_to(root)
        except ValueError:  # pragma: no cover - defensive
            continue
        if len(rel.parts) > MAX_DEPTH:
            continue
        if any(part in SKIP_DIRS for part in rel.parts[:-1]):
            continue
        if path.is_file():
            found.append(rel)
    return {"files": found, "truncated": truncated}


def package_scripts(root: Path) -> list[dict]:
    """Extract script names from package.json without assuming npm is used."""
    pkg = root / "package.json"
    if not pkg.is_file():
        return []
    try:
        data = json.loads(pkg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [{"file": "package.json", "error": str(exc)}]
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return []
    return [{"file": "package.json", "name": k, "command": v} for k, v in sorted(scripts.items())]


def make_targets(root: Path) -> list[dict]:
    """Extract Makefile target names. Declarations only — never executed."""
    mk = root / "Makefile"
    if not mk.is_file():
        return []
    out: list[dict] = []
    try:
        for line in mk.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"^([A-Za-z0-9_.-]+)\s*:(?!=)", line)
            if m and not m.group(1).startswith("."):
                out.append({"file": "Makefile", "name": m.group(1)})
    except OSError:
        return []
    return out


def compose_services(rel: Path) -> list[str]:
    """List service names from a compose file, tolerating YAML variants."""
    try:
        text = rel.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    services: list[str] = []
    in_services = False
    for line in text.splitlines():
        if re.match(r"^services\s*:\s*$", line):
            in_services = True
            continue
        if in_services:
            if line.strip() and not line.startswith((" ", "\t")):
                in_services = False
                continue
            m = re.match(r"^\s{2}([A-Za-z0-9_.-]+)\s*:\s*$", line)
            if m:
                services.append(m.group(1))
    return services


def discover(root: Path) -> dict:
    scan_result = scan(root)
    files = scan_result["files"]
    rel_strings = [str(f).replace("\\", "/") for f in files]
    rel_set = set(rel_strings)

    instructions = [p for p in INSTRUCTION_FILES if p in rel_set]

    manifests = [
        {"file": str(f).replace("\\", "/"), "ecosystem": MANIFEST_FILES[f.name]}
        for f in files
        if f.name in MANIFEST_FILES
    ]

    lockfiles = [
        {"file": str(f).replace("\\", "/"), "manager": LOCKFILES[f.name]}
        for f in files
        if f.name in LOCKFILES
    ]

    project_files = [
        str(f).replace("\\", "/") for f in files if PROJECT_FILES.search(f.name)
    ]

    ci: list[str] = []
    for entry in CI_FILES:
        if entry in rel_set:
            ci.append(entry)
        elif any(r.startswith(entry + "/") for r in rel_strings):
            ci.append(entry)

    infrastructure: dict[str, list[str]] = {"compose": [], "terraform": [], "k8s": [], "other": []}
    compose_services_found: dict[str, list[str]] = {}
    for f in files:
        name = f.name
        if name.startswith("docker-compose") or name.startswith("compose."):
            path = str(f).replace("\\", "/")
            infrastructure["compose"].append(path)
            services = compose_services(root / f)
            if services:
                compose_services_found[path] = services
        elif name.endswith(".tf"):
            infrastructure["terraform"].append(str(f).replace("\\", "/"))
        elif name in ("Chart.yaml", "kustomization.yaml") or "k8s" in f.parts or "kube" in f.parts:
            infrastructure["k8s"].append(str(f).replace("\\", "/"))
        elif name in ("Dockerfile", "docker-bake.hcl"):
            infrastructure["other"].append(str(f).replace("\\", "/"))

    warnings: list[str] = []
    if scan_result["truncated"]:
        warnings.append(
            f"file scan truncated at {MAX_FILES_SCANNED} paths; findings may be incomplete"
        )
    if not instructions:
        warnings.append("no project instruction file found; ask the user for conventions")
    if not ci:
        warnings.append("no CI configuration found; CI-executed results are unavailable")
    if not lockfiles and manifests:
        warnings.append("manifests present but no lockfile found; dependency state is unverifiable")

    evidence_gaps: list[str] = []
    if not any(e["ecosystem"] == "node" for e in manifests):
        evidence_gaps.append("no node manifest; a JS/TS UI test runner may still exist")
    if "pyproject.toml" in rel_set and "uv.lock" not in rel_set:
        evidence_gaps.append("pyproject without uv.lock; test runner may be unpinned")

    return {
        "root": str(root),
        "unit_hints": {
            "project_files": project_files,
            "ecosystems": sorted({m["ecosystem"] for m in manifests}),
            "compose_services": compose_services_found,
        },
        "instructions": instructions,
        "manifests": manifests,
        "lockfiles": lockfiles,
        "command_declarations": {
            "package_json_scripts": package_scripts(root),
            "make_targets": make_targets(root),
            "authoritative": False,
            "note": (
                "Declarations only. Read the project instructions to learn which "
                "commands are authoritative; never treat a script's existence as proof it runs."
            ),
        },
        "ci": ci,
        "infrastructure": infrastructure,
        "evidence_gaps": evidence_gaps,
        "warnings": warnings,
        "files_scanned": len(files),
    }


def render_text(result: dict) -> str:
    lines = [f"root: {result['root']}", f"files scanned: {result['files_scanned']}"]
    lines.append("")
    lines.append("instructions:")
    if result["instructions"]:
        lines.extend(f"  - {p}" for p in result["instructions"])
    else:
        lines.append("  (none found)")
    lines.append("")
    lines.append("ecosystems: " + (", ".join(result["unit_hints"]["ecosystems"]) or "(none detected)"))
    lines.append("")
    lines.append("command declarations (unverified):")
    scripts = result["command_declarations"]["package_json_scripts"]
    targets = result["command_declarations"]["make_targets"]
    for s in scripts:
        lines.append(f"  package.json:{s.get('name')} -> {s.get('command', s.get('error', ''))}")
    for t in targets:
        lines.append(f"  Makefile:{t['name']}")
    if not scripts and not targets:
        lines.append("  (none found)")
    lines.append("")
    lines.append("ci: " + (", ".join(result["ci"]) or "(none found)"))
    infra = result["infrastructure"]
    lines.append(
        "infrastructure: "
        + ", ".join(infra[k][0] if infra[k] else "" for k in ("compose", "terraform", "k8s")).strip(", ")
    )
    if result["warnings"]:
        lines.append("")
        lines.append("warnings:")
        lines.extend(f"  - {w}" for w in result["warnings"])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discover project gates (read-only).")
    parser.add_argument("root", nargs="?", default=".", help="repository root to inspect")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")
    args = parser.parse_args(argv)

    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    result = discover(root)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(render_text(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
