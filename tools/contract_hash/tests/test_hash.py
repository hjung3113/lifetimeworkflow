"""Direct coverage for the RFC 8785 (JCS) per-schema hasher (CONTRACT-04, D-07).

``tools.contract_hash`` underpins the whole schema-hash drift gate, yet was only exercised
indirectly (via the drift tests' ``build_manifest`` calls). These tests pin the load-bearing
behaviour directly: JCS canonicalization is order/whitespace-invariant, the manifest is keyed
``contracts/...`` relative to the tree's parent, the symlink-escape defence drops out-of-subtree
targets, and ``write_manifest`` emits deterministic sorted JSON.

Core-plane invariant (GEN-04): lives under ``tools/`` and names no instance — every tree here is a
self-built SYNTHETIC ``contracts/`` fixture; the committed root baseline is never touched.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Make the repo-root `tools` package importable (virtual uv workspace members, not pip-installed).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.contract_hash.hash import (  # noqa: E402
    build_manifest,
    schema_hash,
    write_manifest,
)

_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["a", "b"],
    "properties": {"a": {"type": "string"}, "b": {"type": "integer"}},
}


def _write_schema(path: Path, obj: dict, *, indent: int | None = 2) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=indent), encoding="utf-8")
    return path


# --- schema_hash: RFC 8785 canonicalization is order/whitespace-invariant ------------------------


def test_schema_hash_is_key_order_invariant(tmp_path: Path) -> None:
    a = _write_schema(tmp_path / "a.schema.json", {"type": "object", "required": ["x", "y"]})
    # Same document, keys authored in a different order + compact whitespace.
    b = _write_schema(
        tmp_path / "b.schema.json", {"required": ["x", "y"], "type": "object"}, indent=None
    )
    assert schema_hash(a) == schema_hash(b)


def test_schema_hash_changes_on_value_change(tmp_path: Path) -> None:
    a = _write_schema(tmp_path / "a.schema.json", _SCHEMA)
    mutated = {
        **_SCHEMA,
        "required": ["a"],
    }  # dropped a required field -> different canonical bytes
    b = _write_schema(tmp_path / "b.schema.json", mutated)
    assert schema_hash(a) != schema_hash(b)


def test_schema_hash_is_hex_sha256(tmp_path: Path) -> None:
    h = schema_hash(_write_schema(tmp_path / "a.schema.json", _SCHEMA))
    assert len(h) == 64 and all(c in "0123456789abcdef" for c in h)


# --- build_manifest: contracts/... keying + subtree confinement ----------------------------------


def test_build_manifest_keys_are_contracts_relative(tmp_path: Path) -> None:
    contracts = tmp_path / "contracts"
    _write_schema(contracts / "widget" / "thing.schema.json", _SCHEMA)
    _write_schema(contracts / "top.schema.json", _SCHEMA)
    manifest = build_manifest(contracts)
    assert set(manifest) == {"contracts/widget/thing.schema.json", "contracts/top.schema.json"}


def test_build_manifest_ignores_non_schema_files(tmp_path: Path) -> None:
    contracts = tmp_path / "contracts"
    _write_schema(contracts / "a.schema.json", _SCHEMA)
    (contracts / "notes.json").write_text("{}", encoding="utf-8")  # not *.schema.json
    (contracts / "README.md").write_text("# x", encoding="utf-8")
    assert list(build_manifest(contracts)) == ["contracts/a.schema.json"]


def test_build_manifest_drops_symlink_escaping_subtree(tmp_path: Path) -> None:
    # A symlink inside contracts/ pointing at a schema OUTSIDE the subtree must be excluded by the
    # defence-in-depth guard (resolved parent not under root) — else drift could hash foreign files.
    outside = _write_schema(tmp_path / "outside" / "secret.schema.json", {"type": "string"})
    contracts = tmp_path / "contracts"
    _write_schema(contracts / "real.schema.json", _SCHEMA)
    link = contracts / "escape.schema.json"
    try:
        os.symlink(outside, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unsupported on this platform")
    manifest = build_manifest(contracts)
    assert "contracts/escape.schema.json" not in manifest
    assert list(manifest) == ["contracts/real.schema.json"]


# --- write_manifest: deterministic sorted JSON round-trip ----------------------------------------


def test_write_manifest_sorted_with_trailing_newline(tmp_path: Path) -> None:
    contracts = tmp_path / "contracts"
    _write_schema(contracts / "b.schema.json", _SCHEMA)
    _write_schema(contracts / "a.schema.json", _SCHEMA)
    out = write_manifest(manifest_path=tmp_path / "m.json", contracts_dir=contracts)
    text = out.read_text(encoding="utf-8")
    assert text.endswith("\n")
    loaded = json.loads(text)
    assert list(loaded) == sorted(loaded)  # sort_keys=True
    assert loaded == build_manifest(contracts)
