"""pointer-index generator — scan roots → "what points to each memory item" (MEM2-07, SC2, D-16-02).

The load-bearing new engine of Phase 16. It enumerates the memory items (the two
``.memory/state`` files plus every ``.memory/agreements`` file — active AND retired, via the
read-only :func:`tools.harness_lint.agreements.iter_agreement_files`), scans a fixed set of roots
line-by-line, and records every referrer as ``{"file", "line", "kind"}`` keyed by memory item. The
result is the data source for the UI's Referrers panel (16-03) and the referential-integrity orphan
check (16-05).

A faithful clone of :mod:`tools.memory_regen.repo_map`'s generator shape — module-level paths +
``DERIVED_HEADER``, the ``build_index → render_md → write → main`` quartet, deterministic sort, and
NO timestamp/wall-clock/float. Determinism (delete + regenerate byte-identical — success criterion
2, Pitfall 1) is proven by a committed syrupy snapshot and a write→hash→delete→regenerate test —
NOT by ``git diff`` (the target is gitignored, Pitfall 2).

Tier contract (T-16-10): this module READS ``.memory/agreements/`` but MUST NEVER write it — it
writes ONLY under the gitignored ``.memory/derived/`` plane.

Path-traversal defense (T-16-01): each directory scan-root walk is confined to its resolved subtree
and symlinks escaping the tree are skipped — mirroring :func:`repo_map._iter_source_files`.

Entrypoint: ``python -m tools.memory_regen.pointer_index``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from tools.harness_lint.agreements import iter_agreement_files

# --- paths (derived plane is gitignored + regenerated every session, D-16-02) -----------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
JSON_PATH = DERIVED_DIR / "pointer-index.json"
MD_PATH = DERIVED_DIR / "pointer-index.md"

# --- stable text (part of the derived-plane contract) -----------------------------------------
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/pointer_index.py)"

# The two state-plane memory items (enumerated even with zero referrers).
_STATE_ITEMS = ("activeContext.md", "progress.md")

# Text suffixes scanned (allow-list); a suffixless file is treated as ``.md``.
_TEXT_SUFFIXES = frozenset({".md", ".ts", ".py", ".json", ".toml"})

# The derived plane is excluded from every walk (self-reference churn guard, T-16-11).
_DERIVED_MARKER = ".memory/derived/"


def _default_scan_roots() -> list[Path]:
    """The production scan roots (D-16-02): recursive dirs + single-file roots."""
    return [
        _REPO_ROOT / "docs",
        _REPO_ROOT / "harness",
        _REPO_ROOT / "tools" / "memory_regen" / "inject.py",
        _REPO_ROOT / ".memory" / "README.md",
        _REPO_ROOT / "AGENTS.md",
    ]


def _rel(path: Path, base: Path) -> str:
    """Repo-relative POSIX key for ``path`` under ``base`` (falls back to the raw POSIX path)."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(base).as_posix()
    except ValueError:
        return path.as_posix()


def _iter_scan_files(scan_roots: list[Path]) -> list[Path]:
    """Yield scannable text files under each root, symlink-confined (T-16-01), de-duped, sorted.

    A root may be a single file (scanned directly) or a directory (walked recursively). Non-text
    suffixes are skipped via the allow-list (suffixless treated as ``.md``); anything under
    ``.memory/derived/`` is excluded so the generator never scans its own output.
    """
    files: list[Path] = []
    seen: set[Path] = set()
    for root in scan_roots:
        root = Path(root)
        if not root.exists():
            continue
        if root.is_file():
            candidates: list[Path] = [root]
            confine = False
            root_resolved = root.resolve()
        else:
            root_resolved = root.resolve()
            candidates = [p for p in sorted(root.rglob("*")) if p.is_file()]
            confine = True
        for p in candidates:
            resolved = p.resolve()
            # Defense-in-depth: skip anything a symlink points outside the subtree (repo_map idiom).
            if confine and root_resolved != resolved and root_resolved not in resolved.parents:
                continue
            suffix = p.suffix
            if suffix != "" and suffix not in _TEXT_SUFFIXES:
                continue
            if _DERIVED_MARKER in resolved.as_posix():
                continue
            if resolved in seen:
                continue
            seen.add(resolved)
            files.append(p)
    return sorted(files, key=lambda x: x.resolve().as_posix())


