#!/usr/bin/env python3
"""
Derive an honest completion status from per-check results.

The input file is data, not instructions. This script applies the rules in
references/verification-matrix.md and refuses to derive PASS from a check that
did not execute, or from a coverage claim the user asserts but cannot support.

Check object:
    {
      "id": "AC-1",
      "applies": true,              # false -> NOT APPLICABLE, requires reason
      "status": "pass",             # pass | fail | partial | blocked | not_run | not_applicable
      "provenance": "executed",     # executed | ci | formal | working-tree | head | inferred
      "kind": "test",               # optional: test|build|lint|migration|browser|
                                    #           authorization|integration|deployment|
                                    #           ci|manual
      "tests_collected": 12,        # optional, test checks only
      "tests_skipped": 3,           # optional, test checks only
      "depends_on": [],             # optional: ids that must not be FAIL/BLOCKED
      "requires_multinode": false,  # optional claim about topology
      "formal_property": "...",     # required when provenance is formal
      "evidence": "..."             # optional free text
    }

Usage:
    uv run skills/force-complete-slice/scripts/completion_status.py results.json
    uv run skills/force-complete-slice/scripts/completion_status.py --input results.json --json

Input may be a bare list of checks or an object with a "checks" key. An object
may also carry {"all_coverage_exists": true|false} for the second claim; when
absent, that claim is reported as unknown rather than assumed.

An object may also carry "contract": a list of criterion ids from the
completion contract. When present, every id must appear in the checks: a
criterion that is absent from results.json is reported as a check with status
NOT RUN and a note saying it was dropped from the results, because omitting
an inconvenient criterion must never read as clean.

An object may also carry {"code_complete": true|false}, the verdict from
code_completeness.py. Code completeness is a gate: when it is false, no check
may hold PASS, because the slice's shape is not all there and a passing subset
of an incomplete slice is not a pass. When the key is absent the gate does not
apply — that keeps a bare check list usable on its own — but the slice then
cannot be reported DONE, and code_completeness.py is what establishes the
state.

Exit code:
    0 — derived a status (even if that status is FAIL or BLOCKED)
    2 — input unreadable or malformed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

VALID_STATUS = {
    "pass", "partial", "fail", "blocked", "not_run", "not_applicable",
    "not applicable", "not run",
}

NORMALISE = {
    "pass": "PASS",
    "partial": "PARTIAL",
    "fail": "FAIL",
    "blocked": "BLOCKED",
    "not_run": "NOT RUN",
    "not run": "NOT RUN",
    "not_applicable": "NOT APPLICABLE",
    "not applicable": "NOT APPLICABLE",
}

# Checks whose execution has to reach the real thing, not a substitute.
REAL_EVIDENCE_KINDS = {"integration", "browser", "deployment", "migration"}

# Provenance the matrix defines. Anything else is not a stronger claim than
# `inferred` — it is an unrecognised one, and unrecognised must not pass.
VALID_PROVENANCE = {"executed", "ci", "formal", "working-tree", "head", "inferred"}

# Kinds for which a skipped or zero-test run is evidence of nothing.
TEST_KINDS = {"test", "integration", "browser", "migration"}


def _as_count(cid: str, value, field: str):
    """Coerce a test count. Strings and negatives are rejected, not ignored:
    `"0"` and `-1` must not slip past the zero-test guard."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"check {cid}: '{field}' must be an integer, got {value!r}")
    if value < 0:
        raise ValueError(f"check {cid}: '{field}' must not be negative, got {value}")
    return value


