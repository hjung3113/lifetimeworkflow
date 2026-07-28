"""Workspace-aware golden path resolution + widened ``_confine`` allowlist (MREPO-03).

Proves:

* (a) an edge-spanning golden case resolves under its declared member root via
  :func:`workspace_golden_case` and PASSes with the language-agnostic ``identity`` converter
  (no .NET) — the in-repo demo fixture confines cleanly under the default allowlist;
* (b) NEGATIVE CONTROL — the widening EXTENDS, never removes, the escape guard: a path outside
  REPO_ROOT, ``/tmp``, and every threaded member/extra root STILL raises ``GoldenRunnerError``;
* (c) the additive ``allowed_roots`` thread ADMITS a path under a threaded root that the base
  allowlist would otherwise reject, and a real declared member-root path confines.

GEN-04 core-plane invariant (this file lives under ``tools/``): the member root(s) it exercises
are resolved at RUNTIME via ``tools.workspace_config.members()``/``load_workspace()`` — NEVER as a
hardcoded member-root path literal — so it passes the 11-02 generalized GEN-04 guard
(``test_core_no_workspace_member_dep.py``).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from golden_runner.runner import (
    GoldenRunnerError,
    _confine,
    workspace_golden_case,
)

from tools.workspace_config import load_workspace, members

# tests -> golden_runner -> tools -> repo root (mirrors conftest.py).
_REPO_ROOT = Path(__file__).resolve().parents[4]

# The edge-spanning golden case shipped by 11-01 (a case id, not a member-root path literal).
_EDGE_CASE = "greeting-edge"


def _member_roots() -> list[Path]:
    """Absolute declared member roots, resolved from the manifest at runtime (no path literals)."""
    return [(_REPO_ROOT / m["root"]).resolve() for m in members(load_workspace())]


def _member_with_case(case: str) -> tuple[str, Path]:
    """Resolve (id, absolute root) of the member that owns ``golden/<case>`` — via the loader."""
    for m in members(load_workspace()):
        root = (_REPO_ROOT / m["root"]).resolve()
        if (root / "golden" / case).is_dir():
            return m["id"], root
    raise AssertionError(f"no declared member owns golden/{case}")


def test_workspace_golden_case_passes_via_member_root(tmp_path: Path) -> None:
    """The edge-spanning case runs under its member's golden dir (identity converter) and PASSes."""
    member_id, _root = _member_with_case(_EDGE_CASE)
    out = tmp_path / "out.tsv"

    result = workspace_golden_case(_EDGE_CASE, member_id, out, converter="identity")

    assert result.passed, f"workspace golden case should PASS; diff:\n{result.diff}"
    assert result.received_path is None  # PASS never writes a .received


def test_confine_rejects_path_outside_all_roots() -> None:
    """NEGATIVE CONTROL: a path outside repo/temp AND every threaded root still raises (guard intact).

    The declared member roots plus a synthetic extra root are threaded in; a path under none of
    them must be rejected — the widening extends the allowlist, it does not remove the guard."""
    threaded = tuple(_member_roots()) + (Path("/opt/synthetic-member-xyz"),)
    outside = Path("/opt/definitely-outside-abc123/case/input/seed.tsv")
    with pytest.raises(GoldenRunnerError):
        _confine(outside, allowed_roots=threaded)


def test_confine_widening_admits_threaded_root() -> None:
    """The additive thread ADMITS a path under a root the base allowlist would reject."""
    extra = Path("/opt/synthetic-member-xyz")
    inside = extra / "golden" / "case" / "input" / "seed.tsv"

    # Base allowlist (repo/temp only) rejects it …
    with pytest.raises(GoldenRunnerError):
        _confine(inside)
    # … threading the extra root admits it (guard extended, not removed).
    assert _confine(inside, allowed_roots=(extra,)) == inside.resolve()


def test_confine_admits_real_member_root_path() -> None:
    """A path inside a declared member root confines successfully when that root is threaded."""
    _member_id, root = _member_with_case(_EDGE_CASE)
    seed = root / "golden" / _EDGE_CASE / "input" / "seed.tsv"
    assert _confine(seed, allowed_roots=(root,)) == seed.resolve()
