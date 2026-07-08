"""Golden-runner loop (CONTRACT-03, D-01/D-02/D-03).

For a golden case the runner:
  1. resolves the .NET executable via an EXPLICIT absolute path ($DOTNET_ROOT/dotnet →
     $HOME/.dotnet/dotnet) — NOT a bare PATH lookup (the bootstrap's PATH export does not persist
     across separate tool invocations; project risk P5 / threat T-06-01),
  2. spawns the fixture-grade .NET toy converter via subprocess.run([list], shell=False) — never
     string+shell — passing the seed as --in and a tmp --out,
  3. reads the converter's --out FILE (the A-model boundary is a file, not stdout; §4.5),
  4. normalizes BOTH that output and the approved expected/baseline.verified.tsv via the shared
     §4-5 Python core (never a byte-diff — Pitfall P4),
  5. diffs the normalized strings: equal → PASS; differ → FAIL and write a machine-proposed
     expected/baseline.received.tsv, NEVER overwriting the human-approved .verified baseline (P9).

This module contains the pure comparison logic (``compare``) SEPARATE from the .NET spawn
(``run_converter``) so the normalize+diff path is testable without a live .NET runtime.
"""

from __future__ import annotations

import difflib
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

# --- import the shared §4-5 core (libs/python is a virtual uv workspace member, not installed) ---
REPO_ROOT = Path(__file__).resolve().parents[2]  # golden_runner -> tools -> repo root
_LIBS_PYTHON = REPO_ROOT / "libs" / "python"
if str(_LIBS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_LIBS_PYTHON))

from normalize.core import normalize_tsv  # noqa: E402

GOLDEN_DIR = REPO_ROOT / "golden"
TOY_CONVERTER_PROJECT = REPO_ROOT / "components" / "toy-converter" / "ToyConverter.csproj"


class GoldenRunnerError(RuntimeError):
    """The converter failed to run (non-zero exit) or a path escaped its confinement."""


@dataclass(frozen=True)
class GoldenResult:
    """Outcome of one golden case."""

    case: str
    passed: bool
    diff: str
    received_path: Path | None  # set only on FAIL (machine-proposed baseline)


# --- path helpers -----------------------------------------------------------------------------


def case_dir(case: str) -> Path:
    return GOLDEN_DIR / case


def seed_path(case: str) -> Path:
    return case_dir(case) / "input" / "seed.tsv"


def verified_path(case: str) -> Path:
    """The human-approved baseline the runner diffs against and NEVER overwrites (P9)."""
    return case_dir(case) / "expected" / "baseline.verified.tsv"


# ``baseline`` and ``verified`` are the same file; the alias reads naturally in both contexts.
baseline_path = verified_path


def received_path(case: str) -> Path:
    """The machine-proposed baseline written on FAIL; /golden-approve may later promote it."""
    return case_dir(case) / "expected" / "baseline.received.tsv"


def resolve_dotnet() -> str:
    """Resolve the .NET executable via an explicit absolute path — never a bare PATH lookup (P5).

    ``$DOTNET_ROOT/dotnet`` when DOTNET_ROOT is set, else ``$HOME/.dotnet/dotnet`` (where the
    SessionStart bootstrap installs it). Mirrors 01-01 verify.sh, which hardcodes the same path.
    """
    root = os.environ.get("DOTNET_ROOT") or os.path.join(os.path.expanduser("~"), ".dotnet")
    return os.path.join(root, "dotnet")


def _confine(path: Path) -> Path:
    """Resolve and confine a path to the repo or the system temp area (T-06-02)."""
    resolved = path.resolve()
    allowed_roots = (
        REPO_ROOT.resolve(),
        Path(os.path.realpath("/tmp")),
        Path(os.environ.get("TMPDIR", "/tmp")).resolve(),
    )
    for root in allowed_roots:
        try:
            resolved.relative_to(root)
            return resolved
        except ValueError:
            continue
    raise GoldenRunnerError(f"path escapes confinement (repo/temp): {resolved}")


# --- pure comparison logic (no .NET needed) ---------------------------------------------------


def compare(output_bytes: bytes, case: str) -> GoldenResult:
    """Normalize the converter output AND the approved baseline via the §4-5 core, then diff.

    On mismatch, write ``expected/baseline.received.tsv`` (the raw converter output — the exact
    bytes a human would review) and return FAIL. NEVER touch ``baseline.verified.tsv``.
    """
    normalized_new = normalize_tsv(output_bytes)
    normalized_baseline = normalize_tsv(verified_path(case).read_bytes())

    if normalized_new == normalized_baseline:
        return GoldenResult(case=case, passed=True, diff="", received_path=None)

    diff = "\n".join(
        difflib.unified_diff(
            normalized_baseline.splitlines(),
            normalized_new.splitlines(),
            fromfile=f"{case}/baseline.verified (normalized)",
            tofile=f"{case}/converter-output (normalized)",
            lineterm="",
        )
    )

    rec = received_path(case)
    rec.parent.mkdir(parents=True, exist_ok=True)
    rec.write_bytes(output_bytes)  # machine-proposed; .verified is left untouched (P9)
    return GoldenResult(case=case, passed=False, diff=diff, received_path=rec)


# --- .NET spawn (A-model boundary) ------------------------------------------------------------


def run_converter(
    seed: Path,
    out_path: Path,
    dotnet_exe: str | None = None,
    project: Path | None = None,
) -> int:
    """Spawn the .NET toy converter over the A-model CLI boundary; return its exit code.

    subprocess.run([list], shell=False) — never string+shell (T-06-01). Paths are confined.
    """
    dotnet_exe = dotnet_exe or resolve_dotnet()
    project = project or TOY_CONVERTER_PROJECT
    seed = _confine(seed)
    out_path = _confine(out_path)

    proc = subprocess.run(
        [
            dotnet_exe,
            "run",
            "--project",
            str(project),
            "-c",
            "Release",
            "--",
            "--in",
            str(seed),
            "--out",
            str(out_path),
        ],
        shell=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise GoldenRunnerError(
            f"toy-converter exited {proc.returncode}: {proc.stderr.strip() or proc.stdout.strip()}"
        )
    return proc.returncode


def run_golden_case(
    case: str,
    out_path: Path,
    dotnet_exe: str | None = None,
    project: Path | None = None,
) -> GoldenResult:
    """Full loop for one case: spawn converter → read --out → normalize both sides → diff."""
    run_converter(seed_path(case), out_path, dotnet_exe=dotnet_exe, project=project)
    output_bytes = Path(out_path).read_bytes()
    return compare(output_bytes, case)


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m tools.golden_runner.runner <case> [--out PATH]``. Exit 0 PASS, 1 FAIL."""
    import argparse
    import tempfile

    parser = argparse.ArgumentParser(description="Run one golden equivalence case.")
    parser.add_argument("case", help="golden case id (e.g. repr-only)")
    parser.add_argument("--out", default=None, help="converter --out path (default: a temp file)")
    args = parser.parse_args(argv)

    out = Path(args.out) if args.out else Path(tempfile.mkstemp(suffix=".tsv")[1])
    result = run_golden_case(args.case, out)
    if result.passed:
        print(f"PASS  {result.case}")
        return 0
    print(f"FAIL  {result.case}\n{result.diff}")
    print(f"\n.received written to {result.received_path} (NOT promoted — human sign-off req'd).")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
