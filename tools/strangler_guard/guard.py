"""``/strangler-step`` baseline-refusal gate (CMD-06, D-05, Pitfall P10).

Before a legacy path is strangler-extracted, a *trusted equivalence reference* must already exist:
a captured legacy golden ``.verified`` baseline for that path. This module asserts that precondition
and REFUSES outright — ``require_baseline`` raises :class:`StranglerRefused`, and :func:`main` maps
that to a non-zero exit code (3) — exactly mirroring
``tools.golden_runner.approve.GoldenApprovalRefused`` (CLI exit 3). "Machines gate, humans ratify":
the golden/human plane provides the baseline; this gate only checks and refuses. It NEVER fabricates
or creates a baseline (that would defeat the whole point — a migration with no equivalence reference
silently regresses, T-03-24 / P10).

Single-path-only extraction and the mandatory ``/golden`` parity gate are enforced by the command
macro (``harness/commands/strangler-step.md``); this runnable module is the load-bearing refusal.
"""

from __future__ import annotations

import re
from pathlib import Path

# guard.py -> strangler_guard -> tools -> repo root (parents[2]; mirrors golden_runner/runner.py).
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GOLDEN_DIR = REPO_ROOT / "golden"

# The captured-baseline filename the golden plane writes (golden_runner.verified_path).
_VERIFIED_NAME = "baseline.verified.tsv"


class StranglerRefused(Exception):
    """Strangler extraction refused — no captured legacy golden baseline exists for the target path.

    The migration equivalent of :class:`tools.golden_runner.approve.GoldenApprovalRefused`: a machine
    gate an agent must not route around by inventing a baseline.
    """


def _slug(target_path: str) -> str:
    """Derive a deterministic golden case slug from a legacy target path.

    ``src/legacy/Parser.cs`` -> ``src-legacy-parser-cs``. Purely structural (lowercase, non-alnum
    runs collapse to a single hyphen) so the derived location is reproducible by the golden plane and
    by the test that seeds a baseline.
    """
    return re.sub(r"[^a-z0-9]+", "-", target_path.lower()).strip("-")


def baseline_path(target_path: str, golden_dir: str | Path = DEFAULT_GOLDEN_DIR) -> Path:
    """The deterministic location of the captured ``.verified`` baseline for ``target_path``.

    ``<golden_dir>/<slug(target_path)>/expected/baseline.verified.tsv``. This does NOT assert the
    file exists — it only computes where a captured legacy baseline for the path would live.
    """
    return Path(golden_dir) / _slug(target_path) / "expected" / _VERIFIED_NAME


def require_baseline(target_path: str, golden_dir: str | Path = DEFAULT_GOLDEN_DIR) -> Path:
    """Return the captured legacy ``.verified`` baseline for ``target_path``, or REFUSE.

    Looks for a captured baseline under ``golden_dir`` associated with ``target_path``. If present,
    returns its :class:`~pathlib.Path`. If absent, raises :class:`StranglerRefused` with a clear
    ``REFUSED: no captured legacy golden baseline for <path>`` message. NEVER creates the baseline.
    """
    if not target_path or not str(target_path).strip():
        raise StranglerRefused("REFUSED: no target path given for strangler extraction.")

    candidate = baseline_path(target_path, golden_dir)
    if candidate.is_file():
        return candidate

    # Fallback: honor any captured *.verified* file under the derived case dir (tolerant of the
    # golden plane naming the baseline slightly differently) — still refuse if none exists.
    case_dir = candidate.parent.parent
    if case_dir.is_dir():
        found = sorted(case_dir.rglob("*.verified*"))
        if found:
            return found[0]

    raise StranglerRefused(
        f"REFUSED: no captured legacy golden baseline for {target_path!r}. "
        "A strangler extraction requires a trusted equivalence reference — capture a legacy golden "
        "baseline (via /golden + human /golden-approve) first. The gate never fabricates one (P10)."
    )


def main(argv: list[str] | None = None) -> int:
    """CLI: refuse (exit 3) unless a captured legacy golden baseline exists for the target path.

    ``python -m tools.strangler_guard <target-path> [--golden-dir DIR]``. Exit 0 when a baseline is
    present, 3 on refusal — mirrors ``tools.golden_runner.approve`` (GoldenApprovalRefused -> exit 3).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Refuse a strangler extraction that lacks a captured legacy golden baseline (P10)."
    )
    parser.add_argument("target_path", help="the single legacy path being strangler-extracted")
    parser.add_argument(
        "--golden-dir",
        default=str(DEFAULT_GOLDEN_DIR),
        help="golden baseline root (default: repo golden/)",
    )
    args = parser.parse_args(argv)

    try:
        baseline = require_baseline(args.target_path, golden_dir=args.golden_dir)
    except StranglerRefused as exc:
        print(str(exc))
        return 3

    print(f"OK: captured legacy baseline present for {args.target_path!r} -> {baseline}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
