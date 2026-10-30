#!/usr/bin/env python3
"""
SQLite-backed runtime catalog for plugin-router.

The DB is a disposable cache of the discovered marketplace inventory,
rebuilt in full by refresh_catalog.py. It lives outside the repo so it
is never shipped and never stale-by-shipping.

Usage (as a library):
    conn = get_connection()
    write_marketplace(conn, "my-marketplace", "desc")
    plugin_id = write_plugin(conn, "my-marketplace", "my-plugin", "desc")
    write_capability(conn, "my-marketplace", plugin_id, "skill", "my-skill",
                     "desc", domains="testing")
    finalize_refresh(conn, source_mtime)
    rows = query_capabilities(conn, domains="testing")
"""

from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path

CATALOG_DB = Path.home() / ".skill-admin" / "plugin-router" / "catalog.sqlite"
DEFAULT_SOURCE_DIR = Path.home() / ".claude" / "plugins" / "marketplaces"

SCHEMA = """
CREATE TABLE IF NOT EXISTS marketplaces (
    name TEXT PRIMARY KEY,
    description TEXT
);

CREATE TABLE IF NOT EXISTS plugins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    marketplace TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    FOREIGN KEY (marketplace) REFERENCES marketplaces(name)
);

CREATE TABLE IF NOT EXISTS capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plugin_id INTEGER,
    marketplace TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('skill', 'command', 'agent')),
    name TEXT NOT NULL,
    description TEXT,
    domains TEXT,
    FOREIGN KEY (plugin_id) REFERENCES plugins(id)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_capabilities_type_name
    ON capabilities(type, name);

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""

DOMAINS = {
    "backend", "frontend", "full-stack", "mobile", "testing", "security",
    "database", "devops", "infrastructure", "documentation", "api", "web",
    "performance", "refactoring", "design", "ui", "ux", "cli", "config",
    "observability", "data", "ml", "ai", "llm", "agents", "migration",
    "networking", "caching", "queue", "auth", "encryption", "secrets",
    "compliance", "supply-chain", "cloud", "serverless", "containers",
    "kubernetes", "ci-cd", "iac", "git", "build", "lint", "format",
    "type-check", "runtime", "web3", "embedded", "os", "shell", "editor",
    "ide", "browser", "desktop", "iot", "game", "ar-vr", "3d", "audio",
    "video", "image", "pdf", "office", "markdown", "xml", "yaml", "json",
    "csv", "sql", "graphql", "rest", "grpc", "websocket", "email",
    "messaging", "notifications", "payments", "billing", "crm", "erp",
    "hr", "finance", "legal", "medical", "science", "math", "stats",
    "nlp", "vision", "speech", "translation", "ocr", "search",
    "recommendation", "forecasting", "optimization", "simulation",
    "robotics", "blockchain", "crypto", "p2p", "cdn", "dns", "proxy",
    "vpn", "firewall", "ids-ips", "siem", "waf", "ddos", "zero-trust",
    "sso", "oauth", "saml", "jwt", "rbac", "abac", "policy", "audit",
    "backup", "dr", "ha", "scalability", "capacity", "cost", "green",
    "sustainability", "ethics", "privacy", "fairness", "bias",
    "explainability", "robustness", "safety", "alignment", "red-team",
    "blue-team", "purple-team", "threat-intel", "osint", "forensics",
    "malware", "reverse-engineering", "exploit", "vulnerability",
    "patch", "config-management", "monitoring", "alerting", "tracing",
    "logging", "metrics", "dashboards", "reporting", "analytics", "bi",
    "etl", "elt", "data-warehouse", "data-lake", "data-mesh",
    "streaming", "batch", "olap", "oltp", "nosql", "relational",
    "graph", "vector", "time-series", "spatial", "text", "blob",
    "object-store", "file-store", "block-store", "in-memory", "cache",
    "session", "cookie", "token", "api-key", "webhook", "cron",
    "scheduler", "workflow", "orchestration", "pipeline", "dag", "seed",
    "fixture", "mock", "stub", "fake", "snapshot", "diff", "changelog",
    "version", "release", "deploy", "rollback", "canary",
    "blue-green", "feature-flag", "experiment", "ab-test",
    "load-test", "stress-test", "chaos", "fuzz", "property-based",
    "mutation", "coverage", "tdd", "bdd", "ddt", "atdd", "unit",
    "integration", "e2e", "contract", "visual", "accessibility",
    "soak", "spike", "exploratory", "regression", "smoke", "sanity",
    "acceptance", "uat", "alpha", "beta", "rc", "lts", "nightly",
    "stable", "deprecated", "experimental", "internal", "public",
    "private", "ga", "preview", "draft", "archived", "active",
    "inactive", "eol",
}

# Sort longest-first so multi-word/hyphenated tags win over their prefixes.
_DOMAIN_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(d) for d in sorted(DOMAINS, key=len, reverse=True)) + r")\b"
)


def match_domains(text: str) -> list[str]:
    """Return known domain tags found as whole words in text (deduped)."""
    if not text:
        return []
    found = _DOMAIN_PATTERN.findall(text.lower())
    return sorted(set(found))


def get_connection(db_path: Path | str = CATALOG_DB) -> sqlite3.Connection:
    """Open (creating if needed) the catalog DB and ensure schema exists."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    return conn


