#!/usr/bin/env python3
"""Idempotent off-plane applier for the MONO-12 `update` disposition + `installed[]` array.

`contracts/harness/adoption/manifest.schema.json` is on the constitution plane
(`tools/hooks/contract_guard.py`'s `CONSTITUTION_GLOBS`), which denies agent Write/Edit unless a
human has set `GOLDEN_APPROVE_HUMAN`. This script is the human-run vehicle for the one sanctioned
edit (Phase 53 plan 01, task 1 authors it / task 2 runs it): it appends exactly one value —
`update` — to `$defs.dispositionEnum.enum`, rewrites that enum's `description`, adds
`$defs.installedRecord`, and adds ONE optional top-level `installed[]` array — then re-derives
the committed hash baseline via the SHIPPED `tools.contract_hash.hash` module (never
re-implementing JCS hashing). Modeled line-for-line on the Phase 52 precedent,
`.planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py`.

Two modes:
  --check (default)  Write nothing. Verify the current schema is either the exact expected
                      pre-state or already carries the new shape (idempotent no-op), and report
                      which. Exits 2 on any other shape — this script never "repairs" a surprise.
  --write             Perform the edit (only if the pre-state matches) and rebaseline
                      `contracts/.hashes/manifest.json` in the same invocation. Re-running
                      --write after a successful run is a no-op and exits 0.

Usage (from repo root, human-run only), where SCRIPT is
.planning/phases/53-managed-adopt-updates/scripts/apply-manifest-update-enum.py:
    uv run python "$SCRIPT" --check
    GOLDEN_APPROVE_HUMAN=1 uv run python "$SCRIPT" --write
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# scripts/ -> 53-managed-adopt-updates/ -> phases/ -> .planning/ -> repo root
REPO_ROOT = Path(__file__).resolve().parents[4]
SCHEMA_PATH = REPO_ROOT / "contracts" / "harness" / "adoption" / "manifest.schema.json"

# The exact 6-value pre-state named in 53-01-PLAN.md <interfaces> — semantically ordered, not
# sorted. This script refuses (exit 2) on any other shape rather than guessing a repair.
EXPECTED_ENUM: list[str] = [
    "create",
    "preserve",
    "conflict",
    "marker-merge",
    "derived-regenerate",
    "human-ratification-required",
]
EXPECTED_DESCRIPTION = "Exactly these 6 values (D-03/D-04's total rule chain), no more, no fewer."
NEW_VALUE = "update"
NEW_DESCRIPTION = (
    "Exactly these 7 values, no more, no fewer: D-03/D-04's total rule chain plus MONO-12's "
    "`update` — fired when the target's current hash equals the recorded installed_sha256 AND "
    "the recomputed harness payload hash now differs (a harness-side move, not a target-side "
    "edit)."
)


def _load_schema(path: Path) -> dict:
    return json.loads(path.read_bytes())


def _disposition_enum_node(schema: dict) -> dict:
    return schema["$defs"]["dispositionEnum"]


def check_state(schema: dict) -> str:
    """Return "pre" (expected 6-value pre-state) or "post" (already carries the new shape).

    Exits 2 — refusing to guess a repair — on any other shape.
    """
    node = _disposition_enum_node(schema)
    enum = node.get("enum")
    description = node.get("description")
    defs = schema.get("$defs", {})
    properties = schema.get("properties", {})

    is_pre = (
        enum == EXPECTED_ENUM
        and description == EXPECTED_DESCRIPTION
        and "installedRecord" not in defs
        and "installed" not in properties
    )
    if is_pre:
        return "pre"

    is_post = (
        enum == EXPECTED_ENUM + [NEW_VALUE]
        and "installedRecord" in defs
        and "installed" in properties
    )
    if is_post:
        return "post"

    print(
        "apply-manifest-update-enum: unexpected manifest.schema.json shape — refusing to guess "
        f"a repair. dispositionEnum.enum={enum!r} description={description!r} "
        f"$defs={sorted(defs)!r} properties={sorted(properties)!r}",
        file=sys.stderr,
    )
    sys.exit(2)


def apply_edit(schema: dict) -> dict:
    """Mutate ``schema`` in place with exactly the four sanctioned mutations. Returns ``schema``."""
    disposition_enum = _disposition_enum_node(schema)
    disposition_enum["enum"] = list(EXPECTED_ENUM) + [NEW_VALUE]
    disposition_enum["description"] = NEW_DESCRIPTION

    # Copied verbatim from dispositionRecord.properties.destination.pattern at runtime — never
    # retyped by hand into a different form.
    destination_pattern = schema["$defs"]["dispositionRecord"]["properties"]["destination"][
        "pattern"
    ]

    installed_record = {
        "type": "object",
        "additionalProperties": False,
        "required": ["destination", "installed_sha256", "batch_id"],
        "properties": {
            "destination": {
                "type": "string",
                "minLength": 1,
                "pattern": destination_pattern,
                "description": (
                    "A repo-relative POSIX path in the TARGET tree that /adopt itself wrote."
                ),
            },
            "installed_sha256": {
                "type": "string",
                "pattern": "^[0-9a-f]{64}$",
                "description": (
                    "sha256 of the bytes /adopt actually wrote at this destination, AS WRITTEN "
                    "(post-splice for harness/project.toml). Exactly one hash is stored: the "
                    "source side is recomputed every run by "
                    "destinations.harness_proposed_hashes(), "
                    "so a second source_sha256 field would only go stale."
                ),
            },
            "batch_id": {
                "type": "string",
                "minLength": 1,
                "description": "The adoption batch that wrote these bytes.",
            },
        },
    }

    # Insert $defs.installedRecord right after excludedDestinationRecord, preserving key order.
    new_defs: dict = {}
    for key, value in schema["$defs"].items():
        new_defs[key] = value
        if key == "excludedDestinationRecord":
            new_defs["installedRecord"] = installed_record
    schema["$defs"] = new_defs

    # Optional top-level array. Never added to `required`; `additionalProperties` stays untouched.
    schema["properties"]["installed"] = {
        "type": "array",
        "items": {"$ref": "#/$defs/installedRecord"},
        "description": (
            "Optional (MONO-12): the installed-file records this manifest's dispositions were "
            "resolved against, copied verbatim from the target's .harness/adoption/installed.json. "
            "Absent on a first-ever adopt and on every Phase-52-era manifest — this array is "
            "never added to `required`, so older documents stay valid."
        ),
    }
    return schema


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="apply-manifest-update-enum.py",
        description=(
            "Human-run off-plane applier: appends the `update` disposition value plus "
            "$defs.installedRecord and the optional installed[] array to manifest.schema.json, "
            "and rebaselines contracts/.hashes/manifest.json."
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
                f"--check: {_rel(SCHEMA_PATH)} would gain enum value {NEW_VALUE!r}, "
                "$defs.installedRecord, and the optional installed[] array (no write performed)."
            )
        else:
            print(
                f"--check: {_rel(SCHEMA_PATH)} already carries {NEW_VALUE!r} and installedRecord "
                "(idempotent no-op — no write performed)."
            )
        return 0

    if state == "post":
        print(
            f"--write: {_rel(SCHEMA_PATH)} already carries {NEW_VALUE!r} and installedRecord — "
            "nothing to do (idempotent)."
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
