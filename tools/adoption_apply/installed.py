"""Target-resident adopt bookkeeping, never a manifest disposition row.

The record stores exactly one post-write hash per destination because the source side is recomputed
on every run by ``destinations.harness_proposed_hashes()``. Reads and writes validate the contract
shape: the target file is untrusted. Validation proves shape, not provenance; an ``update`` always
writes harness content, never target-supplied content.
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from tools.adoption_apply.apply import refuse_if_outside_root

__all__ = ("INSTALLED_REL", "installed_path", "read_installed_record", "write_installed_record")

INSTALLED_REL: str = ".harness/adoption/installed.json"
_REPO_ROOT = Path(__file__).resolve().parents[2]
_MANIFEST_SCHEMA = json.loads(
    (_REPO_ROOT / "contracts" / "harness" / "adoption" / "manifest.schema.json").read_text(
        encoding="utf-8"
    )
)
_VALIDATOR = Draft202012Validator(
    {
        "type": "object",
        "additionalProperties": False,
        "required": ["installed"],
        "properties": {
            "installed": {"type": "array", "items": {"$ref": "#/$defs/installedRecord"}}
        },
        "$defs": _MANIFEST_SCHEMA["$defs"],
    }
)


class InstalledRecordError(ValueError):
    """Raised when the target-resident installed record is malformed or invalid."""


def installed_path(target_root: str | Path) -> Path:
    """Return the one fixed installed-record path within ``target_root``."""
    return Path(target_root) / INSTALLED_REL


def _validate(document: dict, path: Path) -> None:
    errors = sorted(_VALIDATOR.iter_errors(document), key=lambda error: list(error.path))
    if errors:
        raise InstalledRecordError(f"invalid installed record at {path}: {errors[0].message}")


def read_installed_record(target_root: str | Path) -> list[dict]:
    """Read and validate the target record, returning no records for a first-ever adopt."""
    path = installed_path(target_root)
    if not path.exists():
        return []
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise InstalledRecordError(f"invalid installed record at {path}: {error}") from error
    _validate(document, path)
    return document["installed"]


def write_installed_record(target_root: str | Path, records: list[dict]) -> Path:
    """Validate and deterministically write the target's installed record."""
    path = installed_path(target_root)
    document = {"installed": list(records)}
    _validate(document, path)
    document["installed"].sort(key=lambda record: record["destination"])
    refuse_if_outside_root(path, target_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
