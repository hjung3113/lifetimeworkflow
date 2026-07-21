"""cli.py — the argument-routed ``draft``/``apply``/``promote`` dispatcher
``python -m tools.adoption_apply`` needs (``__main__.py``'s ``from tools.adoption_apply.cli import
main``, Plan 27-01's output, has had nothing to import from until this module).

Composition only — this module never re-implements ``tools.adoption_apply``'s own
``batch``/``apply``/``approval`` logic, nor ``tools.adoption_scan``'s scan/plan/manifest logic.
Discovery (``python -m tools.adoption_scan``) stays out of scope here; ``cli.py`` composes only
the ``adoption_apply``-owned half of the lifecycle (``draft``/``apply``/``promote``), per
``harness/commands/adopt.md``'s own sub-verb split.

``draft`` mirrors ``tools.adoption_scan.cli.main``'s EXACT scan -> plan -> manifest wiring order
(``scan.build_inventory`` -> ``plan.build_plan`` -> ``destinations.build_manifest`` over
``destinations.harness_proposed_hashes()``), but resolves ``--out`` to a task-local batch
directory (``create_or_resume_batch``) instead of a bare ``--out`` flag, and confines every write
to that batch root via ``apply.refuse_if_outside_root`` BEFORE writing (ADOPT-05 clause 1, wired
into the real draft path — not only exercised by its own isolated unit test).

``apply`` reads a drafted batch's ``manifest.json`` and applies it against a target root via
``apply.apply_manifest``. The bytes/fenced-block content for a ``create``/``marker-merge``
destination are the HARNESS'S OWN checkout content at that destination (CR-01's "proposed content
is what the harness template would install", already the source of truth
``destinations.harness_proposed_hashes()`` hashes against) — never content read back from the
scanned target itself.

``promote`` mirrors ``tools.golden_runner.approve.py::main``'s EXACT refuse-by-default exit-code
idiom: catch the human-ratification refusal, print, return exit code **3** (D-05).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tools.adoption_apply import apply as apply_module
from tools.adoption_apply.apply import apply_manifest, refuse_if_outside_root
from tools.adoption_apply.approval import (
    AdoptionApprovalRefused,
    check_valid,
)
from tools.adoption_apply.approval import (
    promote as approval_promote,
)
from tools.adoption_apply.batch import create_or_resume_batch
from tools.adoption_scan import destinations, scan
from tools.adoption_scan import plan as plan_mod

# cli.py -> adoption_apply -> tools -> repo root (parents[2]) — same depth as adoption_scan/cli.py.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _REPO_ROOT / "contracts" / "harness" / "adoption"

_DRAFT_ARTIFACTS: tuple[str, ...] = ("inventory", "plan", "manifest")


def _load_schema(name: str) -> dict:
    path = _SCHEMA_DIR / f"{name}.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(name: str, document: dict) -> str | None:
    """Return the first schema-validation error message for *document*, or ``None`` if valid."""
    schema = _load_schema(name)
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document), key=lambda item: list(item.path)
    )
    if not errors:
        return None
    return errors[0].message


def _batch_root(task_dir: Path, batch_id: str) -> Path:
    return Path(task_dir) / "artifacts" / "adoption" / batch_id


def _cmd_draft(args: argparse.Namespace) -> int:
    target = Path(args.target).resolve()
    if not target.is_dir():
        print(
            f"tools.adoption_apply draft: --target is not an existing directory: {args.target}",
            file=sys.stderr,
        )
        return 2

    target_ref = args.target_ref if args.target_ref is not None else str(target)
    status = create_or_resume_batch(args.task_dir, target_ref)
    batch_id = status["batch_id"]
    batch_root = _batch_root(args.task_dir, batch_id)

    # Identical scan -> plan -> manifest sequence tools.adoption_scan.cli.main uses — never
    # re-implemented. Target is read strictly read-only.
    inventory = scan.build_inventory(target)
    plan_doc = plan_mod.build_plan(inventory)
    proposed_hashes = destinations.harness_proposed_hashes()
    manifest_doc = destinations.build_manifest(inventory, target, proposed_hashes)

    documents: dict[str, dict] = {
        "inventory": inventory,
        "plan": plan_doc,
        "manifest": manifest_doc,
    }

    for name in _DRAFT_ARTIFACTS:
        document = documents[name]
        error = _validate(name, document)
        if error is not None:
            print(
                f"tools.adoption_apply draft: {name}.json failed schema validation: {error}",
                file=sys.stderr,
            )
            return 1

    for name in _DRAFT_ARTIFACTS:
        out_path = batch_root / f"{name}.json"
        # ADOPT-05 clause 1: confine every draft write to the batch root, before writing, every
        # call — wires refuse_if_outside_root into the real draft path.
        refuse_if_outside_root(out_path, batch_root)
        out_path.write_bytes(scan._dump(documents[name]))
        print(f"wrote {out_path}", file=sys.stderr)

    return 0


def _harness_payload(destination: str) -> bytes:
    """The harness's own checkout content at *destination* — what a ``create`` disposition
    installs (CR-01: never content read back from the scanned target)."""
    candidate = _REPO_ROOT / destination
    if not candidate.is_file():
        return b""
    return candidate.read_bytes()


def _harness_block_body(destination: str) -> str:
    """The harness's own checkout text content at *destination*, for a ``marker-merge`` fenced
    block body. Empty string when the harness checkout has no file there."""
    candidate = _REPO_ROOT / destination
    if not candidate.is_file():
        return ""
    return candidate.read_text(encoding="utf-8")


def _cmd_apply(args: argparse.Namespace) -> int:
    # CR-03 (ADOPT-06): a batch must be promoted, and the promotion must still exactly match the
    # batch's current (draft_hash, task_revision, git_ref) — checked FIRST, before any manifest
    # read or write. repo_root here is the harness's OWN checkout root (D-02), never the
    # brownfield --target being adopted into: git_ref/task_revision are harness-side concepts and
    # a brownfield target may not even be a git repo.
    if not check_valid(args.task_dir, args.batch_id, args.repo_root):
        print(
            f"tools.adoption_apply apply: REFUSED: batch '{args.batch_id}' has no valid, "
            "current approval — run `promote` first (ADOPT-06 gates apply).",
            file=sys.stderr,
        )
        return 4

    batch_root = _batch_root(args.task_dir, args.batch_id)
    manifest_path = batch_root / "manifest.json"
    if not manifest_path.is_file():
        print(
            f"tools.adoption_apply apply: no manifest.json for batch '{args.batch_id}' "
            f"under {batch_root}",
            file=sys.stderr,
        )
        return 2
    manifest = json.loads(manifest_path.read_bytes())

    # WR-04: re-validate manifest.json against its schema before use — a schema-invalid or
    # tampered manifest must refuse cleanly, not surface as an unhandled KeyError traceback.
    error = _validate("manifest", manifest)
    if error is not None:
        print(
            f"tools.adoption_apply apply: manifest.json failed schema validation: {error}",
            file=sys.stderr,
        )
        return 1

    payloads: dict[str, bytes] = {}
    block_bodies: dict[str, str] = {}
    for record in manifest["dispositions"]:
        destination = record["destination"]
        disposition_value = record["disposition"]
        if disposition_value == "create":
            payloads[destination] = _harness_payload(destination)
        elif disposition_value == "marker-merge":
            block_bodies[destination] = _harness_block_body(destination)

    try:
        summary = apply_manifest(
            manifest, Path(args.target), payloads=payloads, block_bodies=block_bodies
        )
    # WR-05: this tuple is a BACKSTOP, not the guard — a directory-shaped destination is refused by
    # apply.refuse_unsafe_destination before any write. IsADirectoryError and CollisionError are
    # named here as defense in depth so a write-side fault still maps to the documented exit 1
    # rather than leaking a traceback. WR-02 adds FileExistsError/NotADirectoryError for the same
    # reason: they are the mkdir-side faults a destination with a non-directory ancestor produced.
    # Both are now unreachable through the guard — they are backstop-only by construction.
    except (
        apply_module.ConstitutionRefusal,
        apply_module.ReviewLedgerRefusal,
        apply_module.ConcurrentDriftError,
        apply_module.UnknownDispositionError,
        apply_module.PathEscapeError,
        apply_module.SymlinkRefusal,
        apply_module.CollisionError,
        IsADirectoryError,
        FileExistsError,
        NotADirectoryError,
    ) as exc:
        print(f"tools.adoption_apply apply: {exc}", file=sys.stderr)
        return 1

    print(
        f"applied={len(summary['applied'])} skipped={len(summary['skipped'])} "
        f"refused={len(summary['refused'])}",
        file=sys.stderr,
    )
    return 0


def _cmd_promote(args: argparse.Namespace) -> int:
    decisions: list[dict[str, Any]] | None = None
    if args.decisions is not None:
        decisions = json.loads(Path(args.decisions).read_bytes())

    try:
        document = approval_promote(
            args.task_dir,
            args.batch_id,
            args.repo_root,
            approve=args.approve,
            decisions=decisions,
            confirmation=args.confirm,
        )
    except AdoptionApprovalRefused as exc:
        print(str(exc), file=sys.stderr)
        return 3

    print(f"PROMOTED: {document['batch_id']}")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m tools.adoption_apply {draft,apply,promote}``."""
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(prog="tools.adoption_apply")
    subparsers = parser.add_subparsers(dest="command", required=True)

    draft_parser = subparsers.add_parser("draft", help="create or resume a task-local batch")
    draft_parser.add_argument("--task-dir", type=Path, required=True)
    draft_parser.add_argument("--target", type=Path, required=True)
    draft_parser.add_argument("--target-ref", default=None)
    draft_parser.set_defaults(func=_cmd_draft)

    apply_parser = subparsers.add_parser("apply", help="apply a drafted batch's manifest")
    apply_parser.add_argument("--task-dir", type=Path, required=True)
    apply_parser.add_argument("--batch-id", required=True)
    apply_parser.add_argument("--target", type=Path, required=True)
    # D-02: mirrors promote_parser's own --repo-root — the harness's OWN checkout root, never the
    # brownfield --target being adopted into (check_valid's git_ref/task_revision are harness-side
    # concepts; a brownfield target may not even be a git repo).
    apply_parser.add_argument("--repo-root", type=Path, required=True)
    apply_parser.set_defaults(func=_cmd_apply)

    promote_parser = subparsers.add_parser("promote", help="ratify a batch's reviewed decisions")
    promote_parser.add_argument("--task-dir", type=Path, required=True)
    promote_parser.add_argument("--batch-id", required=True)
    promote_parser.add_argument("--repo-root", type=Path, required=True)
    promote_parser.add_argument("--approve", action="store_true")
    promote_parser.add_argument("--decisions", default=None)
    promote_parser.add_argument("--confirm", default=None)
    promote_parser.set_defaults(func=_cmd_promote)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
