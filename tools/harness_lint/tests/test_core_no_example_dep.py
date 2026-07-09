"""GEN-04/GEN-05 core→example single-direction guard (SCOPE-A code deps + prose purity).

Proves the template invariant that makes the harness reusable: nothing under the CORE planes
(``tools/``, ``harness/``, ``libs/``) may import or path-reference an INSTANCE living under
``examples/`` (SCOPE A), NOR carry the DOMAIN/LANGUAGE prose of a moved-asset or the
semiconductor domain (GEN-05 prose tier). A core file that grows an ``examples/`` path
reference, a Python ``import examples`` / ``from examples ...``, a surviving reference to the
relocated ``components/toy-converter`` artifact, or one of the narrow prose tokens below is a
one-directional-dependency / vocabulary leak that RED-flags the suite (T-05-13 + T-055-06
tamper-evidence: the negative-control tests below prove the scan is live).

Two token tiers are enforced:

* **SCOPE A — code dependency** (``_PATH_TOKENS`` + ``_IMPORT_EXAMPLES``): ``examples/`` path
  refs, the relocated ``components/toy-converter`` artifact, and ``import examples``.
* **GEN-05 — prose purity** (``_PROSE_TOKENS``): the proper nouns of the moved assets
  (``dotnet-engineer``, ``dotnet-conventions``, ``normalization-catalog``, ``pipeline-patterns``),
  the moved data path ``libs/dotnet``, and rare semiconductor vocabulary (``equipment``,
  ``standard-log``, ``correction-rules``, ``wafer``, ``설비``).

The prose tier is deliberately NARROW: it EXCLUDES the bare general terms
``dotnet`` / ``.NET`` / ``parser`` / ``converter`` / ``normalize`` / ``log-parser``. Those appear
legitimately in core (argparse ``parser`` variables, ``golden_runner`` spawning "the .NET
converter", ``logparser-*`` package names, "the log-parser example" comments) and flagging them
would over-reach and RED the suite on legitimately-general text (T-055-08).

Mirrors the structural-scan idiom of ``test_commands.py`` (repo root via ``parents[3]``,
enumeration-driven, no runtime import of any example module). The tracked set is discovered with
``git ls-files`` (subprocess, ``shell=False``) so only committed core files are scanned.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

# test_core_no_example_dep.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Core planes whose tracked files must not depend on any example instance.
_CORE_ROOTS = ("tools", "harness", "libs")

# This guard file itself holds the forbidden tokens as negative-control literals; it is EXCLUDED
# from the scanned set (scan the tracked core set MINUS this file), or the guard would flag itself.
_SELF = Path(__file__).resolve()

# Forbidden CODE-dependency path tokens (SCOPE A): an ``examples/`` path reference, and the
# relocated-artifact token ``components/toy-converter`` (moved to the example — a surviving core ref
# by the OLD path is a leak).
_PATH_TOKENS = ("examples/", "components/toy-converter")

# Prose domain/language tokens (GEN-05): moved-asset proper nouns + rare domain vocab.
# NARROW on purpose — NO bare dotnet/.NET/parser/converter/normalize/log-parser (those are general, stay).
_PROSE_TOKENS = (
    "dotnet-engineer",
    "dotnet-conventions",
    "normalization-catalog",
    "pipeline-patterns",
    "libs/dotnet",
    "equipment",
    "standard-log",
    "correction-rules",
    "wafer",
    "설비",
)

# A Python import of the example package.
_IMPORT_EXAMPLES = re.compile(r"^\s*(from|import)\s+examples\b")

# The single sanctioned instance-pointer file: ``harness/project.toml``. Its ``[instance] root``
# value and its per-language ``persona =`` values are the ONE place a core-plane file names an
# instance-owned asset (ADR-0002 (c)). The ``dotnet.persona`` line points at
# ``examples/log-parser/agents/dotnet-engineer.md`` — a single line that legitimately contains BOTH
# the SCOPE-A ``examples/`` token AND the GEN-05 ``dotnet-engineer`` token — so the whole pointer
# line is exempted.
_INSTANCE_ROOT_FILE = "harness/project.toml"

# Matches the sanctioned instance-pointer lines in project.toml: ``root = ...`` and ``persona = ...``.
_INSTANCE_POINTER_LINE = re.compile(r"\s*(root|persona)\s*=")


def _tracked_core_files() -> list[Path]:
    """Tracked files under the core planes (``git ls-files``), MINUS this guard file itself."""
    completed = subprocess.run(
        ["git", "ls-files", *_CORE_ROOTS],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    files: list[Path] = []
    for rel in completed.stdout.splitlines():
        rel = rel.strip()
        if not rel:
            continue
        resolved = (_REPO_ROOT / rel).resolve()
        if resolved == _SELF:
            continue  # negative-control literals live here — never scan self
        files.append(resolved)
    return files


def _is_instance_pointer_line(rel_path: str, line: str) -> bool:
    """The one sanctioned exemption: the ``root =`` / ``persona =`` instance-pointer lines in
    harness/project.toml (ADR-0002 (c)) — the only core-plane place that may name an instance asset."""
    return rel_path == _INSTANCE_ROOT_FILE and _INSTANCE_POINTER_LINE.match(line) is not None


def _scan_lines(rel_path: str, text: str) -> list[tuple[int, str]]:
    """Return ``(lineno, line)`` hits: a SCOPE-A ``examples/`` / ``components/toy-converter`` path
    ref or ``import examples``, OR a GEN-05 ``_PROSE_TOKENS`` prose token — skipping the sanctioned
    ``harness/project.toml`` instance-pointer (``root =`` / ``persona =``) lines."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _is_instance_pointer_line(rel_path, line):
            continue
        if (
            any(tok in line for tok in _PATH_TOKENS)
            or any(tok in line for tok in _PROSE_TOKENS)
            or _IMPORT_EXAMPLES.match(line)
        ):
            hits.append((lineno, line))
    return hits


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None  # binary/unreadable — no textual dependency to scan


