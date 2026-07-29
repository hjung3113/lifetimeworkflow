"""DEBT-01 — the ratcheting ruff baseline.

`ruff check` reports real debt in this repo, but a lint that cannot fail CI is not a gate, and a
gate that fires on 400 pre-existing findings is one nobody can act on. This module holds the
middle ground: the committed per-rule counts in ``baseline.json`` are a ceiling that may only
ever fall.

Three design points that are load-bearing, not incidental:

**Keyed per rule, not per (file, rule).** Per-file keying is stricter but reads every file rename
as an increase, which forces an ``--update`` that can raise counts — the escape hatch that makes a
ratchet decorative. Per-rule keying is rename-proof, which in turn lets ``write_baseline`` be
structurally incapable of raising a count. The residual gap is recorded rather than hidden:
deleting one E501 in file A while adding one in file B is a wash this gate permits.

**A code absent from the baseline is baseline 0.** A ruff bump that adds a check under E/F/I/UP/B,
or a genuinely new violation class, fails on first appearance instead of being absorbed.

**Ruff's exit 2 raises.** Exit 0 is clean and exit 1 is findings; anything else is a broken
invocation, and reporting it as "zero findings" would leave the gate permanently green.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = Path(__file__).resolve().parent / "baseline.json"

#: Ruff emits ``code: null`` for syntax errors. They are bucketed under an explicit key rather
#: than dropped, so an unparseable file cannot slip past the gate as "no findings".
SYNTAX_ERROR_CODE = "<syntax-error>"

_BASELINE_COMMENT = (
    "Ratcheting ruff baseline (DEBT-01). Per-rule finding counts that may only SHRINK. "
    "Regenerate after fixing findings with `uv run python -m tools.ruff_baseline --update`, "
    "which refuses to raise any count. Enforced by the `lint` CI job."
)


class RuffInvocationError(RuntimeError):
    """Ruff could not be run, or did not return parseable JSON."""


class BaselineError(ValueError):
    """The baseline document is missing or malformed."""


class BaselineRaiseRefused(BaselineError):
    """An update would have raised a count. The baseline may only shrink."""


@dataclass(frozen=True)
class RatchetResult:
    """The comparison of a live run against the committed baseline."""

    regressions: dict[str, tuple[int, int]] = field(default_factory=dict)
    improvements: dict[str, tuple[int, int]] = field(default_factory=dict)
    baseline_total: int = 0
    current_total: int = 0

    @property
    def ok(self) -> bool:
        return not self.regressions


def ruff_command() -> list[str]:
    """The exact argv the gate runs.

    ``sys.executable -m ruff`` rather than a bare ``ruff``: the wheel ships ``ruff/__main__.py``,
    so this resolves through the interpreter the workspace already selected and cannot pick up a
    different ruff from the ambient environment.

    ``--no-cache`` is deliberate. CI runners are always cold and local runs are usually warm; the
    gate must not have a verdict that depends on which of the two you are standing in. A full cold
    run over this repo costs about a second. Do not "optimise" it away.
    """
    return [
        sys.executable,
        "-m",
        "ruff",
        "check",
        ".",
        "--no-cache",
        "--output-format=json",
    ]


def run_ruff(cwd: Path = REPO_ROOT) -> list[dict[str, Any]]:
    """Run ruff over the repo and return its diagnostics."""
    completed = subprocess.run(  # fixed argv, shell=False, no caller-supplied input
        ruff_command(),
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode not in (0, 1):
        raise RuffInvocationError(
            f"ruff exited {completed.returncode} (expected 0=clean or 1=findings): "
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )
    try:
        diagnostics = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError as exc:
        raise RuffInvocationError(f"ruff did not emit parseable JSON: {exc}") from exc
    if not isinstance(diagnostics, list):
        raise RuffInvocationError("ruff JSON output was not a list of diagnostics")
    return diagnostics


def counts_from_diagnostics(diagnostics: list[dict[str, Any]]) -> dict[str, int]:
    """Bucket ruff diagnostics by rule code."""
    counts: dict[str, int] = {}
    for diagnostic in diagnostics:
        code = diagnostic.get("code") or SYNTAX_ERROR_CODE
        counts[code] = counts.get(code, 0) + 1
    return counts


def compare_counts(baseline: dict[str, int], current: dict[str, int]) -> RatchetResult:
    """Compare live counts against the baseline. Pure — no ruff, no filesystem."""
    regressions: dict[str, tuple[int, int]] = {}
    improvements: dict[str, tuple[int, int]] = {}
    for code in sorted(set(baseline) | set(current)):
        allowed = baseline.get(code, 0)
        found = current.get(code, 0)
        if found > allowed:
            regressions[code] = (allowed, found)
        elif found < allowed:
            improvements[code] = (allowed, found)
    return RatchetResult(
        regressions=regressions,
        improvements=improvements,
        baseline_total=sum(baseline.values()),
        current_total=sum(current.values()),
    )


def render(result: RatchetResult) -> str:
    """Human-readable verdict. A failure an operator cannot act on is one they will disable."""
    lines = [f"ruff ratchet: {result.current_total} findings (baseline {result.baseline_total})"]
    for code, (allowed, found) in result.regressions.items():
        lines.append(f"  REGRESSION  {code}: baseline {allowed} -> found {found}")
    for code, (allowed, found) in result.improvements.items():
        lines.append(f"  improved    {code}: baseline {allowed} -> found {found}")
    if result.regressions:
        lines += [
            "",
            "FAIL: a ruff rule class grew. The baseline may only SHRINK.",
            "Fix the new finding(s) above. Do NOT raise the baseline — "
            "`--update` refuses to, and hand-raising the committed file is visible in review.",
        ]
    elif result.improvements:
        lines += [
            "",
            "PASS — and findings went DOWN. Record the shrink so it cannot come back:",
            "    uv run python -m tools.ruff_baseline --update",
        ]
    else:
        lines.append("PASS: every rule class is at its baseline.")
    return "\n".join(lines)


def load_baseline(path: Path = BASELINE_PATH) -> dict[str, int]:
    """Read the committed per-rule counts."""
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise BaselineError(f"baseline not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise BaselineError(f"baseline is not valid JSON: {path}: {exc}") from exc
    counts = document.get("counts") if isinstance(document, dict) else None
    if not isinstance(counts, dict):
        raise BaselineError(f"baseline is missing a 'counts' mapping: {path}")
    for code, value in counts.items():
        if not isinstance(code, str) or not isinstance(value, int) or isinstance(value, bool):
            raise BaselineError(f"baseline has a non-integer count for {code!r}: {path}")
    return dict(counts)


def baseline_ruff_version(path: Path = BASELINE_PATH) -> str | None:
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    version = document.get("ruff_version") if isinstance(document, dict) else None
    return version if isinstance(version, str) else None


def write_baseline(path: Path, counts: dict[str, int], ruff_version: str) -> None:
    """Record `counts`, refusing any update that would RAISE a count.

    This is what makes "can only shrink" an executable claim rather than a norm: there is no
    ordinary path by which the committed baseline grows. Growing it requires hand-editing a
    committed JSON file, which is visible in review.
    """
    if path.exists():
        previous = load_baseline(path)
        raised = {
            code: (previous.get(code, 0), found)
            for code, found in counts.items()
            if found > previous.get(code, 0)
        }
        if raised:
            detail = ", ".join(f"{c}: {was} -> {now}" for c, (was, now) in sorted(raised.items()))
            raise BaselineRaiseRefused(
                f"refusing to raise the ruff baseline ({detail}). "
                "The baseline may only shrink — fix the new findings instead."
            )
    document = {
        "_comment": _BASELINE_COMMENT,
        "ruff_version": ruff_version,
        "total": sum(counts.values()),
        "counts": dict(sorted(counts.items())),
    }
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def installed_ruff_version() -> str:
    completed = subprocess.run(  # fixed argv, shell=False, no caller-supplied input
        [sys.executable, "-m", "ruff", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuffInvocationError(f"could not read ruff's version: {completed.stderr.strip()}")
    return completed.stdout.strip().removeprefix("ruff ").strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m tools.ruff_baseline",
        description="Ratcheting ruff baseline: fail when any rule class grows.",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="rewrite the baseline from the current tree; refuses to raise any count",
    )
    parser.add_argument("--json", action="store_true", help="emit the comparison as JSON")
    args = parser.parse_args(argv)

    try:
        current = counts_from_diagnostics(run_ruff())
        version = installed_ruff_version()
    except RuffInvocationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.update:
        try:
            write_baseline(BASELINE_PATH, current, version)
        except BaselineRaiseRefused as exc:
            print(f"REFUSED: {exc}", file=sys.stderr)
            return 3
        except BaselineError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
        print(f"baseline updated: {sum(current.values())} findings across {len(current)} rules")
        return 0

    try:
        baseline = load_baseline()
    except BaselineError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    recorded = baseline_ruff_version()
    if recorded and recorded != version:
        # A version bump must be DIAGNOSABLE from the output rather than indistinguishable from a
        # code regression — but it is not itself a failure.
        print(f"note: baseline was generated under ruff {recorded}; running ruff {version}")

    result = compare_counts(baseline, current)
    if args.json:
        print(
            json.dumps(
                {
                    "ok": result.ok,
                    "regressions": {k: list(v) for k, v in result.regressions.items()},
                    "improvements": {k: list(v) for k, v in result.improvements.items()},
                    "baseline_total": result.baseline_total,
                    "current_total": result.current_total,
                },
                indent=2,
            )
        )
    else:
        print(render(result))
    return 0 if result.ok else 1
