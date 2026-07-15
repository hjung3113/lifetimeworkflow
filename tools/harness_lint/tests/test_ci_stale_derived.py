"""MAINT-02 gate proof (D-07/D-08) — structural + negative-control assertions for the
``stale-derived`` CI job in ``.github/workflows/ci.yml``.

Two independent proofs, no network:

1. **Structural** — parse the workflow with ``ruamel.yaml`` (``YAML(typ="safe")``; the same
   parser the rest of this suite uses, NO pyyaml) and assert the ``stale-derived`` job exists,
   uses the untracked-safe diff primitive (``git add -A`` + ``git diff --cached --exit-code``,
   NOT bare ``git diff`` — Pitfall P1) over the committed-derived paths, is a member of the
   fan-in ``gate.needs`` (non-bypassable, T-9-02), and never interpolates
   ``${{ github.event.* }}`` into a ``run:`` shell (T-9-02-EoP).

2. **Negative-control** — exercise the gate's core diff primitive against real ``git`` plumbing
   in a throwaway ``tmp_path`` repo (``subprocess`` with ``shell=False``): a mutated staged file
   makes ``git diff --cached --exit-code`` return non-zero, a clean staged tree returns zero.
   This documents locally that the gate discriminates stale vs. clean — the exact assertion the
   CI job relies on.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from ruamel.yaml import YAML

# test_ci_stale_derived.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

# The two committed-derived artifacts the stale-derived gate regenerates and diffs.
_DERIVED_PATHS = ("docs/reference", ".memory/derived/contracts-index.md")


def _load_ci() -> dict:
    yaml = YAML(typ="safe")
    with _CI_WORKFLOW.open(encoding="utf-8") as fh:
        return yaml.load(fh)


def _run_texts(job: dict) -> list[str]:
    """Every ``run:`` shell body in a job's steps (as strings)."""
    return [str(step.get("run", "")) for step in job.get("steps", [])]


# ── Structural: the gate is present, correctly shaped, and non-bypassable ─────────────────────


def test_stale_derived_job_exists() -> None:
    ci = _load_ci()
    assert "stale-derived" in ci["jobs"], "ci.yml must define a `stale-derived` job (MAINT-02)"


def test_stale_derived_uses_untracked_safe_diff_primitive() -> None:
    """The gate MUST stage first (`git add -A`) then diff `--cached --exit-code` — bare
    `git diff` misses NEW untracked pages (Pitfall P1)."""
    ci = _load_ci()
    runs = _run_texts(ci["jobs"]["stale-derived"])
    joined = "\n".join(runs)

    assert "git add -A" in joined, "stale-derived must `git add -A` (stage untracked pages, P1)"
    assert "git diff --cached --exit-code" in joined, (
        "stale-derived must use `git diff --cached --exit-code`, NOT bare `git diff` (P1)"
    )
    # Bare `git diff --exit-code` (no --cached) is the P1 bug — assert it is NOT the primitive.
    assert "git diff --exit-code" not in joined, (
        "stale-derived must not use bare `git diff --exit-code` (untracked pages slip through, P1)"
    )
    # The diff must cover BOTH committed-derived paths.
    for path in _DERIVED_PATHS:
        assert path in joined, f"stale-derived diff must cover the committed-derived path `{path}`"


def test_stale_derived_regenerates_both_derived_generators() -> None:
    """The gate regenerates via the canonical tools.* modules (no inline derivation, D-06)."""
    ci = _load_ci()
    joined = "\n".join(_run_texts(ci["jobs"]["stale-derived"]))
    assert "tools.docs_sync" in joined, (
        "stale-derived must regen docs/reference via tools.docs_sync"
    )
    assert "tools.memory_regen.contracts_index" in joined, (
        "stale-derived must regen contracts-index via tools.memory_regen.contracts_index"
    )


