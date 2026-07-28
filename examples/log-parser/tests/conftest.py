"""Shared fixtures for the RELOCATED log-parser domain golden tests (GEN-01, 05-03).

These tests moved out of `tools/golden_runner/tests/` into the example so the core template
names no domain artifact. They import the core runner (example→core, the one allowed direction)
and drive it against the EXAMPLE's own golden tree + .NET converter via the 05-02 overrides
(`golden_dir=`, `project=`). Fixtures mirror the generic core conftest so the .NET-gated cases
SKIP cleanly when the SDK is absent (egress-blocked env), while the pure-Python recorded-output
comparison still runs.

All spawns go through ``subprocess.run([list], shell=False)`` (never string+shell) — see runner.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# --- import path wiring (virtual uv workspace members, not pip-installed) ---------------------
# tests -> log-parser -> examples -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_INSTANCE_ROOT = Path(__file__).resolve().parents[1]
_LIBS_PYTHON = _REPO_ROOT / "libs" / "python"
for _p in (str(_REPO_ROOT), str(_INSTANCE_ROOT), str(_LIBS_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from golden_runner.runner import resolve_dotnet  # noqa: E402

# The example's own relocated golden tree + .NET converter project (05-03 move set).
_EXAMPLE_ROOT = Path(__file__).resolve().parents[1]  # examples/log-parser
EXAMPLE_GOLDEN_DIR = _EXAMPLE_ROOT / "golden"
EXAMPLE_CONVERTER_PROJECT = _EXAMPLE_ROOT / "components" / "toy-converter" / "ToyConverter.csproj"


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return _REPO_ROOT


@pytest.fixture(scope="session")
def example_golden_dir() -> Path:
    """Case root for the relocated domain golden cases (repr-only / value-regression)."""
    return EXAMPLE_GOLDEN_DIR


@pytest.fixture(scope="session")
def toy_converter_project() -> Path:
    """The example's relocated .NET converter project (spawn target)."""
    return EXAMPLE_CONVERTER_PROJECT


@pytest.fixture(scope="session")
def dotnet_exe() -> str:
    """The .NET executable, resolved via an explicit absolute path (never a bare PATH lookup)."""
    return resolve_dotnet()


@pytest.fixture()
def golden_out(tmp_path: Path) -> Path:
    """A tmp --out path for the converter (kept outside the repo tree; auto-cleaned by pytest)."""
    return tmp_path / "toyconv_out.tsv"


@pytest.fixture()
def require_dotnet(dotnet_exe: str):
    """Skip a spawn-dependent test when the .NET SDK is not installed.

    In this container the .NET 10 download is egress-blocked, so the end-to-end spawn tests are
    skipped rather than failed. They go green with zero code changes once .NET 10 is available.
    """
    if not Path(dotnet_exe).exists():
        pytest.skip(
            f"dotnet not installed at {dotnet_exe} — end-to-end golden spawn deferred "
            "(.NET 10 egress-blocked; see 01-06-SUMMARY.md)."
        )
    return dotnet_exe