def _as_check(item: dict, index: int) -> dict:
    if not isinstance(item, dict):
        raise ValueError(f"check {index} is not an object")
    cid = item.get("id")
    if not isinstance(cid, str) or not cid.strip():
        raise ValueError(f"check {index} missing a non-empty 'id'")

    raw_status = item.get("status", "not_run")
    key = str(raw_status).strip().lower().replace("-", "_")
    if key not in VALID_STATUS:
        raise ValueError(f"check {cid}: unknown status {raw_status!r}")

    applies = item.get("applies", True)
    if not isinstance(applies, bool):
        raise ValueError(f"check {cid}: 'applies' must be a boolean")

    reported = NORMALISE[key] if applies else "NOT APPLICABLE"

    return {
        "id": cid,
        "requested_applies": applies,
        # Derived, not consumed: a NOT APPLICABLE row that loses its reason is
        # re-classified as applicable by apply_rules, and must then count.
        "applies": reported != "NOT APPLICABLE",
        # The status as reported, before applies:false rewrote it. A FAIL or
        # BLOCKED must never vanish into NOT APPLICABLE, so apply_rules reads
        # this to reject the demotion.
        "reported_status": reported,
        "original_status": NORMALISE[key],
        "status": reported,
        "provenance": str(item.get("provenance", "inferred")).strip().lower(),
        "kind": str(item.get("kind", "")).strip().lower(),
        "tests_collected": _as_count(cid, item.get("tests_collected"), "tests_collected"),
        "tests_skipped": _as_count(cid, item.get("tests_skipped"), "tests_skipped"),
        "depends_on": list(item.get("depends_on") or []),
        "requires_multinode": bool(item.get("requires_multinode", False)),
        "topology": str(item.get("topology", "single-node")).strip().lower(),
        "reason": item.get("reason"),
        "evidence": item.get("evidence"),
        "formal_property": item.get("formal_property"),
        "notes": [],
    }


SEVERITY = {
    "PASS": 0,
    "PARTIAL": 1,
    "NOT RUN": 2,
    "BLOCKED": 3,
    "FAIL": 4,
}


def downgrade(check: dict, status: str, note: str) -> None:
    """Apply a rule-mandated downgrade. Never used to upgrade a status."""
    current = check["status"]
    if current == "NOT APPLICABLE" or SEVERITY.get(status, 0) >= SEVERITY.get(current, 0):
        check["status"] = status
        check["notes"].append(note)


