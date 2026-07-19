"""cli.py — wires ``scan -> plan -> destinations`` into three schema-conformant artifacts written
to a required, target-external ``--out`` directory (ADOPT-01/02/03, D-11).

``python -m tools.adoption_scan --target <dir> --out <dir>`` is the module entrypoint
(``__main__.py``). Never mutates ``--target``: the pipeline underneath is fully read-only (proven
by ``tools/adoption_scan/tests/test_readonly.py``, Plan 02). ``--out`` has NO default (D-11) — an
adoption scanner that silently wrote inside the scanned target, or defaulted to one, could see its
own prior output as target content on a second run (26-RESEARCH.md Pitfall 9); refusing outright
when ``--out`` would resolve inside, equal to, or an ancestor containing ``--target`` closes that
hole structurally rather than relying on convention.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.adoption_scan import destinations, plan, scan

# cli.py -> adoption_scan -> tools -> repo root (parents[2]).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _REPO_ROOT / "contracts" / "harness" / "adoption"

_ARTIFACTS: tuple[str, ...] = ("inventory", "plan", "manifest")


def _load_schema(name: str) -> dict:
    path = _SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _overlaps(target_resolved: Path, out_resolved: Path) -> bool:
    """True iff ``out_resolved`` would let a scan see its own prior output as target content:
    equal, ``--out`` inside ``--target``, or ``--target`` inside ``--out`` (D-11)."""
    return (
        target_resolved == out_resolved
        or target_resolved in out_resolved.parents
        or out_resolved in target_resolved.parents
    )


def main(argv: list[str] | None = None) -> int:
    """CLI: run the full adoption pipeline (``python -m tools.adoption_scan``)."""
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(prog="tools.adoption_scan")
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-file-bytes", type=int, default=scan.DEFAULT_MAX_FILE_BYTES)
    args = parser.parse_args(argv)

    target_resolved = args.target.resolve()
    if not target_resolved.is_dir():
        print(
            f"adoption_scan: --target is not an existing directory: {args.target}", file=sys.stderr
        )
        return 2

    out_resolved = args.out.resolve()
    if _overlaps(target_resolved, out_resolved):
        print(
            "adoption_scan: --out must not resolve inside, equal to, or containing --target "
            f"(target={target_resolved}, out={out_resolved})",
            file=sys.stderr,
        )
        return 2

    inventory = scan.build_inventory(target_resolved, max_bytes=args.max_file_bytes)
    plan_doc = plan.build_plan(inventory)
    # CR-01: "proposed" content is what the HARNESS TEMPLATE would install at a destination — the
    # harness's own checkout, never the scanned target's own content (a target file must never be
    # compared against itself).
    proposed_hashes = destinations.harness_proposed_hashes()
    manifest_doc = destinations.build_manifest(inventory, target_resolved, proposed_hashes)

    documents = {"inventory": inventory, "plan": plan_doc, "manifest": manifest_doc}

    for name, document in documents.items():
        schema = _load_schema(name)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(document), key=lambda item: list(item.path)
        )
        if errors:
            first = errors[0]
            print(
                f"adoption_scan: {name}.json failed schema validation: {first.message}",
                file=sys.stderr,
            )
            return 1

    out_resolved.mkdir(parents=True, exist_ok=True)
    for name in _ARTIFACTS:
        out_path = out_resolved / f"{name}.json"
        out_path.write_bytes(scan._dump(documents[name]))
        print(f"wrote {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
