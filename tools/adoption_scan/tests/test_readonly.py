"""Byte-invariance proof (constraint: this plan is read-only-by-design).

The scanned target tree must be provably unchanged after a full ``build_inventory`` call — every
regular file's sha256 identical before and after, and the escaping symlink's own target string
identical (never followed, never rewritten).
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from tools.adoption_scan import scan


def _tree_snapshot(root: Path) -> dict[str, tuple[str, str]]:
    """Map ``relative path -> ("file", sha256)`` or ``("symlink", target)`` for every entry."""
    snapshot: dict[str, tuple[str, str]] = {}
    for p in sorted(root.rglob("*")):
        rel = str(p.relative_to(root))
        if p.is_symlink():
            try:
                target = os.readlink(p)
            except OSError:
                continue
            snapshot[rel] = ("symlink", target)
        elif p.is_file():
            snapshot[rel] = ("file", hashlib.sha256(p.read_bytes()).hexdigest())
    return snapshot


def test_target_tree_byte_unchanged_after_scan(tmp_minirepo: Path) -> None:
    before = _tree_snapshot(tmp_minirepo)
    scan.build_inventory(tmp_minirepo)
    after = _tree_snapshot(tmp_minirepo)
    assert before == after


def test_target_tree_byte_unchanged_after_repeated_scans(tmp_minirepo: Path) -> None:
    before = _tree_snapshot(tmp_minirepo)
    scan.build_inventory(tmp_minirepo)
    scan.build_inventory(tmp_minirepo)
    after = _tree_snapshot(tmp_minirepo)
    assert before == after
