"""POLY-01 in-session call-site proof: /lint invokes the polyglot §4.3-4.6 linter (no regression).

Success criterion 2 requires the ONE POLY-01 engine (``tools.polyglot_lint.lint``) to have three
call sites — on-write (contract-guard/format-on-write, wired 04-03/04-04), in-session (/lint), and
CI (deferred to Phase 5). This test locks the IN-SESSION site: ``harness/commands/lint.md`` must
reference ``tools.polyglot_lint.lint`` AND still carry the pre-existing ``ruff check`` +
dotnet-gated block (a thin-macro append must not regress the existing linters).

Pure text assertion on the committed command markdown — no harness import, no subprocess.
"""

from __future__ import annotations

from pathlib import Path

# test file -> tests -> hooks -> tools -> repo root (parents[3]); mirrors conftest wiring.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LINT_MD = _REPO_ROOT / "harness" / "commands" / "lint.md"


def _text() -> str:
    return _LINT_MD.read_text(encoding="utf-8")


def test_lint_command_wires_polyglot_engine() -> None:
    """/lint calls the single POLY-01 §4.3-4.6 rule engine (the in-session call site exists)."""
    text = _text()
    assert "tools.polyglot_lint.lint" in text, (
        "harness/commands/lint.md must invoke `tools.polyglot_lint.lint` (POLY-01 in-session site)"
    )


def test_lint_command_still_runs_ruff_check() -> None:
    """No regression: the pre-existing `ruff check` python-lint step survives the append."""
    assert "ruff check" in _text(), "the polyglot append must not drop the existing `ruff check`"


def test_lint_command_still_dotnet_gated() -> None:
    """No regression: the presence-gated dotnet format block survives the append."""
    text = _text()
    assert "dotnet" in text and "format" in text, (
        "the polyglot append must not drop the dotnet-gated format check"
    )


def test_lint_command_loops_tracked_tsv_files() -> None:
    """The macro loops over tracked boundary files so the check is presence-safe (zero -> no-op)."""
    text = _text()
    assert "git ls-files" in text and ".tsv" in text, (
        "/lint must iterate tracked *.tsv boundary files (presence-safe, no error when zero exist)"
    )
