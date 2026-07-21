"""Task 3: cli.py — all three artifacts written by a real cli.main() invocation validate with
zero errors against their ratified schemas."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from tools.adoption_scan import cli

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_DIR = _REPO_ROOT / "contracts" / "harness" / "adoption"


def _schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def test_all_three_artifacts_validate(tmp_minirepo: Path, tmp_path: Path) -> None:
    out = tmp_path / "out"
    rc = cli.main(["--target", str(tmp_minirepo), "--out", str(out)])
    assert rc == 0

    for name in ("inventory", "plan", "manifest"):
        document = json.loads((out / f"{name}.json").read_text(encoding="utf-8"))
        validator = Draft202012Validator(_schema(name))
        errors = list(validator.iter_errors(document))
        assert errors == [], f"{name}.json failed validation: {errors}"


def test_out_required_no_default() -> None:
    """--out has no default (D-11); argparse itself refuses (SystemExit(2)) when it's missing."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--target", "/tmp"])
    assert excinfo.value.code == 2


def test_out_inside_target_refused(tmp_minirepo: Path) -> None:
    out = tmp_minirepo / "out"
    rc = cli.main(["--target", str(tmp_minirepo), "--out", str(out)])
    assert rc == 2
    assert not out.exists() or not any(out.iterdir())


def test_target_equal_out_refused(tmp_minirepo: Path) -> None:
    rc = cli.main(["--target", str(tmp_minirepo), "--out", str(tmp_minirepo)])
    assert rc == 2


def test_target_inside_out_refused(tmp_minirepo: Path, tmp_path: Path) -> None:
    out = tmp_minirepo.parent  # tmp_minirepo is a child of this dir -> target is inside out
    rc = cli.main(["--target", str(tmp_minirepo), "--out", str(out)])
    assert rc == 2


def test_target_must_exist(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    out = tmp_path / "out"
    rc = cli.main(["--target", str(missing), "--out", str(out)])
    assert rc == 2