def apply_rules(check: dict, by_id: dict) -> None:
    """Enforce the invalid-combination table. Downgrades only, never upgrades."""
    status = check["status"]

    # A check whose dependency failed or is blocked cannot itself have passed:
    # the dependency was not in place when it ran, so whatever it observed was
    # observed against the wrong tree.
    if status == "PASS":
        for dep_id in check["depends_on"]:
            if dep_id == check["id"]:
                downgrade(check, "PARTIAL", "check depends on itself")
                break
            dep = by_id.get(dep_id)
            if dep is None:
                downgrade(
                    check,
                    "PARTIAL",
                    f"dependency {dep_id!r} is not in this contract — "
                    "a PASS against an unverifiable dependency is unverifiable",
                )
                break
            if dep["status"] in ("FAIL", "BLOCKED", "PARTIAL", "NOT RUN"):
                downgrade(
                    check,
                    "PARTIAL",
                    f"dependency {dep_id} is {dep['status']} — this check cannot "
                    "pass while a prerequisite is unmet",
                )
                break

    if status == "NOT APPLICABLE":
        # A FAIL or BLOCKED cannot be demoted into a non-applicable row: that
        # erases the one piece of evidence a reader most needs.
        if check["original_status"] in ("FAIL", "BLOCKED"):
            check["applies"] = True
            check["status"] = check["original_status"]
            check["notes"].append(
                f"reported {check['original_status']} then marked not applicable — "
                "a failing or blocked check cannot be removed by asserting it does not apply"
            )
            return
        if not (isinstance(check["reason"], str) and check["reason"].strip()):
            check["applies"] = True
            downgrade(
                check,
                "PARTIAL",
                "marked not applicable without a reason — contract incomplete",
            )
        return

    # An unrecognised provenance is not a stronger claim than `inferred`.
    if status == "PASS" and check["provenance"] not in VALID_PROVENANCE:
        downgrade(
            check,
            "PARTIAL",
            f"unknown provenance {check['provenance']!r} — not one of "
            f"{sorted(VALID_PROVENANCE)}",
        )

    # Nothing ran: no status other than NOT RUN or NOT APPLICABLE is defensible.
    if status == "PASS" and check["provenance"] == "inferred":
        downgrade(check, "PARTIAL", "PASS claimed from inferred evidence (nothing executed)")

    # A proof outranks a run, but only if a reviewer can read what was proved.
    if check["status"] == "PASS" and check["provenance"] == "formal":
        prop = check["formal_property"]
        if not (isinstance(prop, str) and len(prop.strip()) >= 20 and " " in prop.strip()):
            downgrade(
                check,
                "PARTIAL",
                "formal provenance needs the proved property stated as a readable "
                "sentence (>=20 chars, multiple words), not a bare label",
            )

    if check["kind"] in TEST_KINDS:
        collected = check["tests_collected"]
        skipped = check["tests_skipped"] or 0
        # An unstated count means the zero-test rule below cannot run, so a PASS
        # cannot be defended either.
        if collected is None and check["status"] == "PASS":
            downgrade(
                check,
                "PARTIAL",
                "test check reported no 'tests_collected' — the empty-suite guard "
                "cannot be applied, so the count is part of the evidence",
            )
        # An empty suite is never evidence of success.
        elif collected == 0 and check["status"] in ("PASS", "PARTIAL"):
            downgrade(
                check,
                "NOT RUN",
                "test suite collected zero tests — never evidence of success",
            )
        # Nor is a suite whose every test was skipped: same zero useful signal.
        elif collected and skipped >= collected and check["status"] == "PASS":
            downgrade(
                check,
                "NOT RUN",
                f"every collected test was skipped ({skipped}/{collected}) — "
                "a skipped test is not a pass",
            )
        # A partly-skipped suite still ran something, so it is evidence — but
        # weaker than an unqualified pass, and the gap must not read as clean.
        elif skipped > 0 and check["status"] == "PASS":
            downgrade(
                check,
                "PARTIAL",
                f"{skipped} of {collected} collected tests were skipped",
            )

    if check["status"] == "PASS" and check["kind"] in REAL_EVIDENCE_KINDS:
        evidence = (check["evidence"] or "").lower()
        for marker in (
            "mock",
            "stub",
            "fake",
            "in-memory",
            "in memory",
            "test double",
            "simulator",
            "sandbox",
        ):
            if marker in evidence:
                downgrade(
                    check,
                    "PARTIAL",
                    f"{check['kind']} criterion backed by a substitute ({marker!r})",
                )
                break

    # A browser gate needs a browser. A unit test exercises a different failure
    # surface, so it cannot stand in for one (matrix: "PASS for a browser
    # criterion backed by a unit test" -> NOT RUN).
    if check["status"] == "PASS" and check["kind"] == "browser":
        evidence = (check["evidence"] or "").lower()
        browser = ("playwright", "cypress", "selenium", "browser", "e2e", "puppeteer")
        unit = ("unit test", "pytest", "vitest", "jest", "junit", "rspec", "go test")
        if any(m in evidence for m in unit) and not any(m in evidence for m in browser):
            downgrade(
                check,
                "NOT RUN",
                "browser criterion backed by a unit test — a different failure "
                "surface, so the browser behavior is unverified",
            )

    # A disabled-but-green test is the classic false green.
    if check["status"] == "PASS":
        evidence = (check["evidence"] or "").lower()
        for marker in ("xfail", "expected failure", "quarantine"):
            if marker in evidence:
                downgrade(
                    check,
                    "PARTIAL",
                    f"evidence mentions {marker!r} — an expected failure is not a pass",
                )
                break

    # Topology is a property of the run, not of the check's optimism. A
    # criterion that only means something on a cluster needs cluster evidence.
    if check["requires_multinode"] and check["topology"] != "multi-node":
        downgrade(
            check,
            "PARTIAL",
            "multi-node criterion not evidenced by a multi-node run "
            f"(topology: {check['topology']})",
        )

    if check["status"] == "PASS" and check["kind"] == "ci" and check["provenance"] == "working-tree":
        downgrade(check, "PARTIAL", "working-tree state is not a CI result")


