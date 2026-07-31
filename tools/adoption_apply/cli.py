"""cli.py — the argument-routed ``draft``/``apply`` dispatcher
``python -m tools.adoption_apply`` needs (``__main__.py``'s ``from tools.adoption_apply.cli import
main``, Plan 27-01's output, has had nothing to import from until this module).

Composition only — this module never re-implements ``tools.adoption_apply``'s own
``batch``/``apply`` logic, nor ``tools.adoption_scan``'s scan/plan/manifest logic.
Discovery (``python -m tools.adoption_scan``) stays out of scope here; ``cli.py`` composes only
the ``adoption_apply``-owned half of the lifecycle (``draft``/``apply``), per
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
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.adoption_apply import apply as apply_module
from tools.adoption_apply.apply import apply_manifest, refuse_if_outside_root
from tools.adoption_apply.batch import create_or_resume_batch
from tools.adoption_scan import destinations, scan
from tools.adoption_scan import plan as plan_mod

# cli.py -> adoption_apply -> tools -> repo root (parents[2]) — same depth as adoption_scan/cli.py.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_DIR = _REPO_ROOT / "contracts" / "harness" / "adoption"

_DRAFT_ARTIFACTS: tuple[str, ...] = ("inventory", "plan", "manifest")

# OBS-D-03 / D-12 (52-CONTEXT.md): target-derived [[languages]] row — the ONE sanctioned CR-01
# exception. Every other draft/apply artifact stays the harness's own checkout bytes (CR-01); this
# is the single deliberate splice, computed at draft time from the TARGET's own package.json.
_DERIVED_LANGUAGE_ID = "javascript"
_DERIVED_BASH_SCOPE = "pnpm *"
_DERIVED_SCRIPT_KEYS: tuple[str, ...] = ("lint", "test", "format")
_DERIVED_LANGUAGES_SIDECAR = "languages.toml"
_DERIVED_PROVENANCE_COMMENT = (
    "# Derived by tools.adoption_apply from the adopted target's own package.json scripts "
    "(OBS-D-03 / D-12)."
)


def derive_language_rows(package_json_text: str) -> str | None:
    """Pure, filesystem-free: render a ``[[languages]]`` TOML table from a target's own
    ``package.json`` ``scripts`` object, or ``None`` when there is nothing to derive.

    OBS-D-03 / D-12 (52-CONTEXT.md): the ONE sanctioned CR-01 exception — target-derived content
    flowing into ``harness/project.toml``, computed here at draft time. Script VALUES are never
    copied into the row and never executed: only the fixed literal ``"pnpm run <key>"`` command
    strings are emitted, keyed by which of the allowlisted ``_DERIVED_SCRIPT_KEYS`` names exist
    (T-52-07 — no subprocess argv is ever built from manifest/draft content).

    Returns ``None`` on malformed JSON, a non-object top level, a missing/non-dict ``scripts``, or
    a ``scripts`` object that does not declare ``test`` — nothing is invented, and nothing
    partially-shaped is emitted.

    CR-03 (52-REVIEW.md) — WHY ``test`` is the one hard requirement, and why the other keys are
    omitted rather than blanked. The apply cycle installs ``tools/**`` and
    ``.github/workflows/**`` into the adopted target, so the target inherits the consumers of
    this row. Traced against what each ACTUALLY does with it:

    - ``.github/workflows/ci.yml`` (SHIPPED) — the ``setup`` job ``sys.exit``s when any
      ``[[languages]]`` entry has an empty ``id`` or ``test``. The previous ``test = ""`` for a
      target declaring ``lint`` but no ``test`` (extremely common) therefore made the adopted
      target's CI unable to start. Hence: no ``test`` script -> no row at all. That job reads
      ``test_paths`` with ``.get(..., [])``, and a bare ``pnpm run test`` at a workspace root is
      the correct invocation, so an absent ``test_paths`` is right, not merely tolerated.
    - ``tools/harness_config/loader.py::conventions_for`` (SHIPPED) — reads the row by subscript.
      Made ``.get``-tolerant in the same commit, matching the ``lint`` treatment D-11 already
      established, so an omitted ``format`` resolves to ``None`` instead of raising.
    - ``tools/harness_lint/tests/test_language_config.py`` (NOT SHIPPED) — the ``persona``
      subscript, the ``test_paths`` non-empty check and the ``bash_scope`` set-equality check all
      live here, and ``destinations._SKIP_SEGMENTS`` excludes every ``tools/**`` path with a
      ``tests`` segment from the catalog, so none of those three reaches an adopted target.
      That is what makes omitting ``persona``/``test_paths`` the honest answer rather than a
      shortcut: neither is derivable from a ``package.json`` at all (there is no javascript
      persona in ``harness/agents/``, and a target's test paths are unknowable from its
      manifest), and inventing either would be exactly the fabrication D-02 forbids.

    ``bash_scope`` is still emitted. The target's copied ``harness/permission-matrix.json`` has no
    ``pnpm *`` allow key, so pnpm commands there fall to the matrix's ``*: ask`` catch-all — a
    safe-by-default degradation, not a break, and the only gate that would call the divergence an
    error is the unshipped one above. Dropping the key would discard true, useful data and buy
    nothing.
    """
    try:
        data = json.loads(package_json_text)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    scripts = data.get("scripts")
    if not isinstance(scripts, dict) or "test" not in scripts:
        return None

    lines = [
        _DERIVED_PROVENANCE_COMMENT,
        "[[languages]]",
        f'id = "{_DERIVED_LANGUAGE_ID}"',
        f'bash_scope = "{_DERIVED_BASH_SCOPE}"',
    ]
    # Omit, never blank: an empty string is a second spelling of "absent" that every consumer
    # above reads as a real-but-empty command.
    for key in _DERIVED_SCRIPT_KEYS:
        if key in scripts:
            lines.append(f'{key} = "pnpm run {key}"')
    return "\n".join(lines) + "\n"


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

    # OBS-D-03 / D-12 (52-CONTEXT.md): the ONE sanctioned CR-01 exception — target-derived
    # [[languages]] row, derived here at draft time from the target's OWN root package.json, only
    # when the target declares itself a pnpm workspace. Batch-local sidecar data, never a
    # contract/command/skill (NG-01 untouched).
    workspace_marker = target / "pnpm-workspace.yaml"
    root_manifest = target / "package.json"
    if workspace_marker.is_file() and root_manifest.is_file():
        # WR-06 (52-REVIEW.md): `read_text` on TARGET-controlled content raised
        # UnicodeDecodeError/OSError straight out of `main()` as an unhandled traceback — and it
        # did so AFTER inventory.json / plan.json / manifest.json were already written, leaving a
        # batch that looks drafted but carries no sidecar and no error record. Every other
        # failure in _cmd_draft returns a clean exit code; this one now degrades with a named
        # message and the draft completes without a sidecar.
        try:
            manifest_text: str | None = root_manifest.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            print(
                f"tools.adoption_apply draft: unreadable target package.json: {exc} — "
                "no derived [[languages]] sidecar written",
                file=sys.stderr,
            )
            manifest_text = None
        derived = derive_language_rows(manifest_text) if manifest_text is not None else None
        if derived is not None:
            sidecar_path = batch_root / _DERIVED_LANGUAGES_SIDECAR
            refuse_if_outside_root(sidecar_path, batch_root)
            sidecar_path.write_text(derived, encoding="utf-8")
            print(f"wrote {sidecar_path}", file=sys.stderr)

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

    # OBS-D-03 / D-12 (52-CONTEXT.md): the ONE sanctioned CR-01 exception — target-derived
    # [[languages]] row, appended ONLY to the "harness/project.toml" payload, ONLY when the batch
    # carries a draft-time-derived sidecar. Every other destination stays the harness's own
    # checkout bytes verbatim (T-52-10 — the splice guard is the exact literal destination string,
    # never a prefix/glob match).
    #
    # WR-08 (52-REVIEW.md), recorded consequence — NOT repaired here. The applied bytes are
    # `harness_payload + b"\n" + sidecar_bytes`, so `sha256(existing) != proposed_sha` on the next
    # draft: `destinations.disposition()` step 6 (`preserve`) can never fire for
    # harness/project.toml again and step 7 classifies it `conflict` permanently, with nothing in
    # the manifest recording that the divergence is harness-DERIVED rather than a human edit.
    # Recording that provenance needs a new field on the disposition record, i.e. a change to
    # contracts/harness/adoption/manifest.schema.json — the constitution plane, which is
    # human-gated and closed for this phase. Noted here so Phase 53's re-run-as-update work does
    # not rediscover it.
    sidecar_path = batch_root / _DERIVED_LANGUAGES_SIDECAR
    if "harness/project.toml" in payloads and sidecar_path.is_file():
        sidecar_bytes = sidecar_path.read_bytes()
        payloads["harness/project.toml"] = payloads["harness/project.toml"] + b"\n" + sidecar_bytes
        print(
            f"spliced {sidecar_path} into harness/project.toml payload (OBS-D-03 / D-12)",
            file=sys.stderr,
        )
    elif sidecar_path.is_file():
        # WR-07 (52-REVIEW.md): `payloads` is populated ONLY for `create` dispositions. If the
        # target already carries a harness/project.toml the disposition is `preserve` or
        # `conflict`, so the sidecar was silently ignored — the D-12 repair did nothing and said
        # nothing. Reachable on every re-adoption, i.e. the whole Phase-53 update scenario.
        print(
            f"tools.adoption_apply apply: derived languages sidecar present at {sidecar_path} "
            "but harness/project.toml is not a 'create' destination — NOT spliced "
            "(OBS-D-03 / D-12)",
            file=sys.stderr,
        )

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


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m tools.adoption_apply {draft,apply}``."""
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
    apply_parser.set_defaults(func=_cmd_apply)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
