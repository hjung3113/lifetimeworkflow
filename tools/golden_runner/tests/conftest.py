"""Shared fixtures for the golden-runner integration tests (CONTRACT-03).

Provides the A-model spawn plumbing:
- ``dotnet_exe``   — the .NET executable resolved via an EXPLICIT absolute path
                     (``$DOTNET_ROOT/dotnet`` → ``$HOME/.dotnet/dotnet``), NEVER a bare PATH
                     lookup. The SessionStart bootstrap exports PATH, but that export does NOT
                     persist across separate tool invocations in the ephemeral session (project
                     risk P5 / threat T-06-01), so ``shutil.which("dotnet")`` / a bare ``"dotnet"``
                     string would intermittently fail. Mirror how 01-01 verify.sh hardcodes
                     ``$HOME/.dotnet/dotnet``.
- ``toy_converter_project`` — path to components/toy-converter/ToyConverter.csproj (spawn target).
- ``golden_out``   — a tmp ``--out`` path (converter writes here; kept out of the repo tree).
- ``require_dotnet`` — skips the test when the .NET SDK is not installed (egress-blocked env),
                     so the pure-Python suite (approve gate + recorded comparison) still runs.

All spawns go through ``subprocess.run([list], shell=False)`` (never string+shell) — see runner.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# --- import path wiring (virtual uv workspace members, not pip-installed) ---------------------
# tests -> golden_runner -> tools -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIBS_PYTHON = _REPO_ROOT / "libs" / "python"
for _p in (str(_REPO_ROOT), str(_LIBS_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.golden_runner.runner import resolve_dotnet  # noqa: E402


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return _REPO_ROOT


@pytest.fixture(scope="session")
def dotnet_exe() -> str:
    """The .NET executable, resolved via an explicit absolute path (never a bare PATH lookup)."""
    return resolve_dotnet()


@pytest.fixture(scope="session")
def toy_converter_project(repo_root: Path) -> Path:
    return repo_root / "components" / "toy-converter" / "ToyConverter.csproj"


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