def build_index(
    *,
    base_dir: str | Path | None = None,
    scan_roots: list[Path] | None = None,
) -> dict:
    """Scan the roots and build ``{memory-item: [{"file","line","kind"}, ...]}`` (SC2).

    Memory items = the two ``.memory/state`` files plus every agreement (active + retired) under
    ``base_dir/.memory/agreements`` — each present even with zero referrers (empty list). A referrer
    is recorded when a scanned line contains (a) the item's ``.memory/...`` POSIX path string
    (``kind="path"``), or (b) for agreements only, the slug as a word-boundaried token
    (``kind="slug"``). A full-path hit is preferred over a bare-slug hit on the same line/item. Keys
    and each referrer list are sorted; all paths are repo-relative POSIX (Pitfall 1).
    """
    base = Path(base_dir).resolve() if base_dir is not None else _REPO_ROOT
    if scan_roots is None:
        scan_roots = _default_scan_roots()

    state_dir = base / ".memory" / "state"
    agreements_dir = base / ".memory" / "agreements"

    # item key -> (path string to match, slug or None)
    path_by_item: dict[str, str] = {}
    slug_by_item: dict[str, str] = {}
    for name in _STATE_ITEMS:
        key = _rel(state_dir / name, base)
        path_by_item[key] = key
    for p in iter_agreement_files(agreements_dir):
        key = _rel(p, base)
        path_by_item[key] = key
        slug_by_item[key] = p.stem

    slug_res = {
        key: re.compile(r"(?<![\w-])" + re.escape(slug) + r"(?![\w-])")
        for key, slug in slug_by_item.items()
    }

    referrers: dict[str, set[tuple[str, int, str]]] = {key: set() for key in path_by_item}

    for f in _iter_scan_files([Path(r) for r in scan_roots]):
        frel = _rel(f, base)
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            for key, path_str in path_by_item.items():
                if path_str in line:
                    referrers[key].add((frel, lineno, "path"))
                    continue
                pattern = slug_res.get(key)
                if pattern is not None and pattern.search(line):
                    referrers[key].add((frel, lineno, "slug"))

    return {
        key: [
            {"file": file, "line": line, "kind": kind}
            for file, line, kind in sorted(referrers[key])
        ]
        for key in sorted(referrers)
    }


def render_md(index: dict) -> str:
    """Render the DERIVED-marked, deterministically-sorted markdown twin (no timestamp/float).

    First line is ``# {DERIVED_HEADER}``; then a stable table of ``memory item`` →
    ``referrer/line/kind`` rows. Items with no referrers render a single ``(none)`` row. Contains
    NO timestamp and NO raw
    float so generating twice is byte-identical (Pitfall 1). Trailing newline for POSIX-clean text.
    """
    lines = [
        f"# {DERIVED_HEADER}",
        "",
        "Reference index — what points to each memory item "
        "(`python -m tools.memory_regen.pointer_index`). "
        f"{len(index)} memory item(s); referrer/line/kind only, no scores; regenerated each "
        "session.",
        "",
        "| memory item | referrer | line | kind |",
        "| --- | --- | --- | --- |",
    ]
    for item in sorted(index):
        refs = index[item]
        if not refs:
            lines.append(f"| {item} | (none) | | |")
            continue
        for ref in refs:
            lines.append(f"| {item} | {ref['file']} | {ref['line']} | {ref['kind']} |")
    return "\n".join(lines) + "\n"


def write(
    json_path: str | Path = JSON_PATH,
    md_path: str | Path = MD_PATH,
    *,
    base_dir: str | Path | None = None,
    scan_roots: list[Path] | None = None,
) -> tuple[Path, Path]:
    """Regenerate the derived pointer-index and write both twins (mkdir parents), returning paths.

    The ``.json`` is ``json.dumps(index, indent=2, sort_keys=True) + "\\n"`` (byte-stable); the
    ``.md`` is :func:`render_md`. Writes ONLY under the given paths (default: the gitignored
    ``.memory/derived/`` plane) — never touches ``.memory/agreements/`` (tier contract T-16-10).
    """
    index = build_index(base_dir=base_dir, scan_roots=scan_roots)
    jp = Path(json_path)
    mp = Path(md_path)
    jp.parent.mkdir(parents=True, exist_ok=True)
    mp.parent.mkdir(parents=True, exist_ok=True)
    jp.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    mp.write_text(render_md(index), encoding="utf-8")
    return jp, mp


def main(argv: list[str] | None = None) -> int:
    """CLI: regenerate ``.memory/derived/pointer-index.{json,md}`` (`python -m ...pointer_index`).

    Writes to the real gitignored derived plane via the module-level default paths.
    """
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    jp, mp = write()
    for out in (jp, mp):
        print(f"wrote {out.relative_to(_REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