def _reconcile_contract(checks: list[dict], contract) -> list[dict]:
    """Synthesise a NOT RUN check for every contract criterion the results
    omitted. Without this, dropping a criterion is cheaper than clearing it.

    Ids are matched exactly; a contract may carry ids not otherwise referenced.
    """
    if not contract:
        return checks
    seen = {c["id"] for c in checks}
    missing = [cid for cid in contract if isinstance(cid, str) and cid.strip() and cid not in seen]
    out = list(checks)
    for cid in missing:
        out.append(
            {
                "id": cid,
                "requested_applies": True,
                "applies": True,
                "reported_status": "NOT RUN",
                "original_status": "NOT RUN",
                "status": "NOT RUN",
                "provenance": "inferred",
                "kind": "",
                "tests_collected": None,
                "tests_skipped": None,
                "depends_on": [],
                "requires_multinode": False,
                "topology": "single-node",
                "reason": None,
                "evidence": None,
                "formal_property": None,
                "notes": [
                    "criterion is in the completion contract but absent from the "
                    "results — an omitted criterion is unverified, never satisfied"
                ],
            }
        )
    return out


# Layers whose presence proves a slice has a real domain behind its UI.
BACKEND_LAYERS = {
    "domain", "persistence", "repository", "service", "api", "backend",
    "contract", "migration", "event", "read-model", "integration",
}
# Layers that describe presentation only.
PRESENTATION_LAYERS = {"ui", "frontend", "view", "component", "page", "mockup", "shell"}


def _hollow_warning(checks: list[dict]) -> str | None:
    """A contract with presentation criteria and no backend criterion is the
    signature of a hollow slice. Detection is a paragraph elsewhere; this makes
    it visible in the report even when an agent skipped the prose."""
    size = len(checks)
    if size == 0 or size > 16:
        return None
    kinds = [c["kind"] for c in checks if c["kind"]]
    if not kinds:
        return None
    has_presentation = any(k in PRESENTATION_LAYERS for k in kinds)
    has_backend = any(k in BACKEND_LAYERS for k in kinds)
    if has_presentation and not has_backend:
        return (
            "contract has presentation criteria and no backend/domain criterion — "
            "this looks like a hollow slice; derive a design contract (ports, "
            "events, read models) before implementation criteria"
        )
    return None


