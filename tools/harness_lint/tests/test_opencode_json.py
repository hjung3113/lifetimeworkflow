"""CONFIG-01 structural gate (D-02) — hermetic jsonschema validation of harness/opencode.json.

Proves T-03-05 (opencode.json drift/typo) is caught before the config is trusted: the authored
config is validated against the VENDORED subset schema (harness/opencode.config.schema.json), never
by fetching opencode.ai (T-03-08 — non-hermetic + 403). The test doubles as a presence assertion
that the shipped config carries every CONFIG-01 key the harness surface depends on.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

# test_opencode_json.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CONFIG = _REPO_ROOT / "harness" / "opencode.json"
_SCHEMA = _REPO_ROOT / "harness" / "opencode.config.schema.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_opencode_json_validates_against_vendored_subset() -> None:
    """jsonschema.validate must NOT raise — opencode.json conforms to the vendored subset (T-03-05)."""
    config = _load(_CONFIG)
    schema = _load(_SCHEMA)
    jsonschema.validate(config, schema)  # raises ValidationError on drift/typo


def test_opencode_json_has_config01_keys() -> None:
    """Explicit CONFIG-01 presence: model tiering, instructions, formatter, mcp."""
    config = _load(_CONFIG)
    assert config["model"], "expensive implementer-tier model missing"
    assert config["small_model"], "cheap explorer-tier small_model missing"
    assert isinstance(config["instructions"], list) and config["instructions"], "instructions glob list missing"
    assert isinstance(config["formatter"], dict) and config["formatter"], "formatter wiring missing"
    assert "mcp" in config, "mcp wiring key missing"


def test_opencode_json_permission_has_bash_block() -> None:
    """The coarse project-default permission block carries a bash sub-matrix (last-wins default)."""
    config = _load(_CONFIG)
    assert config["permission"]["bash"], "default permission.bash block missing"


def test_opencode_json_carries_no_real_model_id() -> None:
    """Model-identity constraint: only PLACEHOLDER tier tokens, never a real provider model ID."""
    config = _load(_CONFIG)
    assert config["model"] == "provider/implementer-tier"
    assert config["small_model"] == "provider/explorer-tier"
