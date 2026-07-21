"""toy-converter path confinement stays strict after canonicalization (exit-code contract §4.5).

`IsConfined` compares the REAL path of --in/--out against the real paths of the allowed roots
(cwd + system temp), so two spellings of one directory no longer disagree: on macOS pytest's
tmp_path realpaths to /private/var/... while Path.GetTempPath() returns the /var/... spelling of
the same directory, and the pre-fix Ordinal compare of raw strings falsely tripped (exit 3).

Canonicalizing must NOT relax the guard, so this pins both directions:
  - a tmp path reached through a symlinked ancestor is ACCEPTED (the false-trip regression),
  - a genuine traversal escape is still REFUSED with exit 3.

The escape target is under /etc — unwritable — so a regressed guard cannot quietly succeed: it
would surface as exit 4 (IO failure), which this test's exit-3 assertion still fails on.

Spawns go through subprocess.run([list], shell=False) — never string+shell (T-06-01).
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run_converter(dotnet_exe: str, project: Path, in_path: Path, out_path: Path):
    return subprocess.run(
        [
            dotnet_exe,
            "run",
            "--project",
            str(project),
            "-c",
            "Release",
            "--",
            "--in",
            str(in_path),
            "--out",
            str(out_path),
        ],
        shell=False,
        capture_output=True,
        text=True,
    )


def _seed(tmp_path: Path) -> Path:
    seed = tmp_path / "seed.tsv"
    seed.write_bytes(b"timestamp\tparam_value\n2026-01-02T03:04:05Z\t1.5\n")
    return seed


def test_symlinked_tmp_ancestor_is_accepted(
    require_dotnet, tmp_path: Path, toy_converter_project: Path
) -> None:
    """A path whose ancestor is a symlink resolves to the same real dir → confined, exit 0."""
    real_dir = tmp_path / "real"
    real_dir.mkdir()
    link_dir = tmp_path / "via-link"
    link_dir.symlink_to(real_dir, target_is_directory=True)

    proc = _run_converter(
        require_dotnet, toy_converter_project, _seed(tmp_path), link_dir / "out.tsv"
    )
    assert proc.returncode == 0, (
        "an --out reached through a symlinked ancestor is the SAME real directory as the "
        f"allowed one and must be accepted, not refused. stdout/stderr:\n{proc.stdout}\n{proc.stderr}"
    )
    assert (real_dir / "out.tsv").exists(), "output must land in the real target directory"


def test_traversal_escape_is_still_refused(
    require_dotnet, tmp_path: Path, toy_converter_project: Path
) -> None:
    """Canonicalization must not weaken the guard: a real escape still exits 3."""
    escape = Path("/etc") / "toyconv-escape-probe.tsv"

    proc = _run_converter(require_dotnet, toy_converter_project, _seed(tmp_path), escape)
    assert proc.returncode == 3, (
        "an --out outside the workspace and the temp area must be refused with the §4.5 "
        f"confinement exit code 3. stdout/stderr:\n{proc.stdout}\n{proc.stderr}"
    )
    assert not escape.exists(), "a refused path must never be written"
