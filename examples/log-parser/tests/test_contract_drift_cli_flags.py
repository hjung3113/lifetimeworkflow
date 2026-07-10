"""Instance-plane proof: the CORE drift/hash CLIs gate THIS example's contracts tree (CI-01).

The core template must name no instance (GEN-04), so the example-referencing half of the
Enabler-2 flag proof lives here in the INSTANCE plane (example→core is the one allowed direction).
It drives the already-parameterized ``tools.contract_drift.drift`` / ``tools.contract_hash.hash``
CLIs — by verbatim reuse (D-01) — against ``examples/log-parser/contracts`` + its committed
``.hashes/manifest.json``: a pristine copy passes (exit 0), a mutated copy trips the gate (exit 1),
and ``hash --write --contracts-dir <example>`` writes example-rooted keys (Warning-1 regression).
Off the root ``testpaths`` (run via ``uv run pytest examples/log-parser/tests``); the committed
baseline is never mutated (edits happen on tmp copies).
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

# tests -> log-parser -> examples -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_drift.drift import main  # noqa: E402
from tools.contract_hash.hash import build_manifest  # noqa: E402
from tools.contract_hash.hash import main as hash_main  # noqa: E402

_EXAMPLE_CONTRACTS = _REPO_ROOT / "examples" / "log-parser" / "contracts"


def _copy_contracts(tmp_path: Path) -> Path:
    dst = tmp_path / "contracts"
    shutil.copytree(_EXAMPLE_CONTRACTS, dst)
    return dst


def test_example_manifest_pristine_passes(tmp_path):
    """--contracts-dir/--baseline gate a pristine example copy → exit 0 (verbatim core reuse)."""
    contracts = _copy_contracts(tmp_path)
    manifest = contracts / ".hashes" / "manifest.json"
    assert manifest.is_file(), "example copy must carry its committed baseline"
    assert main(["--contracts-dir", str(contracts), "--baseline", str(manifest)]) == 0


def test_example_manifest_mutated_fails(tmp_path):
    """Mutating a copied example schema trips the core gate through the CLI wrapper → exit 1."""
    contracts = _copy_contracts(tmp_path)
    manifest = contracts / ".hashes" / "manifest.json"
    schema = contracts / "state" / "equipment-progress.schema.json"
    doc = json.loads(schema.read_text(encoding="utf-8"))
    doc["required"].remove("id")  # breaking edit — bumps the JCS SHA-256 vs the copied baseline
    schema.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    assert main(["--contracts-dir", str(contracts), "--baseline", str(manifest)]) == 1


def test_write_targets_example_tree(tmp_path):
    """--write --contracts-dir <example> writes example-rooted keys, not root (Warning-1)."""
    contracts = _copy_contracts(tmp_path)
    out = tmp_path / "out.json"
    assert hash_main(["--write", "--contracts-dir", str(contracts), "--manifest", str(out)]) == 0
    written = json.loads(out.read_text(encoding="utf-8"))
    assert written == build_manifest(str(contracts)), "must hash the example tree"
    assert written != build_manifest(), "must NOT write root-tree hashes into the example manifest"
