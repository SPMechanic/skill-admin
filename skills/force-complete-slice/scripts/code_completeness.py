#!/usr/bin/env python3
"""
Establish whether a slice is CODE COMPLETE.

Code completeness is structural and mechanical: the shape is all there, and it
builds, migrates, boots, and serves. It makes no claim about correctness — that
is VERIFIED, which completion_status.py derives from executed evidence. A slice
is DONE only when it is both.

Why a separate script: completion_status.py is a pure function over data and
never executes anything. Three of these checks must actually run a command, and
mixing a runner into the status derivation is how a claim becomes an assertion.

Checks:
    layers      every layer named in the contract manifest exists on disk
    dependencies every declared dependency is present and itself code complete
    build       the build command exits 0
    migrate     migrations apply against a real database engine
    boot        the start command comes up and a probe URL answers

Usage:
    uv run code_completeness.py --root . --build "npm run build" \
        --migrate "npm run db:migrate" --boot "npm start" --probe http://localhost:3000/health

    # Layers and dependencies from a manifest (both optional):
    #   .audit/<slice>/code.json
    #   {"layers": [{"name": "billing aggregate", "path": "src/domain/billing.ts"}],
    #    "dependencies": [{"name": "student", "root": "../student"}]}

Exit code:
    0 — code complete
    1 — not code complete (the failing checks are named)
    2 — bad invocation
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TIMEOUT = 600


def _run(command: str, cwd: Path) -> tuple[bool, str]:
    """Run a shell command. Returns (ok, tail of output)."""
    try:
        out = subprocess.run(
            command, cwd=cwd, shell=True, capture_output=True, text=True, timeout=TIMEOUT
        )
    except subprocess.TimeoutExpired:
        return False, f"timed out after {TIMEOUT}s"
    except OSError as exc:
        return False, str(exc)
    tail = ((out.stdout or "") + (out.stderr or "")).strip().splitlines()[-2:]
    return out.returncode == 0, f"exit {out.returncode}: " + " | ".join(tail)


def check_layers(root: Path, layers: list[dict]) -> dict:
    missing = [
        layer.get("name", "?")
        for layer in layers
        if not (root / str(layer.get("path", ""))).exists()
    ]
    if not layers:
        return {"ok": None, "detail": "no layer manifest — layer presence not checked"}
    checked = ", ".join(layer.get("name", "?") for layer in layers)
    return {
        "ok": not missing,
        "detail": (
            f"all layers present (checked: {checked})"
            if not missing
            else f"missing: {', '.join(missing)} (checked: {checked})"
        ),
    }


def check_dependencies(root: Path, deps: list[dict]) -> dict:
    if not deps:
        return {"ok": None, "detail": "no dependency manifest — resolution not checked"}
    problems = []
    for dep in deps:
        name = dep.get("name", "?")
        dep_root = (root / str(dep.get("root", ""))).resolve()
        if not dep_root.is_dir():
            problems.append(f"{name} (absent)")
            continue
        # Transitive: a dependency that is itself incomplete is not resolved.
        if dep.get("code_complete") is False:
            problems.append(f"{name} (not code complete)")
    return {
        "ok": not problems,
        "detail": "all dependencies resolved" if not problems else "unresolved: " + ", ".join(problems),
    }


def probe(url: str, attempts: int = 30, delay: float = 1.0) -> dict:
    for _ in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return {"ok": 200 <= resp.status < 400, "detail": f"HTTP {resp.status}"}
        except urllib.error.HTTPError as exc:
            return {"ok": 200 <= exc.code < 400, "detail": f"HTTP {exc.code}"}
        except (urllib.error.URLError, OSError):
            time.sleep(delay)
    return {"ok": False, "detail": f"no response from {url} after {attempts}s"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Establish code completeness for a slice.")
    parser.add_argument("--root", required=True, help="slice root directory")
    parser.add_argument("--build", help="build command")
    parser.add_argument("--migrate", help="migrate command (must target a real database)")
    parser.add_argument("--boot", help="start command, run in the background")
    parser.add_argument("--probe", help="URL that must answer once the server is up")
    parser.add_argument("--slice", dest="slug", help="slice slug; reads .audit/<slug>/code.json")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    root = Path(args.root)
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    if bool(args.boot) != bool(args.probe):
        print("error: --boot and --probe must be given together", file=sys.stderr)
        return 2

    manifest = {}
    if args.slug:
        path = root / ".audit" / args.slug / "code.json"
        if path.is_file():
            try:
                manifest = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(f"error: {path}: {exc}", file=sys.stderr)
                return 2

    results = {
        "layers": check_layers(root, manifest.get("layers", [])),
        "dependencies": check_dependencies(root, manifest.get("dependencies", [])),
    }
    for name, command in (("build", args.build), ("migrate", args.migrate)):
        if command:
            ok, detail = _run(command, root)
            results[name] = {"ok": ok, "detail": detail}
        else:
            results[name] = {"ok": None, "detail": f"no --{name} command supplied"}

    if args.boot and args.probe:
        server = subprocess.Popen(
            args.boot, cwd=root, shell=True,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            results["boot"] = probe(args.probe)
        finally:
            server.terminate()
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                server.kill()
    else:
        results["boot"] = {"ok": None, "detail": "no --boot/--probe supplied"}

    complete = all(v["ok"] is True for v in results.values())
    unchecked = [k for k, v in results.items() if v["ok"] is None]

    if args.json:
        print(json.dumps(
            {"code_complete": complete, "checks": results, "unchecked": unchecked}, indent=2
        ))
    else:
        print(f"CODE COMPLETE: {'yes' if complete else 'no'}")
        for name, r in results.items():
            mark = "ok" if r["ok"] is True else ("NOT CHECKED" if r["ok"] is None else "FAIL")
            print(f"  {name}: {mark} — {r['detail']}")
        if unchecked:
            print(
                f"\n{len(unchecked)} check(s) not run: {', '.join(unchecked)}. "
                "An unchecked requirement is not satisfied, so this is not code complete."
            )
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
