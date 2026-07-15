"""Generalized GEN-04 core→workspace-member single-direction guard (MREPO-04).

The twin of ``test_core_no_example_dep.py``, raised one level: it proves the template invariant
that keeps the harness reusable across workspaces — nothing under the CORE planes (``tools/``,
``harness/``, ``libs/``) may path-reference a workspace MEMBER root declared in ``workspace.toml``.
A core file that grows a ``tests/fixtures/workspace/member-a`` path marker is a
one-directional-dependency leak (the core must depend on NO member) that RED-flags the suite
(T-11-04). The negative-control tests below prove the scan is live and cannot silently no-op.

The forbidden path markers are NOT hardcoded: they are resolved at test time from the manifest via
``members(load_workspace())`` — so the guard automatically tracks the declared member roots and a
new member widens the guard with no edit here (Pitfall 3). The 11-01 loader carries no member marker
(it reads the manifest at runtime) so it passes clean.

The ONE sanctioned exemption is key-scoped to ``workspace.toml``: the ``root =`` / ``from =`` /
``to =`` / ``contract =`` pointer lines are the only place a config file may name a member
(ADR-0002 (c) precedent). The exemption is NOT a blanket file pass — a member path on any OTHER
key in ``workspace.toml`` is still flagged (T-11-05).

Mirrors the structural-scan idiom of ``test_core_no_example_dep.py``: repo root via ``parents[3]``,
tracked set discovered with ``git ls-files`` (subprocess, ``shell=False``, ``check=True``), no
runtime import of any member module.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from tools.workspace_config import load_workspace, members

# test_core_no_workspace_member_dep.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Core planes whose tracked files must not depend on any workspace member.
_CORE_ROOTS = ("tools", "harness", "libs")

# This guard file itself holds member-root path strings as negative-control literals; it is EXCLUDED
# from the scanned set (scan the tracked core set MINUS this file), or the guard would flag itself.
_SELF = Path(__file__).resolve()

# The single sanctioned member-pointer file: the root ``workspace.toml``. Its ``root =`` member-root
# values (and, defensively, the ``from =`` / ``to =`` / ``contract =`` edge-endpoint keys) are the
# ONE place a config file may name a member — ADR-0002 (c) precedent. The whole pointer line is
# exempted. Note ``workspace.toml`` lives at the repo ROOT, not under a core plane, so the live
# ``git ls-files`` sweep never scans it; the exemption logic is exercised by the explicit unit tests
# below (which pass ``_WORKSPACE_FILE`` as the rel path directly).
_WORKSPACE_FILE = "workspace.toml"

# Matches the sanctioned workspace-pointer keys in workspace.toml: ``root = ...`` (member root, a
# standalone key) and the ``from = ...`` / ``to = ...`` / ``contract = ...`` edge-endpoint keys
# (ADR-0002 (c)). Real edges are a single-line INLINE TABLE
# (``{ from = "…", to = "…", contract = "…" }``), so from/to/contract are NOT the first token on the
# line — they follow ``{`` or ``,``. The key may therefore appear either at line start (optionally
# indented, the standalone ``root =``) OR right after ``{``/``,`` (the inline-table keys); matched
# via ``.search`` (WR-01: a leading-anchored ``.match`` never matched the real inline-table edge).
_WORKSPACE_POINTER_LINE = re.compile(r"(?:^\s*|[{,]\s*)(root|from|to|contract)\s*=")


def _member_roots() -> set[str]:
    """Resolve the forbidden member-root path markers from the manifest at test time.

    Derived from ``members(load_workspace())`` — never hardcoded — so the guard tracks the declared
    ``[[members]].root`` values (e.g. ``tests/fixtures/workspace/member-a``) and a new member widens
    it automatically.
    """
    return {m["root"] for m in members(load_workspace())}


def _tracked_core_files() -> list[Path]:
    """Tracked files under the core planes (``git ls-files``), MINUS this guard file itself."""
    completed = subprocess.run(
        ["git", "ls-files", *_CORE_ROOTS],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    files: list[Path] = []
    for rel in completed.stdout.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        resolved = (_REPO_ROOT / rel).resolve()
        if resolved == _SELF:
            continue  # negative-control literals live here — never scan self
        files.append(resolved)
    return files


def _is_workspace_pointer_line(rel_path: str, line: str) -> bool:
    """The one sanctioned exemption: the ``root =`` / ``from =`` / ``to =`` / ``contract =``
    member-pointer lines in ``workspace.toml`` (ADR-0002 (c)) — the only config place that may name a
    member. Key-scoped: any member path on a NON-pointer key stays flagged. Uses ``.search`` (not
    ``.match``) so the inline-table edge keys (``{ from = … }``) — never the first token — match."""
    return rel_path == _WORKSPACE_FILE and _WORKSPACE_POINTER_LINE.search(line) is not None


def _scan_lines(rel_path: str, text: str, roots: set[str] | None = None) -> list[tuple[int, str]]:
    """Return ``(lineno, line)`` hits: a core line containing a workspace member-root path marker,
    skipping the sanctioned ``workspace.toml`` member-pointer (``root =`` / ``from =`` / ``to =`` /
    ``contract =``) lines. ``roots`` defaults to the live manifest member roots."""
    if roots is None:
        roots = _member_roots()
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _is_workspace_pointer_line(rel_path, line):
            continue
        if any(marker in line for marker in roots):
            hits.append((lineno, line))
    return hits


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None  # binary/unreadable — no textual dependency to scan


def test_core_has_no_workspace_member_dependency() -> None:
    """No tracked file under tools/, harness/, libs/ path-references a declared workspace member root
    (the core depends on NO member — the template invariant, MREPO-04)."""
    roots = _member_roots()
    assert roots, "no member roots resolved from workspace.toml — the guard would be a silent no-op"
    offenders: list[str] = []
    for path in _tracked_core_files():
        text = _read_text(path)
        if text is None:
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for lineno, line in _scan_lines(rel, text, roots):
            offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "core→workspace-member dependency leak — core planes must not name a workspace member root:\n"
        + "\n".join(offenders)
    )


def test_negative_control_flags_synthetic_member_ref() -> None:
    """Scan is live: a crafted core line naming a real member root IS flagged (cannot silently no-op).

    Uses the first live member root so the literal always matches a declared path marker."""
    marker = sorted(_member_roots())[0]
    hits = _scan_lines("tools/fake_core_module.py", f'x = "{marker}/foo"')
    assert hits, "negative control failed: scan did not flag a synthetic workspace-member reference"


def test_workspace_root_pointer_is_exempt() -> None:
    """The sanctioned workspace.toml ``root =`` member-pointer is exempt even though it names a member
    root (ADR-0002 (c))."""
    marker = sorted(_member_roots())[0]
    hits = _scan_lines(_WORKSPACE_FILE, f'root = "{marker}"')
    assert not hits, "the sanctioned workspace.toml root pointer must be exempt from the guard"


def test_inline_table_edge_pointer_is_exempt() -> None:
    """The REAL workspace.toml edge is a single-line inline table
    (``{ from = …, to = …, contract = … }``): its from/to/contract pointer keys are NOT the first
    token on the line, so the exemption must match them mid-line (WR-01 — a leading-anchored
    ``.match`` never matched this). A member root carried on an inline-table pointer key is exempt.
    """
    marker = sorted(_member_roots())[0]
    line = f'  {{ from = "{marker}", to = "member-b:ingest", contract = "greeting" }},'
    hits = _scan_lines(_WORKSPACE_FILE, line)
    assert not hits, (
        "the inline-table edge pointer keys must be exempt against the REAL edge syntax "
        f"(line: {line!r})"
    )


def test_real_workspace_edge_line_is_recognized_as_pointer() -> None:
    """Prove the exemption against the VERBATIM edge line in the committed workspace.toml (not a
    synthetic stand-in): every inline-table edge line is recognized as a sanctioned pointer (WR-01).
    """
    ws_text = (_REPO_ROOT / _WORKSPACE_FILE).read_text(encoding="utf-8")
    edge_lines = [
        ln for ln in ws_text.splitlines() if "from =" in ln and "to =" in ln and "contract =" in ln
    ]
    assert edge_lines, "expected at least one inline-table edge line in workspace.toml"
    for ln in edge_lines:
        assert _is_workspace_pointer_line(_WORKSPACE_FILE, ln), (
            f"real inline-table edge line not recognized as a sanctioned pointer: {ln!r}"
        )


def test_negative_control_flags_nonexempt_workspace_leak() -> None:
    """Scan stays LIVE in workspace.toml: a member path on a NON-pointer key (not
    root/from/to/contract) is still flagged — the exemption is key-scoped, not a blanket file pass
    (T-11-05)."""
    marker = sorted(_member_roots())[0]
    hits = _scan_lines(_WORKSPACE_FILE, f'member = "{marker}"')
    assert hits, (
        "negative control failed: a non-pointer member leak in workspace.toml must be flagged"
    )
