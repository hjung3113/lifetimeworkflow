"""HOOK-01 format-on-write — a PostToolUse(Write|Edit) fixer (encoding hygiene + formatters).

On every Write/Edit the gate canonicalizes the target's BYTES (strip a UTF-8 BOM, fold CRLF/CR
-> LF — the §4.3-4.6 R1+R2 rule REUSED verbatim from ``normalize.core``; no divergent normalizer,
D-02), then runs a language formatter as a SUBPROCESS: ``ruff format`` for ``.py`` and
``dotnet format`` for ``.cs``.

Design invariants
-----------------
* **No re-entry (Open Q3).** The fix mutates the file via the file system / a child process, NEVER
  a Claude Write tool — so it does not re-trigger this PostToolUse hook. Combined with idempotency
  (a second pass yields identical bytes), a re-run is a guaranteed no-op (T-04-10).
* **dotnet-gated, skip-gracefully.** ``.cs`` formatting probes an EXPLICIT dotnet path
  (``$DOTNET_ROOT/dotnet`` -> ``~/.dotnet/dotnet``, the golden_runner pattern — a bare PATH lookup
  does not survive across tool invocations, P5). When dotnet is absent the step is SKIPPED with a
  logged ``SKIP`` line; the gate still exits 0. An env limitation must never turn every edit red
  (Pitfall 3 / D-05, T-04-11).
* **No shell.** Formatters are spawned with ``subprocess.run([argv], shell=False)`` — never a
  shell string, so a hostile ``file_path`` cannot inject a command (T-04-12).
* **PostToolUse does not block.** ``main`` always returns 0; encoding hygiene is applied silently
  and a dotnet SKIP is advisory (stderr).

Composition note: the general-path BOM/CRLF auto-fix is THIS gate's job — contract-guard's
PreToolUse polyglot deny (04-03) is scoped to the constitution plane only, so this PostToolUse fix
is reachable on ordinary source paths.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# --- import the shared §4.3-4.6 byte rule (libs/python is a virtual uv workspace member, not
# installed) — mirrors tools/golden_runner/runner.py's sys.path wiring. ------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]  # hooks -> tools -> repo root
_LIBS_PYTHON = _REPO_ROOT / "libs" / "python"
if str(_LIBS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_LIBS_PYTHON))

from normalize.core import strip_bom_normalize_newlines  # noqa: E402

from tools.hooks._stdin import parse_event, read_stdin  # noqa: E402


def fix_bytes(raw: bytes) -> bytes:
    """Canonicalize raw file bytes to no-BOM / LF (§4.3-4.6 R1+R2), reusing ``normalize.core``.

    Idempotent by construction: once the BOM is stripped and newlines are LF, a second pass
    decodes the same text (``utf-8-sig`` also accepts BOM-less input) and re-encodes to identical
    BOM-less UTF-8 bytes.
    """
    return strip_bom_normalize_newlines(raw).encode("utf-8")


def resolve_dotnet(dotnet_exe: str | None = None) -> str:
    """Resolve the .NET executable via an EXPLICIT absolute path — never a bare PATH lookup (P5).

    ``$DOTNET_ROOT/dotnet`` when DOTNET_ROOT is set, else ``$HOME/.dotnet/dotnet`` (where the
    SessionStart bootstrap installs it). Mirrors ``golden_runner.resolve_dotnet``.
    """
    if dotnet_exe is not None:
        return dotnet_exe
    root = os.environ.get("DOTNET_ROOT") or os.path.join(os.path.expanduser("~"), ".dotnet")
    return os.path.join(root, "dotnet")


def format_file(path: str | os.PathLike[str], *, dotnet_exe: str | None = None) -> list[str]:
    """Byte-fix ``path`` then run its language formatter as a subprocess. Return advisory log lines.

    Steps (never raises for a normal edit):
      1. Missing path -> no-op (nothing to format).
      2. Read bytes, apply :func:`fix_bytes`; write back ONLY if changed (file-system write, not a
         Claude Write -> no PostToolUse re-entry).
      3. ``.py`` -> ``ruff format <path>`` via ``subprocess.run([...], shell=False)``.
      4. ``.cs`` -> ``dotnet format --include <path>`` only when the resolved dotnet exists; else a
         logged ``SKIP`` (Pitfall 3 / D-05 — an env limitation is never a failure).
    """
    log: list[str] = []
    p = Path(path)
    if not p.is_file():
        return log

    raw = p.read_bytes()
    fixed = fix_bytes(raw)
    if fixed != raw:
        p.write_bytes(fixed)  # FS write (NOT a Claude Write) -> no hook re-entry
        log.append(f"bytes-fixed {p}")

    suffix = p.suffix.lower()
    if suffix == ".py":
        subprocess.run(["ruff", "format", str(p)], shell=False, check=False, capture_output=True)
        log.append(f"ruff-format {p}")
    elif suffix == ".cs":
        dotnet = resolve_dotnet(dotnet_exe)
        if os.path.isfile(dotnet):
            subprocess.run(
                [dotnet, "format", "--include", str(p)],
                shell=False,
                check=False,
                capture_output=True,
            )
            log.append(f"dotnet-format {p}")
        else:
            log.append(f"SKIP: dotnet absent ({dotnet}) — .cs formatting skipped for {p}")

    return log


def main() -> int:
    """PostToolUse entrypoint: parse stdin, byte-fix + format the target, ALWAYS exit 0.

    PostToolUse does not block an edit; the byte fix is applied silently and any ``SKIP`` (e.g.
    dotnet absent) is written to stderr as advisory context. Malformed stdin -> safe sentinel
    (empty ``file_path``) -> no-op.
    """
    event = parse_event(read_stdin())
    if event.file_path:
        for line in format_file(event.file_path):
            if line.startswith("SKIP"):
                print(line, file=sys.stderr)
    return 0  # PostToolUse never fails an edit; env-limitation is a logged SKIP (Pitfall 3)


if __name__ == "__main__":
    raise SystemExit(main())
