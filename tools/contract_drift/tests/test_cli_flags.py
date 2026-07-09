"""Enabler-2: drift/hash CLI flags target the EXAMPLE manifest by verbatim tool reuse (CI-01).

Proves the new ``--contracts-dir``/``--baseline`` argparse on ``drift.main`` routes to the
already-parameterized ``run_gate`` so CI can gate the example contracts tree — pristine copy passes
(exit 0), a mutated copy trips the gate (exit 1), and the bare no-flag invocation is unchanged for
the root job. Also the Warning-1 regression: ``hash.main(["--write", "--contracts-dir", <example>])``
must write EXAMPLE-rooted keys, never root-tree content. The committed baselines are never mutated
(all edits happen on tmp copies).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# Make the repo-root `tools` package importable (virtual uv workspace members, not pip-installed).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import main  # noqa: E402
from tools.contract_hash.hash import REPO_ROOT, build_manifest  # noqa: E402
from tools.contract_hash.hash import main as hash_main  # noqa: E402

_EXAMPLE_CONTRACTS = REPO_ROOT / "examples" / "log-parser" / "contracts"


def _copy_example_contracts(tmp_path: Path) -> Path:
    """Copy the example contracts tree (incl. its ``.hashes/manifest.json``) to a tmp dir."""
    dst = tmp_path / "contracts"
    shutil.copytree(_EXAMPLE_CONTRACTS, dst)
    return dst


def test_flags_route_to_example_manifest_pristine_passes(tmp_path):
    """--contracts-dir/--baseline point the gate at a pristine example copy → exit 0."""
    contracts = _copy_example_contracts(tmp_path)
    manifest = contracts / ".hashes" / "manifest.json"
    assert manifest.is_file(), "example copy must carry its committed baseline"
    assert main(["--contracts-dir", str(contracts), "--baseline", str(manifest)]) == 0


def test_flags_route_to_example_manifest_mutated_fails(tmp_path):
    """Mutating a copied example schema trips the gate through the CLI wrapper → exit 1."""
    contracts = _copy_example_contracts(tmp_path)
    manifest = contracts / ".hashes" / "manifest.json"
    schema = contracts / "state" / "equipment-progress.schema.json"

    doc = json.loads(schema.read_text(encoding="utf-8"))
    # Drop a required field (breaking edit) — bumps the JCS SHA-256 vs the copied baseline.
    doc["required"].remove("id")
    schema.write_text(json.dumps(doc, indent=2), encoding="utf-8")

    assert main(["--contracts-dir", str(contracts), "--baseline", str(manifest)]) == 1


def test_no_flags_still_gates_root_defaults(tmp_path):
    """Bare main([]) is unchanged: gates the clean root tree with the committed baseline → exit 0."""
    assert main([]) == 0


def test_write_targets_example_tree(tmp_path):
    """Warning-1 regression: --write --contracts-dir <example> writes EXAMPLE-rooted keys, not root.

    Before ``write_manifest`` threads ``contracts_dir``, the written file equals ``build_manifest()``
    (the ROOT tree) regardless of ``--contracts-dir`` — a silent corruption. This asserts the fix.
    """
    contracts = _copy_example_contracts(tmp_path)
    out = tmp_path / "out.json"

    rc = hash_main(["--write", "--contracts-dir", str(contracts), "--manifest", str(out)])
    assert rc == 0

    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == build_manifest(str(contracts)), "must hash the flagged (example) tree"
    assert written != build_manifest(), "must NOT write root-tree hashes into the example manifest"
