"""RED->GREEN proof for the HOOK-01 format-on-write PostToolUse fixer.

The gate canonicalizes every Write/Edit target at the byte level (strip UTF-8 BOM, fold
CRLF/CR -> LF — the §4.3-4.6 R1+R2 rule REUSED from ``libs/python/normalize/core`` so there is
no divergent normalizer, D-02), then runs a language formatter as a SUBPROCESS: ``ruff format``
for ``.py`` and ``dotnet format`` for ``.cs`` (dotnet-gated). Key invariants proved here:

* **Byte fix** — a BOM+CRLF file becomes no-BOM / LF (``fix_bytes`` and ``format_file``).
* **Idempotent** — a second pass yields byte-identical output (Open Q3 re-entry: the formatter
  mutates via the file system / a subprocess, never a Claude Write, so a re-run is a no-op).
* **ruff via subprocess** — a ``.py`` target invokes ``ruff format`` as an argv subprocess
  (asserted with a monkeypatched ``subprocess.run`` spy), never a Claude Write tool.
* **dotnet gated-skip** — a ``.cs`` target with dotnet absent records a ``SKIP`` and does NOT
  raise or spawn anything; the gate still exits 0 (Pitfall 3 / D-05 — an env limitation must
  never turn every edit red).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tools.hooks import format_on_write
from tools.hooks.format_on_write import fix_bytes, format_file

_REPO_ROOT = Path(__file__).resolve().parents[3]


# --- fix_bytes: §4.3-4.6 R1 (BOM strip) + R2 (LF), idempotent -----------------------------------


def test_fix_bytes_strips_bom_and_crlf() -> None:
    assert fix_bytes(b"\xef\xbb\xbfa\r\nb\r\n") == b"a\nb\n"


def test_fix_bytes_folds_bare_cr() -> None:
    assert fix_bytes(b"a\rb\r") == b"a\nb\n"


def test_fix_bytes_no_bom_lf_unchanged() -> None:
    assert fix_bytes(b"a\nb\n") == b"a\nb\n"


def test_fix_bytes_idempotent() -> None:
    for raw in (b"\xef\xbb\xbfx\r\ny\r\n", b"a\nb\n", b"", b"trailing-no-nl", b"m\rn"):
        once = fix_bytes(raw)
        assert fix_bytes(once) == once, f"not idempotent for {raw!r}"


def test_fix_bytes_reuses_normalize_core() -> None:
    # D-02: the byte rule is the SAME §4.3-4.6 rule as the TSV comparator — not a fresh normalizer.
    from normalize.core import strip_bom_normalize_newlines

    raw = b"\xef\xbb\xbfhello\r\nworld\r\n"
    assert fix_bytes(raw) == strip_bom_normalize_newlines(raw).encode("utf-8")


# --- format_file: writes the byte-fixed content back (no-BOM / LF), idempotent ------------------


def test_format_file_rewrites_bom_crlf_to_lf(tmp_path: Path) -> None:
    f = tmp_path / "sample.txt"
    f.write_bytes(b"\xef\xbb\xbfalpha\r\nbeta\r\n")
    format_file(f)
    assert f.read_bytes() == b"alpha\nbeta\n"


def test_format_file_idempotent(tmp_path: Path) -> None:
    f = tmp_path / "sample.txt"
    f.write_bytes(b"\xef\xbb\xbfalpha\r\nbeta\r\n")
    format_file(f)
    once = f.read_bytes()
    format_file(f)
    assert f.read_bytes() == once


def test_format_file_missing_path_is_noop(tmp_path: Path) -> None:
    # A path that does not exist must not raise (PostToolUse never fails an edit).
    format_file(tmp_path / "does-not-exist.txt")


# --- .py: ruff via an argv subprocess (spy), byte-fix via the file system (not a Claude Write) --


def test_py_file_invokes_ruff_subprocess(tmp_path: Path, monkeypatch) -> None:
    calls: list[list[str]] = []

    def _spy(cmd, *args, **kwargs):
        calls.append(list(cmd))

        class _R:
            returncode = 0

        return _R()

    monkeypatch.setattr(format_on_write.subprocess, "run", _spy)
    f = tmp_path / "mod.py"
    f.write_bytes(b"\xef\xbb\xbfx = 1\r\n")
    format_file(f)

    # Byte-fix applied via the file system (NOT the spied subprocess) -> no BOM, LF.
    assert f.read_bytes() == b"x = 1\n"
    # ruff format invoked as argv (a list, not a shell string) with the target path.
    assert any(cmd[:2] == ["ruff", "format"] and str(f) in cmd for cmd in calls)


# --- .cs: gated-skip when dotnet is absent (no raise, no spawn, logged SKIP) --------------------


def test_cs_file_skips_when_dotnet_absent(tmp_path: Path) -> None:
    f = tmp_path / "Type.cs"
    f.write_bytes(b"\xef\xbb\xbfclass C {}\r\n")
    missing = str(tmp_path / "nowhere" / "dotnet")
    log = format_file(f, dotnet_exe=missing)  # must NOT raise
    # Byte-fix still applied even though the .NET formatter is skipped.
    assert f.read_bytes() == b"class C {}\n"
    assert any("SKIP" in line for line in log)


def test_cs_file_does_not_spawn_when_dotnet_absent(tmp_path: Path, monkeypatch) -> None:
    ran: list[list[str]] = []

    def _spy(cmd, *args, **kwargs):
        ran.append(list(cmd))

        class _R:
            returncode = 0

        return _R()

    monkeypatch.setattr(format_on_write.subprocess, "run", _spy)
    f = tmp_path / "Type.cs"
    f.write_bytes(b"class C {}\n")
    format_file(f, dotnet_exe=str(tmp_path / "absent-dotnet"))
    assert ran == []  # dotnet absent -> nothing spawned


# --- main(): stdin -> mutates the target, always exit 0, SKIP on stderr -------------------------


def _run_main(payload: dict, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "tools.hooks.format_on_write"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        env=env,
    )


def test_main_fixes_bytes_exit0(tmp_path: Path) -> None:
    f = tmp_path / "f.txt"
    f.write_bytes(b"\xef\xbb\xbfa\r\nb\r\n")
    proc = _run_main({"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    assert proc.returncode == 0
    assert f.read_bytes() == b"a\nb\n"


def test_main_second_run_is_noop(tmp_path: Path) -> None:
    f = tmp_path / "f.txt"
    f.write_bytes(b"\xef\xbb\xbfa\r\nb\r\n")
    _run_main({"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    once = f.read_bytes()
    _run_main({"tool_name": "Write", "tool_input": {"file_path": str(f)}})
    assert f.read_bytes() == once


def test_main_cs_dotnet_absent_skip_stderr_exit0(tmp_path: Path) -> None:
    f = tmp_path / "T.cs"
    f.write_bytes(b"class C {}\r\n")
    env = {**os.environ, "DOTNET_ROOT": str(tmp_path / "no-dotnet-here")}
    proc = _run_main(
        {"tool_name": "Write", "tool_input": {"file_path": str(f)}},
        env=env,
    )
    assert proc.returncode == 0
    assert f.read_bytes() == b"class C {}\n"
    assert "SKIP" in proc.stderr


def test_main_malformed_stdin_exit0(tmp_path: Path) -> None:
    proc = subprocess.run(
        [sys.executable, "-m", "tools.hooks.format_on_write"],
        input="}{ not json",
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
    )
    assert proc.returncode == 0
