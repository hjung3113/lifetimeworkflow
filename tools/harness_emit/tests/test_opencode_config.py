"""EMIT-01/02 opencode.json config emit — the one genuine transform (matrix → 15-key block).

RED at Task 2 (this file imports ``tools.harness_emit.permissions``, which does not exist yet, and
calls ``validate.check_opencode_config`` — collection/attribute fails). GREEN once the permission
projector + the schema/model loud-fail validator land.

Pins the two contract-critical properties (STRIDE T-07-06 / T-07-07 / T-07-03):
  * the projected ``permission`` block is EXACTLY the 15 opencode keys — ``_note`` and
    ``path_deny_globs`` (resolver-only data) are stripped;
  * the ``bash`` sub-object keeps its AUTHORED insertion order (``*`` FIRST — last-wins, P3);
  * a schema-invalid emitted config HARD-fails (HarnessEmitError, writes nothing);
  * a non-placeholder ``model`` value HARD-fails (no real model identifier leaks).
"""

from __future__ import annotations

import collections
import copy
import json
from pathlib import Path

import pytest

from tools.harness_emit import generate as harness_emit
from tools.harness_emit import permissions, validate
from tools.harness_emit.generate import HarnessEmitError
from tools.harness_lint.caps import VALID_PERMISSION_KEYS
from tools.harness_perms.resolver import load_matrix

# test_opencode_config.py -> tests -> harness_emit -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_HARNESS = _REPO_ROOT / "harness"
_MATRIX = _HARNESS / "permission-matrix.json"
_SCHEMA = _HARNESS / "opencode.config.schema.json"
_ROOT_CONFIG = _REPO_ROOT / "opencode.json"

_RESOLVER_ONLY = ("_note", "path_deny_globs")


def _schema() -> dict:
    return json.loads(_SCHEMA.read_text(encoding="utf-8"))


# ---- build_permission_block ------------------------------------------------------------------


def test_permission_block_is_exactly_the_15_opencode_keys() -> None:
    """The projected block equals the 15 valid opencode keys — resolver-only data stripped."""
    block = permissions.build_permission_block(load_matrix(_MATRIX))
    assert set(block) == set(VALID_PERMISSION_KEYS)
    for key in _RESOLVER_ONLY:
        assert key not in block, f"resolver-only key {key!r} leaked into the permission block"


def test_permission_block_bash_is_star_first() -> None:
    """bash keeps AUTHORED insertion order — catch-all ``*`` FIRST (last-wins, P3; T-07-06)."""
    block = permissions.build_permission_block(load_matrix(_MATRIX))
    bash_keys = list(block["bash"])
    assert bash_keys[0] == "*", f"bash last-wins order broken (expected '*' first): {bash_keys}"
    # The exact authored order must survive the projection (sorting would break it).
    assert bash_keys == list(load_matrix(_MATRIX)["bash"])


# ---- check_opencode_config (schema + model loud-fail) ----------------------------------------


def test_valid_config_passes() -> None:
    """The emitter-built config validates against the vendored subset schema (no raise)."""
    config = harness_emit.build_opencode_config(_HARNESS)
    validate.check_opencode_config(config, _schema())  # must not raise


def test_schema_invalid_config_raises() -> None:
    """A config missing a required key HARD-fails via HarnessEmitError (T-07-07; writes nothing)."""
    config = harness_emit.build_opencode_config(_HARNESS)
    del config["permission"]  # 'permission' is required by the subset schema
    with pytest.raises(HarnessEmitError):
        validate.check_opencode_config(config, _schema())


def test_real_model_identifier_raises() -> None:
    """A non-placeholder model value HARD-fails — no real model identifier may leak (T-07-03)."""
    config = harness_emit.build_opencode_config(_HARNESS)
    config["model"] = "anthropic/claude-opus-4"
    with pytest.raises(HarnessEmitError):
        validate.check_opencode_config(config, _schema())


def test_small_model_real_identifier_also_raises() -> None:
    """The model-identity gate covers every ``*model`` key, not just ``model`` (T-07-03)."""
    config = harness_emit.build_opencode_config(_HARNESS)
    config["small_model"] = "openai/gpt-5"
    with pytest.raises(HarnessEmitError):
        validate.check_opencode_config(config, _schema())


def test_build_config_replaces_partial_permission_block() -> None:
    """The emitter owns opencode.json wholesale: authored partial block → full 15-key block."""
    authored = json.loads((_HARNESS / "opencode.json").read_text(encoding="utf-8"))
    assert set(authored["permission"]) != set(VALID_PERMISSION_KEYS), "authored block is partial"
    config = harness_emit.build_opencode_config(_HARNESS)
    assert set(config["permission"]) == set(VALID_PERMISSION_KEYS)
    # non-permission authored keys are preserved verbatim
    assert config["instructions"] == authored["instructions"]
    assert config["formatter"] == authored["formatter"]


# ---- emitted root opencode.json --------------------------------------------------------------


def test_emitted_root_config_shape(tmp_path: Path) -> None:
    """Emitting into a tmp tree writes a root opencode.json with the full, ordered 15-key block."""
    harness_emit.emit(
        opencode_dir=tmp_path / ".opencode",
        claude_dir=tmp_path / ".claude",
        manifest_path=tmp_path / "emit-manifest.json",
        root=tmp_path,
    )
    emitted = tmp_path / "opencode.json"
    assert emitted.exists(), "emit did not write a root opencode.json"
    parsed = json.loads(
        emitted.read_text(encoding="utf-8"), object_pairs_hook=collections.OrderedDict
    )
    perm = parsed["permission"]
    assert set(perm) == set(VALID_PERMISSION_KEYS)
    for key in _RESOLVER_ONLY:
        assert key not in perm
    assert list(perm["bash"])[0] == "*", "emitted bash lost '*'-first last-wins order"


def test_committed_root_config_matches_reemit() -> None:
    """The committed root opencode.json carries the emitter's transform (no resolver-only keys)."""
    assert _ROOT_CONFIG.exists(), "committed root opencode.json missing"
    parsed = json.loads(
        _ROOT_CONFIG.read_text(encoding="utf-8"), object_pairs_hook=collections.OrderedDict
    )
    perm = parsed["permission"]
    assert set(perm) == set(VALID_PERMISSION_KEYS)
    assert "_note" not in perm and "path_deny_globs" not in perm
    assert list(perm["bash"])[0] == "*"
    # no real model identifier committed — only placeholder tiers
    for key, value in parsed.items():
        if key == "model" or key.endswith("_model"):
            assert value.startswith("provider/") and value.endswith("-tier")


def test_config_is_deterministic() -> None:
    """Re-serializing the built config is byte-stable (the emit-drift gate depends on it)."""
    config = harness_emit.build_opencode_config(_HARNESS)
    first = permissions.dumps_config(config)
    second = permissions.dumps_config(copy.deepcopy(config))
    assert first == second
