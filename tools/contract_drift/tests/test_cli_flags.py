"""Enabler-2: drift/hash CLI flags route to a NON-root contracts tree (CI-01, core-plane).

Proves the new ``--contracts-dir``/``--baseline`` argparse on ``drift.main`` routes to the
already-parameterized ``run_gate`` — a pristine synthetic tree passes (exit 0), a mutated copy
trips the gate (exit 1), and the bare no-flag invocation is unchanged for the root job. Also the
Warning-1 regression: ``hash.main(["--write", "--contracts-dir", D, "--manifest", M])`` must write
D-rooted keys, never the root tree's content.

Core-plane invariant (GEN-04): this file lives under ``tools/`` and therefore must NOT name any
instance — it exercises the flags against a self-built SYNTHETIC contracts tree. The equivalent
proof against the real instance manifest lives in that instance's own test plane (the one allowed
example->core direction). The committed root baseline is never mutated.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Make the repo-root `tools` package importable (virtual uv workspace members, not pip-installed).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import main  # noqa: E402
from tools.contract_hash.hash import build_manifest, write_manifest  # noqa: E402
from tools.contract_hash.hash import main as hash_main  # noqa: E402

_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["a", "b"],
    "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
}


def _build_synthetic_tree(tmp_path: Path) -> tuple[Path, Path]:
    """Write a generic ``contracts/`` subtree + its committed baseline; return (dir, manifest)."""
    contracts = tmp_path / "contracts"
    (contracts / "widget").mkdir(parents=True)
    (contracts / "widget" / "thing.schema.json").write_text(
        json.dumps(_SCHEMA, indent=2), encoding="utf-8"
    )
    manifest = write_manifest(
        manifest_path=contracts / ".hashes" / "manifest.json", contracts_dir=contracts
    )
    return contracts, manifest


def test_flags_route_to_nonroot_pristine_passes(tmp_path):
    """--contracts-dir/--baseline point the gate at a pristine synthetic tree → exit 0."""
    contracts, manifest = _build_synthetic_tree(tmp_path)
    assert main(["--contracts-dir", str(contracts), "--baseline", str(manifest)]) == 0


def test_flags_route_to_nonroot_mutated_fails(tmp_path):
    """Mutating a copied schema trips the gate through the CLI wrapper → exit 1."""
    contracts, manifest = _build_synthetic_tree(tmp_path)
    schema = contracts / "widget" / "thing.schema.json"
    doc = json.loads(schema.read_text(encoding="utf-8"))
    doc["required"].remove("a")  # breaking edit — bumps the JCS SHA-256 vs the baseline
    schema.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    assert main(["--contracts-dir", str(contracts), "--baseline", str(manifest)]) == 1


def test_no_flags_still_gates_root_defaults(tmp_path):
    """Bare main([]) is unchanged: gates the clean root tree with its committed baseline (0)."""
    assert main([]) == 0


def test_write_threads_contracts_dir_not_root(tmp_path):
    """Warning-1 regression: --write --contracts-dir D --manifest M writes D-rooted keys, not root.

    Before ``write_manifest`` threads ``contracts_dir``, the written file equals the ROOT
    ``build_manifest()`` regardless of ``--contracts-dir`` — a silent corruption. Asserts the fix.
    """
    contracts, _ = _build_synthetic_tree(tmp_path)
    out = tmp_path / "out.json"
    assert hash_main(["--write", "--contracts-dir", str(contracts), "--manifest", str(out)]) == 0

    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == build_manifest(str(contracts)), "must hash the flagged tree"
    assert written != build_manifest(), "must NOT write root-tree hashes into the flagged manifest"
