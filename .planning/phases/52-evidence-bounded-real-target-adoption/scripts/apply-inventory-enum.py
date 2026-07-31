#!/usr/bin/env python3
"""Idempotent off-plane applier for the OBS-D-01 / D-20 `non-workspace-member` enum value.

`contracts/harness/adoption/inventory.schema.json` is on the constitution plane
(`tools/hooks/contract_guard.py`'s `CONSTITUTION_GLOBS`), which denies agent Write/Edit unless a
human has set `GOLDEN_APPROVE_HUMAN`. This script is the human-run vehicle for that one sanctioned
edit (Phase 52 plan 01, task 2): it appends exactly one value —
`non-workspace-member` — to `$defs.excludedEntry.properties.excluded.enum`, extends that
property's `description` with the OBS-D-01 trace sentence, and then re-derives the committed hash
baseline via the SHIPPED `tools.contract_hash.hash` module (never re-implementing JCS hashing).

Two modes:
  --check (default)  Write nothing. Verify the current schema is either the exact expected
                      pre-state or already carries the new value (idempotent no-op), and report
                      which. Exits 2 on any other shape — this script never "repairs" a surprise.
  --write             Perform the edit (only if the pre-state matches) and rebaseline
                      `contracts/.hashes/manifest.json` in the same invocation. Re-running
                      --write after a successful run is a no-op and exits 0.

Usage (from repo root, human-run only):
    uv run python .planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py --check
    GOLDEN_APPROVE_HUMAN=1 uv run python .planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# scripts/ -> 52-evidence-bounded-real-target-adoption/ -> phases/ -> .planning/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "contracts" / "harness" / "adoption" / "inventory.schema.json"

# The exact 8-value pre-state named in 52-01-PLAN.md <interfaces> — semantically ordered, not
# sorted. This script refuses (exit 2) on any other shape rather than guessing a repair.
EXPECTED_ENUM: list[str] = [
    "secret-path",
    "secret-content",
    "binary",
    "vendored",
    "generated",
    "source-dump",
    "size-capped",
    "symlink-escape",
]
NEW_VALUE = "non-workspace-member"
TRACE_SENTENCE = (
    " OBS-D-01 (51-BASELINE-EVIDENCE.md, purpose 2 / D-20): non-workspace-member records a "
    "manifest found by the walk that lies outside the target's declared pnpm workspace globs "
    "— excluded from the member set, never silently dropped."
)


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _excluded_enum_node(schema: dict) -> dict:
    return schema["$defs"]["excludedEntry"]["properties"]["excluded"]


def check_state(schema: dict) -> str:
    """Return "pre" (expected 8-value pre-state) or "post" (already carries NEW_VALUE).

    Exits 2 — refusing to guess a repair — on any other enum shape.
    """
    node = _excluded_enum_node(schema)
    enum = node["enum"]
    if enum == EXPECTED_ENUM:
        return "pre"
    if enum == EXPECTED_ENUM + [NEW_VALUE]:
        return "post"
    print(
        "apply-inventory-enum: unexpected excludedEntry.excluded enum shape — refusing to "
        f"guess a repair. Found: {enum!r}",
        file=sys.stderr,
    )
    sys.exit(2)


def apply_edit(schema: dict) -> dict:
    """Mutate ``schema`` in place: append NEW_VALUE, extend the description. Returns ``schema``."""
    node = _excluded_enum_node(schema)
    node["enum"] = list(EXPECTED_ENUM) + [NEW_VALUE]
    node["description"] = node["description"] + TRACE_SENTENCE
    return schema


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="apply-inventory-enum.py",
        description=(
            "Human-run off-plane applier: appends the non-workspace-member enum value to "
            "inventory.schema.json and rebaselines contracts/.hashes/manifest.json."
        ),
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Perform the edit + rebaseline. Default is --check (write nothing).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Explicit no-op flag for the default (write-free) mode; --write overrides it.",
    )
    args = parser.parse_args(argv)

    schema = _load_schema(SCHEMA_PATH)
    # Runs in BOTH modes — the pre-state assertion is not gated by --write.
    state = check_state(schema)

    if not args.write:
        if state == "pre":
            print(
                f"--check: {_rel(SCHEMA_PATH)} would gain enum value {NEW_VALUE!r} "
                "(no write performed)."
            )
        else:
            print(
                f"--check: {_rel(SCHEMA_PATH)} already carries {NEW_VALUE!r} "
                "(idempotent no-op — no write performed)."
            )
        return 0

    if state == "post":
        print(
            f"--write: {_rel(SCHEMA_PATH)} already carries {NEW_VALUE!r} — nothing to do "
            "(idempotent)."
        )
        return 0

    # Reuse the shipped JCS SHA-256 hasher — never re-implement canonicalization here.
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    from tools.contract_hash.hash import schema_hash, write_manifest  # noqa: PLC0415

    old_digest = schema_hash(SCHEMA_PATH)
    updated = apply_edit(schema)
    SCHEMA_PATH.write_text(
        json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    new_digest = schema_hash(SCHEMA_PATH)
    print(f"--write: {_rel(SCHEMA_PATH)} old digest: {old_digest}")
    print(f"--write: {_rel(SCHEMA_PATH)} new digest: {new_digest}")

    manifest_path = write_manifest()
    print(f"--write: rebaselined {_rel(manifest_path)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