def test_stale_derived_prints_actionable_fix() -> None:
    """On failure the job self-documents the fix (D-08): /refresh-memory or the literal regen."""
    ci = _load_ci()
    joined = "\n".join(_run_texts(ci["jobs"]["stale-derived"]))
    assert "/refresh-memory" in joined or (
        "tools.docs_sync" in joined and "tools.memory_regen.contracts_index" in joined
    ), "stale-derived must echo a copy-pasteable fix (/refresh-memory or the literal regen)"


def test_stale_derived_is_in_gate_needs() -> None:
    """Non-bypassable: the fan-in `gate` job must depend on `stale-derived` (T-9-02)."""
    ci = _load_ci()
    assert "stale-derived" in ci["jobs"]["gate"]["needs"], (
        "stale-derived must be a member of gate.needs (non-bypassable fan-in)"
    )


def test_stale_derived_never_interpolates_event_input() -> None:
    """T-9-02-EoP: no attacker-controllable `${{ github.event.* }}` in any run shell."""
    ci = _load_ci()
    for run in _run_texts(ci["jobs"]["stale-derived"]):
        assert "github.event." not in run, (
            "stale-derived run steps must never interpolate github.event.* (injection surface)"
        )


# ── Negative-control: the diff primitive discriminates stale vs. clean (git plumbing) ─────────


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )


def test_cached_diff_discriminates_stale_vs_clean(tmp_path: Path) -> None:
    """Prove the gate's primitive: `git diff --cached --exit-code` returns 0 on a clean staged
    tree and non-zero once a staged file is mutated (and re-staged). No network."""
    repo = tmp_path / "repo"
    repo.mkdir()

    assert _git(repo, "init").returncode == 0
    # Local identity so `git commit` works in an isolated env.
    _git(repo, "config", "user.email", "gate@example.invalid")
    _git(repo, "config", "user.name", "gate")

    derived = repo / "derived.md"
    derived.write_text("regenerated line\n", encoding="utf-8")
    assert _git(repo, "add", "-A").returncode == 0
    assert _git(repo, "commit", "-m", "seed").returncode == 0

    # Clean staged tree (nothing new to stage) → --cached --exit-code returns 0.
    _git(repo, "add", "-A")
    clean = _git(repo, "diff", "--cached", "--exit-code")
    assert clean.returncode == 0, "clean staged tree must pass `git diff --cached --exit-code`"

    # Mutate the tracked file (simulating a stale, hand-edited derived artifact), re-stage.
    derived.write_text("HAND-EDITED stale line\n", encoding="utf-8")
    _git(repo, "add", "-A")
    stale = _git(repo, "diff", "--cached", "--exit-code")
    assert stale.returncode != 0, "a mutated staged file must FAIL `git diff --cached --exit-code`"


def test_cached_diff_catches_new_untracked_file(tmp_path: Path) -> None:
    """The P1 crux: a brand-NEW file (never tracked) is invisible to bare `git diff` but caught
    once `git add -A` stages it and `git diff --cached --exit-code` runs — proving why the gate
    stages first."""
    repo = tmp_path / "repo"
    repo.mkdir()

    assert _git(repo, "init").returncode == 0
    _git(repo, "config", "user.email", "gate@example.invalid")
    _git(repo, "config", "user.name", "gate")

    (repo / "existing.md").write_text("x\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "seed")

    # A newly-created (untracked) page, exactly like a freshly-generated reference page.
    (repo / "new-page.md").write_text("brand new derived page\n", encoding="utf-8")

    # Bare `git diff --exit-code` (no --cached/staging) MISSES the untracked file (the bug).
    bare = _git(repo, "diff", "--exit-code")
    assert bare.returncode == 0, (
        "bare `git diff` cannot see an untracked file (documents the P1 gap)"
    )

    # The gate's primitive: stage first, then diff --cached → non-zero (caught).
    _git(repo, "add", "-A")
    caught = _git(repo, "diff", "--cached", "--exit-code")
    assert caught.returncode != 0, (
        "`git add -A` + `git diff --cached --exit-code` MUST catch a new untracked page (P1)"
    )
