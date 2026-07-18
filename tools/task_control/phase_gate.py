"""Deterministic, fail-closed phase-start checks; no claim of human understanding."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from tools.task_control.manager import ATTESTATION_SCHEMA, TaskControlError, _json, _validate_document, missing_artifacts, orphan_artifacts, sha256, show


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], text=True, capture_output=True, check=False)
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise TaskControlError(f"git {' '.join(args)} failed: {detail or 'unknown git error'}")
    return result.stdout.strip()


def _is_ancestor(root: Path, base: str, head: str) -> bool:
    """Return False only for git's ordinary non-ancestor result; surface real git failures."""
    result = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, head], text=True, capture_output=True, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    detail = result.stderr.strip() or result.stdout.strip()
    raise TaskControlError(f"git merge-base failed: {detail or 'unknown git error'}")


def phase_gate(task_dir: str | Path, expected_revision: int, *, repo_root: str | Path | None = None, baseline: str | None = None, prohibited_actions: list[str] | None = None) -> list[str]:
    """Return refresh items, raising a single deterministic error when any are needed."""
    packet = Path(task_dir).resolve()
    root = Path(repo_root).resolve() if repo_root else Path(_git(packet, "rev-parse", "--show-toplevel")).resolve()
    refresh: list[str] = []
    try:
        state = show(packet)
    except TaskControlError as exc:
        raise TaskControlError(f"refresh required: state ({exc})") from exc
    if state["revision"] != expected_revision:
        refresh.append("state revision")
    expected_packet = root / ".workflow" / "tasks" / state["task_id"]
    if packet != expected_packet:
        refresh.append("worktree task path")
    head = _git(root, "rev-parse", "HEAD")
    if state["current_ref"] != head:
        refresh.append("current ref")
    if baseline is not None and state["baseline"]["commit"] != baseline:
        refresh.append("baseline commit")
    if not _is_ancestor(root, state["baseline"]["commit"], "HEAD"):
        refresh.append("baseline commit")
    if state["blockers"]:
        refresh.append("unresolved blockers")
    refresh.extend(f"required artifact: {name}" for name in missing_artifacts(packet))
    refresh.extend(f"orphan artifact: {path}" for path in orphan_artifacts(packet))
    task = _json(packet / "task.json")
    if task.get("task_id") != state["task_id"]:
        refresh.append("task/state task ID")
    attestation_path = packet / "context-attestation.json"
    try:
        attestation = _json(attestation_path)
        _validate_document("context-attestation", attestation, ATTESTATION_SCHEMA)
        records = attestation.get("constraints") if isinstance(attestation.get("constraints"), list) else []
    except TaskControlError:
        records = []
    by_id = {item.get("constraint_id"): item for item in records if isinstance(item, dict)}
    phase = state["phase"]
    for constraint in task.get("constraints", []):
        record = by_id.get(constraint["id"])
        source = root / constraint["source_path"]
        if not source.is_file() or not record:
            refresh.append(f"constraint: {constraint['id']}")
            continue
        if record.get("source_path") != constraint["source_path"] or record.get("source_sha256") != constraint["source_sha256"] or sha256(source) != constraint["source_sha256"]:
            refresh.append(f"constraint source: {constraint['id']}")
        applies = record.get("applies_to_phases")
        if not isinstance(applies, list) or phase not in applies:
            refresh.append(f"constraint phase coverage: {constraint['id']}")
        mapping = record.get("planned_action_mapping")
        if not isinstance(mapping, list) or not mapping:
            refresh.append(f"constraint action mapping: {constraint['id']}")
        if phase in {"VERIFY", "COMPLETE"} and (not isinstance(record.get("required_evidence_ids"), list) or not record["required_evidence_ids"]):
            refresh.append(f"constraint evidence: {constraint['id']}")
        prohibited = record.get("prohibited_action_ids", [])
        if prohibited_actions and set(prohibited_actions) & set(prohibited):
            refresh.append(f"prohibited action: {constraint['id']}")
    if refresh:
        raise TaskControlError("refresh required: " + ", ".join(sorted(set(refresh))))
    return []
