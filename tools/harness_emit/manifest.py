"""Ownership manifest — prune-then-write, gsd-* exclusion (EMIT-02, D-03).

The emitter owns ONLY the files it lists in a committed manifest. On each run it PRUNES prior-owned
paths that are no longer emitted (a renamed/removed source artifact leaves no orphan), then writes
the current set — while NEVER enumerating or touching GSD-owned paths (``gsd-*`` files,
``.claude/get-shit-done/**``, ``.claude/hooks/**``, ``.claude/commands/gsd/**``). Manifest set-diff
mirrors the ``tools/contract_drift`` idiom; the JSON is emitted with sorted keys + a trailing LF so
re-emit is byte-identical (the drift gate depends on it).
"""

from __future__ import annotations

import json
from pathlib import Path

# GSD-owned lanes the emitter must NEVER prune or write (D-03). Matched as path fragments (any
# separator style) plus a per-file ``gsd-`` name prefix.
_GSD_DIR_FRAGMENTS = (
    ".claude/get-shit-done/",
    ".claude/hooks/",
    ".claude/commands/gsd/",
)
_GSD_NAME_PREFIX = "gsd-"


def is_gsd_owned(rel: str) -> bool:
    """True iff ``rel`` (repo-relative POSIX path) is in a GSD-owned lane — never emit-managed."""
    normalized = rel.replace("\\", "/")
    if any(frag in normalized for frag in _GSD_DIR_FRAGMENTS):
        return True
    return normalized.rsplit("/", 1)[-1].startswith(_GSD_NAME_PREFIX)


def load_manifest(manifest_path: str | Path) -> list[str]:
    """Load the previously-committed owned-path list (``[]`` when the manifest is absent)."""
    p = Path(manifest_path)
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return list(data.get("paths", []))


def _rel(path: Path, root: Path) -> str:
    """Repo-relative POSIX path of ``path`` under ``root`` (stable, location-agnostic key)."""
    return Path(path).resolve().relative_to(Path(root).resolve()).as_posix()


def _confined(path: Path, root: Path) -> Path | None:
    """Resolved ``path`` iff it stays under ``root``; ``None`` if it would escape.

    The prune loop DELETES, and its input paths come from the on-disk prior manifest (external
    data). A tampered/corrupt entry (``../../etc/passwd``, an absolute path, or a symlink that
    resolves outside) must never let ``unlink`` reach beyond the emit root — mirror the
    ``generate._confine`` traversal guard, but skip (return ``None``) rather than raise so one bad
    entry cannot abort the whole emit. ``.resolve()`` collapses symlinks, so symlink escapes fail
    confinement too.
    """
    resolved = path.resolve()
    root_resolved = Path(root).resolve()
    if root_resolved != resolved and root_resolved not in resolved.parents:
        return None
    return resolved


def prune_then_write(
    written: list[Path],
    manifest_path: str | Path,
    root: Path,
) -> Path:
    """Prune stale prior-owned files, then write the manifest of the currently-emitted paths.

    ``written`` are absolute paths just emitted (under ``root``). Any path in the PRIOR manifest
    absent from the current set is deleted — EXCEPT anything in a GSD-owned lane, which is never
    touched (defensive; the manifest only ever holds harness paths). The manifest JSON is
    ``sort_keys=True, indent=2`` + trailing LF (deterministic).
    """
    root = Path(root)
    current = sorted(_rel(p, root) for p in written)
    current_set = set(current)

    for rel in load_manifest(manifest_path):
        if rel in current_set or is_gsd_owned(rel):
            continue
        stale = _confined(root / rel, root)
        if stale is None:
            continue  # manifest entry escapes the emit root — never delete outside confinement
        if stale.exists():
            stale.unlink()

    manifest = {"tool": "tools.harness_emit", "paths": current}
    out = Path(manifest_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return out