def derive(checks: list[dict], coverage_exists, code_complete=None) -> dict:
    by_id = {c["id"]: c for c in checks}
    # Dependencies can chain (AC-3 -> AC-2 -> AC-1), so one pass is not enough:
    # iterate to a fixed point. Bounded by the number of checks, since every
    # round either downgrades something or stops.
    for _ in range(len(checks) + 1):
        before = {c["id"]: c["status"] for c in checks}
        for c in checks:
            apply_rules(c, by_id)
        if all(c["status"] == before[c["id"]] for c in checks):
            break

    blocking = [c for c in checks if c["status"] == "FAIL" and c["applies"]]
    blocked = [c for c in checks if c["status"] == "BLOCKED" and c["applies"]]
    not_run = [c for c in checks if c["status"] == "NOT RUN" and c["applies"]]
    partial = [c for c in checks if c["status"] == "PARTIAL" and c["applies"]]
    applicable = [c for c in checks if c["applies"]]
    passed = [c for c in checks if c["status"] == "PASS"]

    if blocking:
        overall = "FAIL"
    elif blocked:
        overall = "BLOCKED"
    elif not_run:
        overall = "NOT RUN"
    elif partial:
        overall = "PARTIAL"
    elif not passed:
        overall = "NOT APPLICABLE"
    elif all(c["status"] == "PASS" for c in applicable):
        overall = "PASS"
    else:
        overall = "PARTIAL"

    # Coverage is a separate claim. A green check set does not imply it.
    if coverage_exists is True:
        coverage = "yes"
    elif coverage_exists is False:
        coverage = "no"
    else:
        coverage = "unknown"

    if overall == "PASS" and coverage != "yes":
        overall = "PARTIAL"

    # Code completeness is a gate, not an axis. A passing subset of a slice
    # whose layers do not all exist is not a pass: the criteria that would
    # have failed are the ones never written. Only an explicit false gates —
    # omitting the key means the caller is not using the gate, so it does not
    # silently rewrite every existing all-green result.
    if code_complete is False:
        for c in checks:
            if c["status"] == "PASS":
                c["status"] = "PARTIAL"
                c["notes"].append(
                    "slice is not code complete — a passing check does not "
                    "establish a pass over an incomplete slice"
                )
        if overall in ("PASS", "PARTIAL"):
            overall = "PARTIAL"

    # Every applicable check passed. Computed over the applicable subset, not
    # over every row: a reasoned NOT APPLICABLE is not a failure to pass.
    claim_one = (
        "yes" if (applicable and all(c["status"] == "PASS" for c in applicable)) else "no"
    )

    skipped_detail = [
        {
            "id": c["id"],
            "collected": c["tests_collected"],
            "skipped": c["tests_skipped"],
        }
        for c in checks
        if c["kind"] == "test" and (c["tests_skipped"] or 0) > 0
    ]

    return {
        "overall": overall,
        "code_complete": code_complete,
        "claim_all_applicable_checks_passed": claim_one,
        "claim_all_intended_coverage_exists": coverage,
        "counts": {
            "total": len(checks),
            "applicable": len(applicable),
            "pass": sum(1 for c in checks if c["status"] == "PASS"),
            "partial": sum(1 for c in checks if c["status"] == "PARTIAL"),
            "fail": len(blocking),
            "blocked": len(blocked),
            "not_run": len(not_run),
            "not_applicable": sum(1 for c in checks if c["status"] == "NOT APPLICABLE"),
        },
        "checks": checks,
        "skipped_tests": skipped_detail,
        "hollow_warning": _hollow_warning(checks),
        "unresolved": [
            {"id": c["id"], "status": c["status"], "reason": c["notes"] or [c.get("reason") or c.get("evidence") or ""]}
            for c in checks
            if c["status"] in ("FAIL", "BLOCKED", "NOT RUN", "PARTIAL")
        ],
    }


