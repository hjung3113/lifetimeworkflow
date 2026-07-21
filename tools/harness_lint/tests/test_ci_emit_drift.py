"""EMIT-02 gate proof (15-REVIEW CR-01) — structural assertions for the ``emit-drift`` CI job
in ``.github/workflows/ci.yml``.

The sibling module ``test_ci_stale_derived.py`` pins the SAME untracked-safe diff primitive for
the ``stale-derived`` job and already carries the git-plumbing negative control that proves the
primitive discriminates (bare ``git diff`` blind to a new file; ``git add -A`` +
``git diff --cached --exit-code`` catches it). That control is not duplicated here — it is
primitive-level, not job-level, and one copy is the honest number.

What IS specific to ``emit-drift``, and what this module pins:

``emit-drift`` re-runs the emitter and fails on any divergence between the runtime-neutral
``harness/`` source and the committed ``.opencode/`` + ``.claude/`` trees. Until CR-01 it used
bare ``git diff --exit-code``, which sees tracked-file changes ONLY. A re-emit that produces a
BRAND-NEW artifact — a newly added agent, command or skill — leaves that file untracked, and the
gate passed green on a drifted tree. Plan 29-03 hit this live: bare ``git diff`` reported clean
while four newly emitted files sat untracked. The whole point of this job is that the emitted
surface is machine-written and a NEW file is the most ordinary thing an emitter produces, so the
untracked case is the common case, not the corner one.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

# test_ci_emit_drift.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"

# Every path the emit-drift gate must cover — the full documented emitted surface.
_EMITTED_PATHS = (
    ".opencode",
    "opencode.json",
    ".claude/agents",
    ".claude/commands",
    ".claude/skills",
    "AGENTS.md",
    "CLAUDE.md",
    ".claude/settings.json",
)


def _load_ci() -> dict:
    yaml = YAML(typ="safe")
    with _CI_WORKFLOW.open(encoding="utf-8") as fh:
        return yaml.load(fh)


def _run_texts(job: dict) -> list[str]:
    """Every ``run:`` shell body in a job's steps (as strings)."""
    return [str(step.get("run", "")) for step in job.get("steps", [])]


def test_emit_drift_job_exists() -> None:
    ci = _load_ci()
    assert "emit-drift" in ci["jobs"], "ci.yml must define an `emit-drift` job (EMIT-02)"


def test_emit_drift_uses_untracked_safe_diff_primitive() -> None:
    """CR-01: the gate MUST stage first (`git add -A`) then diff `--cached --exit-code`.

    Bare `git diff` is blind to a NEWLY emitted artifact, which is precisely what an emitter
    produces when an agent/command/skill is added — 29-03 hit this with four untracked files
    while the gate read clean.
    """
    ci = _load_ci()
    joined = "\n".join(_run_texts(ci["jobs"]["emit-drift"]))

    assert "git add -A" in joined, "emit-drift must `git add -A` (stage newly emitted artifacts)"
    assert "git diff --cached --exit-code" in joined, (
        "emit-drift must use `git diff --cached --exit-code`, NOT bare `git diff` (CR-01)"
    )
    # Bare `git diff --exit-code` (no --cached) is the CR-01 bug — assert it is NOT the primitive.
    assert "git diff --exit-code" not in joined, (
        "emit-drift must not use bare `git diff --exit-code` "
        "(a newly emitted artifact stays untracked and slips through, CR-01)"
    )


def test_emit_drift_covers_the_full_emitted_surface() -> None:
    """Every documented emitted path stays in the diff set — a path dropped here is a tree that
    can drift silently."""
    ci = _load_ci()
    joined = "\n".join(_run_texts(ci["jobs"]["emit-drift"]))
    for path in _EMITTED_PATHS:
        assert path in joined, f"emit-drift diff must cover the emitted path `{path}`"


def test_emit_drift_reemits_via_the_canonical_module() -> None:
    """The gate re-emits through `tools.harness_emit`, never an inline reimplementation."""
    ci = _load_ci()
    joined = "\n".join(_run_texts(ci["jobs"]["emit-drift"]))
    assert "tools.harness_emit" in joined, (
        "emit-drift must re-emit via `python -m tools.harness_emit`"
    )


def test_emit_drift_prints_actionable_fix() -> None:
    """On failure the job self-documents the fix: edit `harness/`, then re-emit."""
    ci = _load_ci()
    joined = "\n".join(_run_texts(ci["jobs"]["emit-drift"]))
    assert "harness/" in joined, (
        "emit-drift must echo that the fix is editing the runtime-neutral source under harness/"
    )


def test_emit_drift_is_in_gate_needs() -> None:
    """Non-bypassable: the fan-in `gate` job must depend on `emit-drift`."""
    ci = _load_ci()
    assert "emit-drift" in ci["jobs"]["gate"]["needs"], (
        "emit-drift must be a member of gate.needs (non-bypassable fan-in)"
    )


def test_emit_drift_never_interpolates_event_input() -> None:
    """No attacker-controllable `${{ github.event.* }}` in any run shell."""
    ci = _load_ci()
    for run in _run_texts(ci["jobs"]["emit-drift"]):
        assert "github.event." not in run, (
            "emit-drift run steps must never interpolate github.event.* (injection surface)"
        )
