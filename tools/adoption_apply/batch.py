"""Task-local adoption batch layout (ADOPT-04).

An adoption batch is a task-local *artifact kind* under the ``artifacts/<kind>/<run-id>/``
convention, with ``<batch-id>`` playing the role of ``<run-id>``. A batch is purely additive
evidence, never a phase-transition gate, and this module makes no changes to any other package's
files or contracts (D-01).

Per D-02, ``<batch-id>`` is content-derived from ``(target_ref, discover-time UTC date)`` so a
same-day re-discover against an unchanged ``target_ref`` resumes the SAME batch directory without
mutating it (SC-1's "안전하게 재개").

This module implements its own atomic-create / CAS-guarded-replace idiom
(``tempfile.mkstemp`` + ``os.link``/``os.replace`` + ``fcntl.flock``) as a complete,
self-contained sequence, per 27-RESEARCH.md's "Don't Hand-Roll" guidance.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class BatchError(ValueError):
    """A deterministic adoption-batch failure (stale CAS writer, malformed status, etc.)."""


def _batch_dir(task_dir: str | Path, batch_id: str) -> Path:
    return Path(task_dir) / "artifacts" / "adoption" / batch_id


def _status_path(task_dir: str | Path, batch_id: str) -> Path:
    return _batch_dir(task_dir, batch_id) / "status.json"


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")


def _read_status_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise BatchError(f"missing batch status: {path}") from exc


def _atomic_create_status(path: Path, value: dict[str, Any]) -> None:
    """Create *path* exactly once via durable temp + hard-link publication.

    Same-directory temp file, write/flush/fsync, publish via ``os.link`` (raises
    ``FileExistsError`` on an existing target — the collision check, no separate ``exists()``
    race), best-effort parent-directory fsync, always unlink the temp name in ``finally``.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise BatchError(f"batch status already exists: {path}") from exc
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _atomic_replace_status(path: Path, value: dict[str, Any]) -> None:
    """Durably replace *path* with a same-directory temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def batch_id_for(target_ref: str, discovered_at: datetime | None = None) -> str:
    """Content-derive a ``<batch-id>`` from ``(target_ref, discover-time UTC date)`` (D-02).

    Deterministic given the same ``(target_ref, date)`` pair: two calls on the same UTC calendar
    date with the same ``target_ref`` return the SAME id; a different ``target_ref`` OR a different
    UTC date returns a DIFFERENT id.
    """
    moment = discovered_at or datetime.now(UTC)
    date = moment.date().isoformat()
    return hashlib.sha256(f"{target_ref}|{date}".encode()).hexdigest()[:16]


def create_or_resume_batch(
    task_dir: str | Path, target_ref: str, *, discovered_at: datetime | None = None
) -> dict[str, Any]:
    """Create a new batch, or safely resume an existing same-day batch for the same ``target_ref``.

    If ``status.json`` already exists at the computed batch directory, this is a SAFE RESUME — the
    existing status dict is read and returned UNMODIFIED (no write, no revision bump, no lock
    taken). Otherwise the directory is created and a fresh ``status.json`` is written at
    ``revision: 0``.
    """
    moment = discovered_at or datetime.now(UTC)
    batch_id = batch_id_for(target_ref, moment)
    status_path = _status_path(task_dir, batch_id)
    if status_path.is_file():
        return json.loads(_read_status_bytes(status_path))
    status = {
        "batch_id": batch_id,
        "target_ref": target_ref,
        "discovered_at": moment.date().isoformat(),
        "revision": 0,
    }
    _atomic_create_status(status_path, status)
    return status


def read_status(task_dir: str | Path, batch_id: str) -> dict[str, Any] | None:
    """Return the parsed ``status.json`` for *batch_id*, or ``None`` if absent.

    Pure read, no lock.
    """
    path = _status_path(task_dir, batch_id)
    if not path.is_file():
        return None
    return json.loads(path.read_bytes())


def update_status(
    task_dir: str | Path, batch_id: str, expected_revision: int, patch: dict[str, Any]
) -> dict[str, Any]:
    """CAS-guarded mutation of a batch's ``status.json``.

    Reuses the exact ``manager.py::_cas_write`` shape scoped to this batch's own ``status.json``
    (own sidecar ``.status.json.lock``, own ``fcntl.flock(LOCK_EX)``): re-read current status,
    raise ``BatchError`` if the current revision does not match *expected_revision*, require the
    merged next status to advance revision by exactly one, then atomic-replace.
    """
    if type(expected_revision) is not int or expected_revision < 0:
        raise BatchError("expected revision must be a non-negative integer")
    path = _status_path(task_dir, batch_id)
    lock_path = path.with_name(f".{path.name}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        current = json.loads(_read_status_bytes(path))
        if current["revision"] != expected_revision:
            raise BatchError(
                f"stale writer: expected revision {expected_revision}, found {current['revision']}"
            )
        next_status = dict(current)
        next_status.update(patch)
        if next_status["revision"] != expected_revision + 1:
            raise BatchError("mutation must increment revision by exactly one")
        _atomic_replace_status(path, next_status)
        return next_status
