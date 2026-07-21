"""Every directory the uv workspace GLOBS must be resolvable, or the whole repo loses its tools.

This guard exists because the failure it prevents is not merely annoying — it is
**self-sealing**, and it took a live session down during v2.4 phase 34.

``pyproject.toml`` declares ``members = ["libs/python", "tools/*"]``. uv requires every directory
matched by that glob to contain a ``pyproject.toml``. The moment ``tools/<name>/`` exists without
one, EVERY ``uv`` invocation in the repo fails at workspace resolution — not just the new one::

    error: Workspace member `.../tools/<name>` is missing a `pyproject.toml` (matches: `tools/*`)

That alone would be ordinary. What makes it worth a gate is the second-order effect. This repo's
PreToolUse guards (``contract_guard``, ``secret_scan``, ``ledger_guard``, ``commit_gate``,
``resume_gate``) are all invoked as ``uv run python -m tools.hooks.<name>``. When workspace
resolution fails, every one of those hooks fails, and a failing PreToolUse hook **denies its tool**.
The guards failing closed is CORRECT — a guard that cannot run must not wave writes through — but
the consequence is that file-write AND shell tools all stop working at once, including the ones that
would create the missing file. The repair is locked behind the thing it repairs, and recovery
requires a process outside the agent's tool surface.

So the ordering rule is not a style preference, it is an availability constraint:

    Create ``tools/<name>/pyproject.toml`` in the SAME step that creates ``tools/<name>/``.

Two escape hatches are legitimate and both are honoured here: a directory may be listed in
``[tool.uv.workspace] exclude`` (``tools/bootstrap`` is, being shell-only), and a directory with no
Python content at all is not a package. Everything else must carry a ``pyproject.toml``.

THIS FILE IS NOT THE GATE, AND CANNOT BE
----------------------------------------
``uv run pytest`` is itself a ``uv`` invocation, so when a globbed member is missing its
``pyproject.toml`` uv dies before pytest starts and these tests never execute. Verified by mutation:
planting ``tools/_probe_pkg/mod.py`` with no pyproject produced the raw uv resolution error instead
of a test failure. A pytest guard for this condition would be a claimed control that does not exist.

The real gate is ``tools/harness_lint/workspace_check.py``, which runs on bare ``python3`` with no
uv, no venv and no repo imports, and is wired into CI ahead of every uv step. These tests exist to
prove THAT module's logic is right — including the negative control that fabricates the broken shape
in a tmp tree — not to catch the live condition.

Mirrors the structural-scan idiom of ``test_core_no_example_dep.py``: enumeration-driven, no runtime
import of the packages under scan.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint.workspace_check import (
    main as workspace_check_main,
)
from tools.harness_lint.workspace_check import (
    stale_excludes,
    unresolvable_members,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
ROOT_PYPROJECT = REPO_ROOT / "pyproject.toml"

_unresolvable_members = unresolvable_members


def test_every_globbed_workspace_member_has_a_pyproject() -> None:
    """The live repo resolves: no globbed, non-excluded Python dir lacks a pyproject.toml.

    When this fails, do NOT reach for the tool that reports it — by the time you see this, every
    ``uv``-backed hook in the session is probably already denying writes. Create the missing
    ``pyproject.toml`` from outside the agent tool surface, then re-run.
    """
    broken = _unresolvable_members(REPO_ROOT)
    assert broken == [], (
        "these directories are matched by a [tool.uv.workspace] members glob, contain Python, and "
        f"have no pyproject.toml, so EVERY `uv` call in this repo fails: {broken}. "
        "Add a pyproject.toml to each, or list it under [tool.uv.workspace] exclude. "
        "Because the PreToolUse guards shell out to `uv run`, this state also denies every "
        "file-write and shell tool — the repair is locked behind the thing it repairs."
    )


def test_declared_excludes_are_real_directories() -> None:
    """An ``exclude`` entry that no longer exists is dead config hiding a future surprise."""
    missing = stale_excludes(REPO_ROOT)
    assert missing == [], (
        f"[tool.uv.workspace] exclude names directories that do not exist: {missing}. "
        "Remove them; a stale exclude silently stops protecting anything."
    )


def test_checker_detects_a_fabricated_broken_member(tmp_path: Path) -> None:
    """NEGATIVE CONTROL — the scan is live.

    Builds a miniature repo with the same workspace shape, plants exactly the broken member, and
    asserts the checker names it. Without this, ``test_every_globbed_...`` would keep passing if
    the glob logic silently stopped matching anything.
    """
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["tools/*"]\nexclude = ["tools/shellonly"]\n',
        encoding="utf-8",
    )

    good = tmp_path / "tools" / "good"
    good.mkdir(parents=True)
    (good / "pyproject.toml").write_text("[project]\nname='good'\n", encoding="utf-8")
    (good / "mod.py").write_text("x = 1\n", encoding="utf-8")

    broken = tmp_path / "tools" / "broken"
    broken.mkdir(parents=True)
    (broken / "mod.py").write_text("x = 1\n", encoding="utf-8")

    excluded = tmp_path / "tools" / "shellonly"
    excluded.mkdir(parents=True)
    (excluded / "helper.py").write_text("x = 1\n", encoding="utf-8")

    data_only = tmp_path / "tools" / "fixtures"
    data_only.mkdir(parents=True)
    (data_only / "sample.json").write_text("{}\n", encoding="utf-8")

    found = _unresolvable_members(tmp_path)

    assert found == ["tools/broken"], (
        f"expected exactly the pyproject-less Python member, got {found}. "
        "'tools/good' has one; 'tools/shellonly' is excluded; 'tools/fixtures' carries no Python."
    )


def test_checker_exits_nonzero_on_a_broken_tree(tmp_path: Path) -> None:
    """The CI entry point's exit code is the contract — 1 on a broken member, 0 when clean."""
    (tmp_path / "pyproject.toml").write_text(
        '[tool.uv.workspace]\nmembers = ["tools/*"]\n', encoding="utf-8"
    )
    broken = tmp_path / "tools" / "broken"
    broken.mkdir(parents=True)
    (broken / "mod.py").write_text("x = 1\n", encoding="utf-8")

    assert workspace_check_main([str(tmp_path)]) == 1

    (broken / "pyproject.toml").write_text("[project]\nname='b'\n", encoding="utf-8")
    assert workspace_check_main([str(tmp_path)]) == 0