def write_marketplace(conn: sqlite3.Connection, name: str, description: str = "") -> None:
    """Insert a marketplace, or update its description if it already exists."""
    conn.execute(
        "INSERT INTO marketplaces (name, description) VALUES (?, ?) "
        "ON CONFLICT(name) DO UPDATE SET description=excluded.description",
        (name, description),
    )


def write_plugin(
    conn: sqlite3.Connection, marketplace: str, name: str, description: str = ""
) -> int:
    """Insert a plugin and return its id; reuse the existing row on conflict."""
    conn.execute(
        "INSERT INTO plugins (marketplace, name, description) VALUES (?, ?, ?) "
        "ON CONFLICT DO NOTHING",
        (marketplace, name, description),
    )
    row = conn.execute(
        "SELECT id FROM plugins WHERE marketplace = ? AND name = ?",
        (marketplace, name),
    ).fetchone()
    assert row is not None
    return int(row[0])


def write_capability(
    conn: sqlite3.Connection,
    marketplace: str,
    plugin_id: int | None,
    type: str,
    name: str,
    description: str = "",
    domains: str = "",
) -> None:
    """Insert a capability; silently skip duplicates of (type, name)."""
    if type not in ("skill", "command", "agent"):
        raise ValueError(f"invalid capability type: {type}")
    conn.execute(
        "INSERT OR IGNORE INTO capabilities "
        "(plugin_id, marketplace, type, name, description, domains) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (plugin_id, marketplace, type, name, description, domains),
    )


def finalize_refresh(conn: sqlite3.Connection, source_mtime: float) -> None:
    """Stamp refresh metadata and commit the transaction."""
    conn.execute(
        "INSERT INTO metadata (key, value) VALUES ('generated_at', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(time.time()),),
    )
    conn.execute(
        "INSERT INTO metadata (key, value) VALUES ('source_mtime', ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (str(source_mtime),),
    )
    conn.commit()


def get_db_mtime(db_path: Path | str = CATALOG_DB) -> float | None:
    """Return the DB file mtime, or None if the DB does not exist."""
    try:
        return os.path.getmtime(db_path)
    except OSError:
        return None


def newest_source_mtime(source_dir: Path | str | None = None) -> float | None:
    """Newest mtime under the marketplaces dir (recursive); None if absent."""
    root = Path(source_dir) if source_dir is not None else DEFAULT_SOURCE_DIR
    if not root.is_dir():
        return None
    newest: float | None = None
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            try:
                mtime = os.path.getmtime(Path(dirpath) / filename)
            except OSError:
                continue
            if newest is None or mtime > newest:
                newest = mtime
    return newest


def is_stale(
    db_path: Path | str = CATALOG_DB,
    source_dir: Path | str | None = None,
) -> bool:
    """True when the DB is missing, the source is missing, or source is newer."""
    db_mtime = get_db_mtime(db_path)
    source_mtime = newest_source_mtime(source_dir)
    if db_mtime is None or source_mtime is None:
        return True
    return source_mtime > db_mtime


def query_capabilities(
    conn: sqlite3.Connection,
    domains: str | None = None,
    type: str | None = None,
    marketplace: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Filter capabilities; domains is a comma-separated substring match."""
    sql = (
        "SELECT id, marketplace, plugin_id, type, name, description, domains "
        "FROM capabilities WHERE 1=1"
    )
    params: list[str] = []
    if domains:
        for domain in [d.strip() for d in domains.split(",") if d.strip()]:
            sql += " AND (',' || domains || ',') LIKE ?"
            params.append(f"%,{domain},%")
    if type:
        sql += " AND type = ?"
        params.append(type)
    if marketplace:
        sql += " AND marketplace = ?"
        params.append(marketplace)
    sql += " ORDER BY marketplace, name LIMIT ?"
    params.append(str(limit))
    rows = conn.execute(sql, params).fetchall()
    return [
        {
            "id": row[0],
            "marketplace": row[1],
            "plugin_id": row[2],
            "type": row[3],
            "name": row[4],
            "description": row[5],
            "domains": row[6],
        }
        for row in rows
    ]


if __name__ == "__main__":
    stale = is_stale()
    print(f"catalog DB: {CATALOG_DB}")
    print(f"stale: {stale}")
