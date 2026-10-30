#!/usr/bin/env python3
"""
Recommend plugins, skills, commands, agents, and marketplaces for a project
requirement using a reputation-based ranking engine.

Usage:
    uv run skills/plugin-router/scripts/recommend.py "Build a secure .NET web API with React frontend"
    uv run skills/plugin-router/scripts/recommend.py "Build a secure .NET web API with React frontend" --json
    uv run skills/plugin-router/scripts/recommend.py "<requirement>" --json --log-invocation [--chosen <capability>]

Output:
    Ranked list of installed capabilities + recommended marketplaces to install.
    With --json, emits a machine-readable object instead of formatted text.
    With --log-invocation, appends one audit line to ~/.skill-admin/invocations.jsonl.
    The invocation log is never read by scoring.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Windows console: force UTF-8 for stdout
import os
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, errors="replace")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, errors="replace")

# ── Paths ────────────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
SKILL_ROOT = SCRIPT_DIR.parent
WISHLIST_FILE = SKILL_ROOT / "references" / "marketplace-wishlist.md"
MARKETPLACES_DIR = Path.home() / ".claude" / "plugins" / "marketplaces"
REFRESH_SCRIPT = SCRIPT_DIR / "refresh_catalog.py"

sys.path.insert(0, str(SCRIPT_DIR))
import catalog_db  # noqa: E402

# ── Domain taxonomies ───────────────────────────────────────────────────────

DOMAINS: dict[str, list[str]] = {
    "web-frontend": ["react", "vue", "vue3", "nuxt", "pinia", "vite", "svelte", "angular", "nextjs", "frontend", "ui", "ux", "tailwind", "css", "html", "web", "spa", "component", "design"],
    "web-backend": ["api", "rest", "graphql", "backend", "server", "node", "express", "fastapi", "django", "flask", "spring", "aspnet", "database", "sql", "postgres", "mysql", "mongodb"],
    "mobile": ["ios", "android", "react-native", "flutter", "swift", "kotlin", "mobile", "apk", "ipa"],
    "desktop": ["electron", "tauri", "desktop", "gui", "qt", "wxwidgets"],
    "systems": ["c", "c++", "rust", "zig", "go", "systems", "kernel", "driver", "embedded", "firmware", "bare-metal", "rtos", "microcontroller", "memory", "unsafe", "assembly", "simd", "ffi"],
    "security": ["security", "pentest", "vulnerability", "owasp", "xss", "sqli", "injection", "auth", "jwt", "secrets", "cve", "exploit", "ctf", "forensics", "malware", "harden", "compliance", "soc2", "gdpr", "iso27001"],
    "reverse-engineering": ["reverse", "decompile", "disassemble", "binary", "ghidra", "radare", "ida", "firmware-analysis", "apk", "ipa", "unpack", "obfuscate", "protocol-analysis"],
    "design": ["design", "ui", "ux", "figma", "brand", "visual", "palette", "typography", "poster", "canvas", "mockup", "wireframe", "redesign", "rebrand", "theme"],
    "data": ["data", "analytics", "chart", "visualization", "dashboard", "etl", "pipeline", "ml", "ai", "model", "training", "inference"],
    "docs": ["docx", "xlsx", "pptx", "pdf", "word", "excel", "powerpoint", "document", "report", "memo", "letter", "template"],
    "devops": ["deploy", "ci", "cd", "docker", "kubernetes", "aws", "azure", "gcp", "terraform", "helm", "pipeline", "release", "ship"],
    "testing": ["test", "testing", "tdd", "unit-test", "integration-test", "e2e", "coverage", "regression", "flaky"],
    "debugging": ["debug", "bug", "error", "exception", "stack-trace", "crash", "memory-leak", "performance", "profile", "trace"],
    "dotnet": ["dotnet", "c#", "csharp", "aspnet", "blazor", "maui", "ef-core", "f#", "fsharp", "nuget", ".net"],
    "typescript": ["typescript", "ts", "react", "nextjs", "node", "deno", "bun", "type-level"],
    "python": ["python", "django", "flask", "fastapi", "pandas", "numpy", "pip", "uv", "pytest"],
}

# ── Official marketplaces ───────────────────────────────────────────────────

OFFICIAL_MARKETPLACES = {"claude-plugins-official", "anthropic-agent-skills"}

# ── Project type detection ─────────────────────────────────────────────────

PROJECT_SIGNATURES: dict[str, list[str]] = {
    "typescript-react": ["package.json", "src/**/*.tsx", "next.config.js", "react"],
    "typescript-vue": ["package.json", "src/**/*.vue", "vite.config.ts", "nuxt.config.ts", "vue.config.js"],
    "typescript-svelte": ["package.json", "src/**/*.svelte", "svelte.config.js"],
    "typescript-angular": ["package.json", "src/**/*.component.ts", "angular.json"],
    "dotnet": ["*.csproj", "*.sln", "Program.cs", "Startup.cs", "global.json"],
    "dotnet-vue": ["*.csproj", "package.json", "src/**/*.vue"],  # hybrid
    "dotnet-react": ["*.csproj", "package.json", "src/**/*.tsx"],
    "python-fastapi": ["requirements.txt", "pyproject.toml", "main.py", "fastapi"],
    "python-django": ["requirements.txt", "manage.py", "django"],
    "python-flask": ["requirements.txt", "app.py", "flask"],
    "rust": ["Cargo.toml", "src/**/*.rs"],
    "go": ["go.mod", "cmd/**/*.go"],
    "java-spring": ["pom.xml", "build.gradle", "src/main/java/**/*.java", "spring"],
    "kotlin-android": ["build.gradle.kts", "src/main/AndroidManifest.xml", "kotlin"],
    "swift-ios": ["Package.swift", "ios/**/*.swift", "xcodeproj"],
    "cpp": ["CMakeLists.txt", "Makefile", "src/**/*.cpp", "src/**/*.h"],
    "c": ["Makefile", "src/**/*.c", "src/**/*.h"],
}

PROJECT_DOMAIN_MAP: dict[str, list[str]] = {
    "typescript-react": ["web-frontend", "typescript"],
    "typescript-vue": ["web-frontend", "typescript"],
    "typescript-svelte": ["web-frontend", "typescript"],
    "typescript-angular": ["web-frontend", "typescript"],
    "dotnet": ["dotnet"],
    "dotnet-vue": ["dotnet", "web-frontend", "typescript"],
    "dotnet-react": ["dotnet", "web-frontend", "typescript"],
    "python-fastapi": ["web-backend", "python"],
    "python-django": ["web-backend", "python"],
    "python-flask": ["web-backend", "python"],
    "rust": ["systems"],
    "go": ["systems", "web-backend"],
    "java-spring": ["web-backend"],
    "kotlin-android": ["mobile"],
    "swift-ios": ["mobile"],
    "cpp": ["systems"],
    "c": ["systems"],
}

PROJECT_EXCLUSIONS: dict[str, list[str]] = {
    "typescript-react": ["dotnet", "python", "rust", "go", "java", "kotlin", "swift", "cpp", "c"],
    "typescript-vue": ["dotnet", "python", "rust", "go", "java", "kotlin", "swift", "cpp", "c"],
    "dotnet": ["react", "vue", "svelte", "angular", "python", "rust", "go", "java", "kotlin", "swift"],
    "dotnet-vue": ["python", "rust", "go", "java", "kotlin", "swift", "cpp", "c"],
    "dotnet-react": ["python", "rust", "go", "java", "kotlin", "swift", "cpp", "c"],
    "python-fastapi": ["dotnet", "react", "vue", "rust", "go", "java", "kotlin", "swift", "cpp", "c"],
    "python-django": ["dotnet", "react", "vue", "rust", "go", "java", "kotlin", "swift", "cpp", "c"],
    "rust": ["dotnet", "react", "vue", "python", "java", "kotlin", "swift"],
    "go": ["dotnet", "react", "vue", "python", "java", "kotlin", "swift", "cpp", "c"],
}


def detect_project_type(project_dir: Path) -> str | None:
    """Detect project type from signature files in the project directory."""
    for project_type, signatures in PROJECT_SIGNATURES.items():
        for sig in signatures:
            # Handle glob patterns
            if "*" in sig:
                if list(project_dir.glob(sig)):
                    return project_type
            else:
                if (project_dir / sig).exists():
                    return project_type
    return None


def get_project_domains(project_type: str | None) -> list[str]:
    """Get relevant domains for a detected project type."""
    if not project_type:
        return []
    return PROJECT_DOMAIN_MAP.get(project_type, [])


def get_project_exclusions(project_type: str | None) -> list[str]:
    """Get domains to exclude for a detected project type."""
    if not project_type:
        return []
    return PROJECT_EXCLUSIONS.get(project_type, [])


def is_capability_relevant(cap: Capability, project_type: str | None) -> bool:
    """Check if a capability is relevant for the project type."""
    if not project_type:
        return True  # No filter if unknown project type

    exclusions = get_project_exclusions(project_type)
    cap_domains = set(cap.domains)

    # If capability matches an excluded domain, reject it
    for excl in exclusions:
        if excl in cap_domains:
            return False

    return True

# ── Data classes ────────────────────────────────────────────────────────────

@dataclass
class Capability:
    marketplace: str
    plugin: str | None
    type: str          # skill | command | agent | plugin
    name: str
    description: str
    domains: list[str]  # matched domains

    @property
    def display_score(self) -> int:
        return getattr(self, "_score", 0)


# ── Scoring engine ──────────────────────────────────────────────────────────

def match_domains(text: str) -> list[str]:
    text_lower = text.lower()
    # Normalize separators so "Vue 3" or "vue.js" or "vue-cli" match "vue"
    text_normalized = re.sub(r"[\s\-\.\_,]+", " ", text_lower)
    text_words = set(text_normalized.split())
    matched = []
    for domain, keywords in DOMAINS.items():
        for kw in keywords:
            kw_lower = kw.lower()
            # Require word-boundary match for short keywords to avoid
            # false positives like "academy" matching "academy-guide"
            if len(kw) <= 3:
                if kw_lower in text_words or re.search(rf"\b{re.escape(kw_lower)}\b", text_lower):
                    matched.append(domain)
                    break
            else:
                # Substring match, but also try word-boundary for compound keywords
                if kw_lower in text_lower or re.search(rf"\b{re.escape(kw_lower)}\b", text_normalized):
                    matched.append(domain)
                    break
    return matched


NO_OVERLAP = 0

# Legacy/migration trigger words: a brownfield-only capability is demoted when the
# requirement reads as greenfield (no legacy trigger words present).
LEGACY_SIGNALS = [
    "legacy", "migrate", "migration", "upgrade", "modernize", "refactor",
    "brownfield", "existing", "rewrite", "port", "delta", "compare versions",
]


def is_greenfield_requirement(requirement: str) -> bool:
    """Heuristic: the requirement names no legacy/migration trigger."""
    req = requirement.lower()
    return not any(sig in req for sig in LEGACY_SIGNALS)


def overlap_verdict(cap_domains: list[str], project_domains: list[str]) -> str:
    """Per-candidate domain-overlap verdict for the output line."""
    cap, proj = set(cap_domains), set(project_domains)
    if not cap:
        return "none"
    if cap & proj:
        return "overlap" if cap <= proj else "partial"
    return "none"


def score_capability(cap: Capability, project_domains: list[str], project_type: str | None = None, requirement: str = "") -> int:
    # Project-type exclusion: strongly penalize mismatched tech stacks
    if project_type and not is_capability_relevant(cap, project_type):
        return 0

    # Tech-stack mismatch: reject capabilities whose marketplace/plugin is for a different stack
    cap_text = f"{cap.marketplace} {cap.plugin} {cap.name}".lower()
    req_text = requirement.lower()

    # If the requirement mentions specific frameworks, reject mismatched framework capabilities
    framework_groups = [
        (["vue", "nuxt", "pinia"], ["blazor", "react", "nextjs", "next.js", "svelte", "angular", "ember"]),
        (["react", "nextjs", "next.js"], ["blazor", "vue", "nuxt", "svelte", "angular"]),
        (["dotnet", "c#", "csharp", "aspnet", "blazor"], ["django", "flask", "fastapi", "rails", "laravel", "nodejs", "express"]),
        (["python", "django", "flask", "fastapi"], ["dotnet", "blazor", "c#", "aspnet"]),
        (["rust"], ["dotnet", "python", "java", "go"]),
        (["go"], ["dotnet", "python", "rust", "java", "nodejs"]),
    ]
    for req_frameworks, excluded_frameworks in framework_groups:
        if any(fw in req_text for fw in req_frameworks):
            if any(excl in cap_text for excl in excluded_frameworks):
                return 0

    # Domain match — must overlap with project domains to score at all.
    # Non-overlapping candidates are capped at NO_OVERLAP (0) so that every
    # overlapping candidate, however weak, outranks them.
    overlap = set(cap.domains) & set(project_domains)
    if not overlap:
        return NO_OVERLAP

    # Greenfield demotion: brownfield/legacy-analysis capabilities rank below
    # greenfield-build skills when the requirement reads as greenfield.
    if is_greenfield_requirement(requirement) and cap.domains:
        legacy_markers = ("legacy", "migration", "modernization", "brownfield", "code-modernization")
        if any(m in cap.marketplace.lower() or (cap.plugin and m in cap.plugin.lower()) for m in legacy_markers):
            return NO_OVERLAP

    score = 0

    # Domain match — strongest signal
    score += 40 * min(len(overlap), 3) / 3  # 0..40

    # Reputation — secondary
    rep = get_marketplace_reputation(cap.marketplace)
    score += 20 * rep / 100  # 0..20

    # Official bonus — small
    if cap.marketplace in OFFICIAL_MARKETPLACES:
        score += 10  # 0..10

    # Type fit
    type_scores = {"skill": 1.0, "command": 0.9, "agent": 0.8, "plugin": 0.7}
    score += 15 * type_scores.get(cap.type, 0.5)  # 0..15

    # Specificity
    desc_len = len(cap.description)
    score += 10 * min(desc_len / 200, 1.0)  # 0..10

    return int(min(score, 100))


# ── DB-backed catalog loading ─────────────────────────────────────────────────

def ensure_catalog_fresh() -> None:
    """Check staleness; auto-refresh if the DB is older than the marketplace source."""
    if not catalog_db.is_stale():
        return
    try:
        result = subprocess.run(
            [sys.executable, str(REFRESH_SCRIPT)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(
                f"warning: catalog refresh failed (exit {result.returncode}), using existing data",
                file=sys.stderr,
            )
    except subprocess.TimeoutExpired:
        print("warning: catalog refresh timed out, using existing data", file=sys.stderr)
    except Exception as e:
        print(f"warning: catalog refresh error: {e}, using existing data", file=sys.stderr)


def load_capabilities() -> list[Capability]:
    """Load capabilities from the SQLite runtime catalog."""
    ensure_catalog_fresh()
    try:
        conn = catalog_db.get_connection()
        rows = catalog_db.query_capabilities(conn, limit=10000)
        conn.close()
    except Exception as e:
        print(f"warning: could not query catalog DB: {e}", file=sys.stderr)
        return []

    capabilities = []
    for row in rows:
        domains = match_domains(f"{row['name']} {row['description']}")
        capabilities.append(
            Capability(
                marketplace=row["marketplace"],
                plugin=None,  # plugin name is in the DB but not used for scoring
                type=row["type"],
                name=row["name"],
                description=row["description"],
                domains=domains,
            )
        )
    return capabilities


# ── Reputation lookup ───────────────────────────────────────────────────────

_REPUTATION_CACHE: dict[str, int] = {}


def get_marketplace_reputation(marketplace: str) -> int:
    if marketplace in _REPUTATION_CACHE:
        return _REPUTATION_CACHE[marketplace]

    rep = 50  # default for unknown
    if WISHLIST_FILE.exists():
        text = WISHLIST_FILE.read_text(encoding="utf-8")
        # Find the marketplace section and extract its Reputation line
        pattern = rf"### `{re.escape(marketplace)}`.*?- \*\*Reputation\*\*: (\d+)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            rep = int(match.group(1))

    _REPUTATION_CACHE[marketplace] = rep
    return rep


# ── Catalog loading (delegated to catalog_db) ────────────────────────────────

def parse_catalog() -> list[Capability]:
    return load_capabilities()


# ── Marketplace recommendation ──────────────────────────────────────────────

def recommend_marketplaces(project_domains: list[str]) -> list[dict[str, Any]]:
    if not WISHLIST_FILE.exists():
        return []
    text = WISHLIST_FILE.read_text(encoding="utf-8")

    # Parse wishlist entries
    entries = []
    for match in re.finditer(
        r"### `([^`]+)`\n- \*\*URL\*\*: ([^\n]+)\n(.*?)(?=\n### |\n---|\Z)",
        text,
        re.DOTALL,
    ):
        name = match.group(1)
        url = match.group(2).strip()
        body = match.group(3)
        domains_m = re.search(r"- \*\*Domains\*\*: ([^\n]+)", body)
        rep_m = re.search(r"- \*\*Reputation\*\*: (\d+)", body)
        desc_m = re.search(r"- \*\*Description\*\*: ([^\n]+)", body)

        if not rep_m:
            continue

        entry_domains = []
        if domains_m:
            entry_domains = [d.strip() for d in domains_m.group(1).split(",")]

        # Check if marketplace covers any project domain
        overlap = set(project_domains) & set(entry_domains)
        if not overlap:
            continue

        # Check if already installed
        installed = (MARKETPLACES_DIR / name).exists()

        entries.append({
            "name": name,
            "url": url,
            "reputation": int(rep_m.group(1)),
            "domains": entry_domains,
            "overlap": list(overlap),
            "installed": installed,
            "score": int(rep_m.group(1)) + len(overlap) * 10,
        })

    entries.sort(key=lambda x: x["score"], reverse=True)
    return entries


# ── Invocation log (audit only — never read by scoring) ──────────────────────

INVOCATIONS_LOG = Path.home() / ".skill-admin" / "invocations.jsonl"


def log_invocation(requirement: str, project_type: str | None, top: list[Capability], chosen: str | None) -> None:
    INVOCATIONS_LOG.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "request": requirement[:200],
        "project_type": project_type,
        "top": [f"{c.marketplace}:{c.name}" for c in top[:5]],
        "chosen": chosen,
    }
    with open(INVOCATIONS_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


# ── Main ────────────────────────────────────────────────────────────────────

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Recommend plugins/skills for a project requirement")
    parser.add_argument("requirement", help="project requirement description")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--log-invocation", action="store_true", help="append one audit line to ~/.skill-admin/invocations.jsonl")
    parser.add_argument("--chosen", default=None, help="capability the user actually chose (logged with --log-invocation)")
    args = parser.parse_args()

    requirement = args.requirement

    # Auto-detect project type from current directory
    project_dir = Path.cwd()
    project_type = detect_project_type(project_dir)
    detected_domains = get_project_domains(project_type)

    # Match requirement keywords to domains
    requirement_domains = match_domains(requirement)

    # Merge: requirement domains take priority, detected adds context
    project_domains = list(set(requirement_domains) | set(detected_domains))

    # Score installed capabilities
    capabilities = parse_catalog()
    for cap in capabilities:
        cap._score = score_capability(cap, project_domains, project_type, requirement)  # type: ignore[attr-defined]

    capabilities.sort(key=lambda c: c.display_score, reverse=True)

    # Recommend marketplaces (do once before JSON/text branch)
    recommendations = recommend_marketplaces(project_domains)

    def _top_installed(n: int = 20) -> list[Capability]:
        seen: set[str] = set()
        out: list[Capability] = []
        for cap in capabilities:
            if cap.display_score == 0:
                continue
            key = f"{cap.marketplace}:{cap.name}"
            if key in seen:
                continue
            seen.add(key)
            out.append(cap)
            if len(out) >= n:
                break
        return out

    if args.json:
        payload = {
            "project_type": project_type,
            "project_domains": detected_domains,
            "requirement_domains": requirement_domains,
            "installed": [
                {
                    "name": c.name,
                    "type": c.type,
                    "plugin": c.plugin,
                    "marketplace": c.marketplace,
                    "score": c.display_score,
                    "verdict": overlap_verdict(c.domains, project_domains),
                    "domains": c.domains,
                }
                for c in _top_installed()
            ],
            "marketplaces": recommendations[:10],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if args.log_invocation:
            log_invocation(requirement, project_type, _top_installed(5), args.chosen)
        return

    print(f"\nProject type detected: {project_type or 'unknown'}")
    print(f"Project domains: {', '.join(detected_domains) or 'none'}")
    print(f"Requirement domains: {', '.join(requirement_domains) or 'none'}")
    print(f"Merged domains: {', '.join(project_domains) or 'none'}\n")

    print("=" * 70)
    print("TOP INSTALLED CAPABILITIES FOR YOUR REQUIREMENT")
    print("=" * 70)
    for cap in _top_installed():
        verdict = overlap_verdict(cap.domains, project_domains)
        plugin_str = f" (plugin: {cap.plugin})" if cap.plugin else ""
        print(
            f"  [{cap.display_score:3d}] {cap.type.upper():8s} `{cap.name}`"
            f"{plugin_str}"
            f"\n         from {cap.marketplace}"
            f"\n         verdict: {verdict}"
            f"\n         {cap.description[:120]}..."
        )

    # Recommend marketplaces
    print()
    print("=" * 70)
    print("RECOMMENDED MARKETPLACES TO INSTALL")
    print("=" * 70)
    for rec in recommendations[:10]:
        status = "INSTALLED" if rec["installed"] else "NOT INSTALLED"
        print(
            f"  [{rec['score']:3d}] `{rec['name']}` ({status})"
            f"\n         URL: {rec['url']}"
            f"\n         Reputation: {rec['reputation']}"
            f"\n         Domains: {', '.join(rec['domains'])}"
            f"\n         Overlap: {', '.join(rec['overlap'])}"
        )

    print()


if __name__ == "__main__":
    main()
