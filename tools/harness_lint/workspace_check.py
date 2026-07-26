"""Standalone workspace-resolvability check — runs on BARE ``python3``, never through ``uv``.

Run as::

    python3 tools/harness_lint/workspace_check.py

Stdlib only, no imports from this repo, no package install, no virtualenv. That independence is the
entire point and must not be optimised away. It also does not assume Python 3.11: ``tomllib`` is
used when present and a deliberately tiny regex reader covers the two fields this check needs on an
older system ``python3``, because the whole value of this module is running on whatever interpreter
happens to exist when the workspace is broken.

WHY THIS IS NOT A PYTEST TEST
-----------------------------
``pyproject.toml`` declares ``members = ["libs/python", "tools/*"]`` and uv requires every directory
matched by that glob to contain a ``pyproject.toml``. The moment ``tools/<name>/`` exists without
one, every ``uv`` invocation in the repo fails at workspace resolution::

    error: Workspace member `.../tools/<name>` is missing a `pyproject.toml` (matches: `tools/*`)

``uv run pytest`` is a ``uv`` invocation. So is every PreToolUse guard in this repo
(``contract_guard``, ``secret_scan``, ``commit_gate``, ``resume_gate``), each
invoked as ``uv run python -m tools.hooks.<name>``. When workspace resolution fails the guards
fail, and a failing PreToolUse guard DENIES its tool — correctly, since a guard that cannot run
must not
wave writes through. The result is that file-write and shell tools stop working at the same
moment, including the ones that would create the missing file.

A pytest test for this condition therefore **cannot fire on the condition**: uv dies before pytest
starts. Shipping one would be a claimed control that does not exist — the exact defect this
milestone was convened to remove — so the real check lives here, reachable without uv, and the
pytest twin in ``tests/test_workspace_member_completeness.py`` exists only to prove this module's
logic is correct, never to be the gate.

Exit codes: ``0`` resolvable, ``1`` a globbed Python directory has no ``pyproject.toml``,
``2`` the check could not run (missing/unparseable root ``pyproject.toml``).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

try:  # pragma: no cover - branch depends on the interpreter, both are exercised in CI
    import tomllib

    _HAVE_TOMLLIB = True
except ModuleNotFoundError:  # Python < 3.11 — the system python3 on some dev machines
    _HAVE_TOMLLIB = False

REPO_ROOT = Path(__file__).resolve().parents[2]


class WorkspaceCheckError(Exception):
    """The check could not be performed (unreadable or unparseable root pyproject)."""


_WORKSPACE_TABLE = re.compile(r"^\[tool\.uv\.workspace\]\s*$", re.MULTILINE)
_NEXT_TABLE = re.compile(r"^\[", re.MULTILINE)


def _array_field(body: str, key: str) -> list[str]:
    """Extract a single-line or multi-line TOML string array by key, comments stripped."""
    match = re.search(rf"^\s*{key}\s*=\s*\[(.*?)\]", body, re.MULTILINE | re.DOTALL)
    if not match:
        return []
    without_comments = re.sub(r"#[^\n]*", "", match.group(1))
    return re.findall(r"""["']([^"']+)["']""", without_comments)


def _read_workspace(pyproject: Path) -> tuple[list[str], list[str]]:
    """Return ``(members, exclude)``.

    Uses ``tomllib`` when the interpreter has it. Falls back to a deliberately tiny regex reader
    for the two string-array fields this check needs, so the gate still runs on a pre-3.11 system
    ``python3``. The fallback is NOT a TOML parser and must never grow into one — if this check
    ever needs a third field, give it a real parser or accept the 3.11 floor explicitly.
    """
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError as exc:
        raise WorkspaceCheckError(f"cannot read {pyproject}: {exc}") from exc

    if _HAVE_TOMLLIB:
        try:
            data = tomllib.loads(text)
        except tomllib.TOMLDecodeError as exc:
            raise WorkspaceCheckError(f"cannot parse {pyproject}: {exc}") from exc
        workspace = data.get("tool", {}).get("uv", {}).get("workspace", {})
        return workspace.get("members", []), workspace.get("exclude", [])

    table = _WORKSPACE_TABLE.search(text)
    if not table:
        return [], []
    rest = text[table.end() :]
    following = _NEXT_TABLE.search(rest)
    body = rest[: following.start()] if following else rest
    return _array_field(body, "members"), _array_field(body, "exclude")


def unresolvable_members(repo_root: Path) -> list[str]:
    """Return repo-relative dirs matched by a workspace glob that uv could not resolve.

    Reported when a directory is matched by a ``members`` glob, is not in ``exclude``, contains at
    least one ``.py`` file (so it is genuinely a Python member and not a data or shell-only dir),
    and has no ``pyproject.toml``.
    """
    members, exclude = _read_workspace(repo_root / "pyproject.toml")
    excluded = {e.rstrip("/") for e in exclude}

    broken: list[str] = []
    for pattern in members:
        for candidate in sorted(repo_root.glob(pattern)):
            if not candidate.is_dir():
                continue
            rel = candidate.relative_to(repo_root).as_posix()
            if rel in excluded or not any(candidate.rglob("*.py")):
                continue
            if not (candidate / "pyproject.toml").is_file():
                broken.append(rel)
    return sorted(broken)


def stale_excludes(repo_root: Path) -> list[str]:
    """Return ``exclude`` entries that name directories which no longer exist."""
    _, exclude = _read_workspace(repo_root / "pyproject.toml")
    return [e for e in exclude if not (repo_root / e).is_dir()]


def main(argv: list[str] | None = None) -> int:
    root = Path(argv[0]).resolve() if argv else REPO_ROOT
    try:
        broken = unresolvable_members(root)
        stale = stale_excludes(root)
    except WorkspaceCheckError as exc:
        print(f"workspace-check: {exc}", file=sys.stderr)
        return 2

    for entry in stale:
        print(f"workspace-check: WARNING stale [tool.uv.workspace] exclude: {entry!r}")

    if not broken:
        print("workspace-check: OK — every globbed Python member has a pyproject.toml.")
        return 0

    for entry in broken:
        print(f"workspace-check: BROKEN MEMBER {entry} — no pyproject.toml", file=sys.stderr)
    print(
        "\nEvery `uv` call in this repo now fails, including `uv run pytest` and every PreToolUse\n"
        "guard hook — which means file-write and shell tools are denied too, and the repair is\n"
        "locked behind the thing it repairs. Create the pyproject.toml from outside the agent\n"
        "tool surface, or add the directory to [tool.uv.workspace] exclude.\n"
        "Rule: create tools/<name>/pyproject.toml in the SAME step that creates tools/<name>/.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":  # pragma: no cover - exercised as a subprocess
    raise SystemExit(main(sys.argv[1:]))
