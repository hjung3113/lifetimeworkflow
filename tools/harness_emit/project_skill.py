"""Skill frontmatter projection + references discovery (EMIT-02 — divergence = None).

A ``harness/skills/<name>/SKILL.md`` frontmatter carries ``name`` (== the directory) and
``description``. Unlike agents/commands, a skill has NO per-runtime divergence: opencode and Claude
keep the SAME two keys, so ``to_opencode`` and ``to_claude`` both return the identical projection
(the Mapping Table cell is None). The progressively-disclosed ``references/`` subtree is copied
BYTE-FOR-BYTE to both trees by the emitter — this module only ENUMERATES it (sorted, symlink-safe)
so ``generate.emit`` can route each copy target through ``_confine`` (T-07-01).
"""

from __future__ import annotations

from pathlib import Path

# Fixed key order — identical for both runtimes (no divergence).
_SKILL_KEYS = ("name", "description")


def _project(fm: dict, keys: tuple[str, ...]) -> dict:
    """Select ``keys`` from ``fm`` in order, dropping absent/None values — values pass unchanged."""
    return {k: fm[k] for k in keys if k in fm and fm[k] is not None}


def project(fm: dict) -> dict:
    """Project a skill's frontmatter (name + description) — the SAME shape for both runtimes."""
    return _project(fm, _SKILL_KEYS)


def to_opencode(fm: dict) -> dict:
    """opencode skill shape — identical to the Claude shape (name + description)."""
    return project(fm)


def to_claude(fm: dict) -> dict:
    """Claude skill shape — identical to the opencode shape (name + description)."""
    return project(fm)


def iter_reference_files(references_dir: str | Path) -> list[Path]:
    """Yield each regular file under ``references/`` as a path RELATIVE to it, sorted, symlink-safe.

    Returns ``[]`` when the directory is absent (the common case — only golden-debug and
    polyglot-boundary carry a ``references/`` subtree). Symlinks are skipped so a link pointing
    outside the subtree can never be followed into the emitted tree (T-07-01, mirrors the docs_sync
    ``iter_*`` traversal defense); the emitter still ``_confine``s every resolved target.
    """
    root = Path(references_dir)
    if not root.exists() or not root.is_dir():
        return []
    files: list[Path] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        # Defence-in-depth: skip anything whose real path escaped the references subtree.
        resolved = path.resolve()
        if root.resolve() not in resolved.parents:
            continue
        files.append(path.relative_to(root))
    return files
