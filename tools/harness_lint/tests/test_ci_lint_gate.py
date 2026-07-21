"""DEBT-01 gate proof — structural assertions for the ``lint`` CI job in ``.github/workflows/ci.yml``.

DEBT-01 exists because `ruff check` has never been able to fail anything: the repo carried 617
findings and zero CI jobs that looked at them. A `lint` job that exists but is missing from the
fan-in ``gate.needs`` would reproduce that defect exactly — visibly present, unable to block a
merge — so fan-in membership is asserted here rather than read once and trusted.

The workflow is PARSED (``ruamel.yaml``, the resolved parser in this workspace — no pyyaml), never
grepped: the bare string ``lint`` occurs in comments, in ``polyglot_lint``, and in
``lifecycle-eval``'s prose, so a substring match would report success against nothing.

The general invariant at the bottom (every job except ``gate`` is a member of ``gate.needs``) is
the part that keeps working after this phase: it fails for the NEXT job someone forgets to wire in.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml import YAML

# test_ci_lint_gate.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict:
    yaml = YAML(typ="safe")
    with _CI_WORKFLOW.open(encoding="utf-8") as fh:
        return yaml.load(fh)


def _run_texts(job: dict) -> list[str]:
    """Every ``run:`` shell body in a job's steps (as strings)."""
    return [str(step.get("run", "")) for step in job.get("steps", [])]


def test_lint_job_exists() -> None:
    ci = _load_ci()
    assert "lint" in ci["jobs"], "ci.yml must define a `lint` job (DEBT-01)"


def test_lint_job_runs_the_ratchet() -> None:
    ci = _load_ci()
    joined = "\n".join(_run_texts(ci["jobs"]["lint"]))
    assert "tools.ruff_baseline" in joined, (
        "the lint job must gate on the ratchet CLI (`python -m tools.ruff_baseline`)"
    )


def test_lint_job_does_not_run_a_bare_repo_wide_ruff_check() -> None:
    """A bare `ruff check .` is red today (393 held findings) and would make the job PERMANENTLY
    red — the same non-gate as having no job at all. It becomes a step when the baseline reaches
    zero, and not before (34-CONTEXT D-10)."""
    ci = _load_ci()
    for run in _run_texts(ci["jobs"]["lint"]):
        normalized = " ".join(run.split())
        assert "ruff check ." not in normalized, (
            "the lint job must not run a bare repo-wide `ruff check .` while the baseline is "
            "non-zero — gate on `python -m tools.ruff_baseline` instead"
        )


def test_lint_job_is_in_the_fan_in() -> None:
    """A job absent from `gate.needs` cannot block a merge, however green or red it goes."""
    ci = _load_ci()
    assert "lint" in ci["jobs"]["gate"]["needs"], (
        "`lint` must be a member of gate.needs or it cannot block a merge"
    )


def test_every_job_is_in_the_fan_in() -> None:
    """The general invariant — catches the NEXT job someone forgets to wire in, not just this one."""
    ci = _load_ci()
    declared = set(ci["jobs"]) - {"gate"}
    fan_in = set(ci["jobs"]["gate"]["needs"])
    assert declared <= fan_in, (
        f"these jobs are not in gate.needs and therefore cannot block a merge: "
        f"{sorted(declared - fan_in)}"
    )


def test_lint_job_keeps_the_repo_security_posture() -> None:
    """Pinned actions, and no attacker-controllable event data interpolated into a run shell."""
    ci = _load_ci()
    job = ci["jobs"]["lint"]
    for step in job.get("steps", []):
        uses = step.get("uses")
        if uses is not None:
            assert "@" in uses, f"action `{uses}` must be version-pinned"
            ref = uses.split("@", 1)[1]
            assert ref not in ("main", "master"), f"action `{uses}` must not track a branch"
    for run in _run_texts(job):
        assert "github.event" not in run, (
            "the lint job must never interpolate `${{ github.event.* }}` into a run shell"
        )