def test_core_has_no_example_dependency() -> None:
    """No tracked file under tools/, harness/, libs/ path-references examples/, the moved artifact,
    or carries a GEN-05 domain/moved-asset prose token."""
    offenders: list[str] = []
    for path in _tracked_core_files():
        text = _read_text(path)
        if text is None:
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for lineno, line in _scan_lines(rel, text):
            offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "core→example dependency/prose leak — core planes must not depend on or name an instance:\n"
        + "\n".join(offenders)
    )


def test_negative_control_flags_synthetic_example_ref() -> None:
    """Scan is live: a crafted examples/ path ref is flagged (the guard cannot silently no-op)."""
    hits = _scan_lines("tools/fake_core_module.py", "x = 'examples/log-parser/foo'")
    assert hits, "negative control failed: scan did not flag a synthetic examples/ reference"


def test_negative_control_flags_moved_artifact_token() -> None:
    """Scan is live: a crafted components/toy-converter path ref is flagged."""
    hits = _scan_lines("tools/fake_core_module.py", "p = 'components/toy-converter/x.csproj'")
    assert hits, "negative control failed: scan did not flag a components/toy-converter reference"


def test_negative_control_flags_import_examples() -> None:
    """Scan is live: a Python ``from examples import ...`` is flagged."""
    hits = _scan_lines("tools/fake_core_module.py", "from examples.log_parser import thing")
    assert hits, "negative control failed: scan did not flag an `import examples`"


@pytest.mark.parametrize("token", _PROSE_TOKENS)
def test_negative_control_flags_each_prose_token(token: str) -> None:
    """Scan is live per prose token: a synthetic core line naming the token IS flagged.

    ``wafer`` and ``설비`` have 0 real occurrences in core — they are guaranteed-live anchors
    proving the prose scan cannot silently no-op (T-055-07)."""
    hits = _scan_lines("tools/fake_core_module.py", f"# ref to {token}")
    assert hits, f"negative control failed: prose scan did not flag a synthetic '{token}' reference"


def test_instance_root_pointer_is_exempt() -> None:
    """The sanctioned harness/project.toml [instance] root datum is exempt even if it names examples/."""
    hits = _scan_lines(_INSTANCE_ROOT_FILE, 'root = "examples/log-parser"')
    assert not hits, "the sanctioned [instance] root pointer must be exempt from the guard"


def test_instance_pointer_persona_is_exempt() -> None:
    """The sanctioned harness/project.toml persona pointer is exempt even though it contains BOTH an
    ``examples/`` (SCOPE-A) and a ``dotnet-engineer`` (GEN-05) token on one line (T-055-09)."""
    hits = _scan_lines(
        _INSTANCE_ROOT_FILE, 'persona = "examples/log-parser/agents/dotnet-engineer.md"'
    )
    assert not hits, "the sanctioned dotnet.persona instance pointer must be exempt from the guard"