def load_input(path: Path) -> tuple[list[dict], object, list, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    contract = None
    code_complete = None
    if isinstance(data, list):
        raw_checks, coverage = data, None
    elif isinstance(data, dict):
        raw_checks = data.get("checks")
        coverage = data.get("all_coverage_exists")
        contract = data.get("contract")
        code_complete = data.get("code_complete")
        if code_complete is not None and not isinstance(code_complete, bool):
            raise ValueError("'code_complete' must be a boolean")
        if contract is not None and (
            not isinstance(contract, list) or not all(isinstance(i, str) for i in contract)
        ):
            raise ValueError("'contract' must be a list of criterion id strings")
        if not isinstance(raw_checks, list):
            raise ValueError("object input must carry a 'checks' array")
    else:
        raise ValueError("input must be a list of checks or an object with 'checks'")
    checks = [_as_check(item, i) for i, item in enumerate(raw_checks)]
    return _reconcile_contract(checks, contract), coverage, contract, code_complete


def render_text(result: dict) -> str:
    lines = [f"overall: {result['overall']}"]
    lines.append(f"claim 1 — all applicable checks passed: {result['claim_all_applicable_checks_passed']}")
    lines.append(f"claim 2 — all intended coverage exists: {result['claim_all_intended_coverage_exists']}")
    cc = result.get("code_complete")
    lines.append(f"code complete: {'yes' if cc is True else ('no' if cc is False else 'not stated')}")
    lines.append("")
    for c in result["checks"]:
        lines.append(f"  {c['id']}: {c['status']} ({c['provenance']})")
        for note in c["notes"]:
            lines.append(f"      - {note}")
    counts = result["counts"]
    lines.append("")
    lines.append(
        "counts: "
        + ", ".join(f"{k}={v}" for k, v in counts.items() if k != "total")
        + f", total={counts['total']}"
    )
    return "\n".join(lines)


def write_audit(result: dict, root: Path, slice_slug: str, contract: list | None) -> Path:
    """Persist the contract and status so a later session — or the orchestrator —
    can read what this run found. The orchestrator classifies slices from these
    files; nothing else writes them, so without this the .audit convention can
    never be satisfied by this plugin.

    Row order follows the contract when one was given, then any remaining checks.
    """
    audit_dir = root / ".audit" / slice_slug
    audit_dir.mkdir(parents=True, exist_ok=True)

    by_id = {c["id"]: c for c in result["checks"]}
    ordered: list[str] = []
    for cid in contract or []:
        if cid in by_id and cid not in ordered:
            ordered.append(cid)
    for c in result["checks"]:
        if c["id"] not in ordered:
            ordered.append(c["id"])

    lines = [
        "criterion\tlayer\tstatus\tprovenance\tevidence",
        *(
            "\t".join(
                _tsv(
                    by_id[cid]["id"],
                    by_id[cid]["kind"],
                    by_id[cid]["status"],
                    by_id[cid]["provenance"],
                    (by_id[cid]["evidence"] or "").replace("\n", " "),
                )
            )
            for cid in ordered
        ),
    ]
    (audit_dir / "acceptance.tsv").write_text("\n".join(lines) + "\n", encoding="utf-8")

    (audit_dir / "status.json").write_text(
        json.dumps(
            {
                "slice": slice_slug,
                "overall": result["overall"],
                "claims": {
                    "all_applicable_checks_passed": result["claim_all_applicable_checks_passed"],
                    "all_intended_coverage_exists": result["claim_all_intended_coverage_exists"],
                },
                "counts": result["counts"],
                "hollow_warning": result.get("hollow_warning"),
                "checks": [
                    {"id": c["id"], "status": c["status"], "provenance": c["provenance"], "notes": c["notes"]}
                    for c in result["checks"]
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return audit_dir


def _tsv(*cells: str) -> list[str]:
    return [str(c).replace("\t", " ").replace("\r", " ").replace("\n", " ") for c in cells]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Derive completion status from check results.")
    parser.add_argument("input", nargs="?", help="path to results JSON")
    parser.add_argument("--input", dest="input_opt", help="path to results JSON")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--audit-root",
        help="write .audit/<slice>/acceptance.tsv and status.json under this root",
    )
    parser.add_argument("--slice", dest="slice_slug", help="slice slug for the .audit directory")
    args = parser.parse_args(argv)

    raw_path = args.input_opt or args.input
    if not raw_path:
        print("error: no input file given", file=sys.stderr)
        return 2
    if bool(args.audit_root) != bool(args.slice_slug):
        print("error: --audit-root and --slice must be given together", file=sys.stderr)
        return 2

    try:
        checks, coverage, contract, code_complete = load_input(Path(raw_path))
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = derive(checks, coverage, code_complete)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(render_text(result))

    if result.get("hollow_warning"):
        print(
            f"\nwarning: {result['hollow_warning']}",
            file=sys.stderr,
        )

    if args.audit_root:
        written = write_audit(result, Path(args.audit_root), args.slice_slug, contract)
        print(f"\naudit written: {written}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
