"""GEN-04 core→example single-direction dependency guard (SCOPE A: CODE deps only).

Proves the template invariant that makes the harness reusable: nothing under the CORE planes
(``tools/``, ``harness/``, ``libs/``) may import or path-reference an INSTANCE living under
``examples/``. A core file that grows an ``examples/`` path reference, a Python
``import examples`` / ``from examples ...``, or a surviving reference to the relocated
``components/toy-converter`` artifact is a one-directional-dependency leak that RED-flags the
suite (T-05-13 tamper-evidence: the negative-control tests below prove the scan is live).

SCOPE A — CODE dependency only, NOT prose purity. This guard does **not** flag bare ``libs/dotnet``
prose / authored surface (the ``dotnet-engineer`` persona, ``dotnet-conventions`` /
``normalization-catalog`` / ``pipeline-patterns`` skills, the ``new-normalization-rule`` command,
prose mentions in ``libs/normalize-spec.md`` etc.). That DOMAIN/LANGUAGE authored-surface
genericization is legitimately deferred to GEN-05; flagging it here would over-reach and RED the
suite on deferred content.

Mirrors the structural-scan idiom of ``test_commands.py`` (repo root via ``parents[3]``,
enumeration-driven, no runtime import of any example module). The tracked set is discovered with
``git ls-files`` (subprocess, ``shell=False``) so only committed core files are scanned.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# test_core_no_example_dep.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]

# Core planes whose tracked files must not depend on any example instance.
_CORE_ROOTS = ("tools", "harness", "libs")

# This guard file itself holds the forbidden tokens as negative-control literals; it is EXCLUDED
# from the scanned set (scan the tracked core set MINUS this file), or the guard would flag itself.
_SELF = Path(__file__).resolve()

# Forbidden CODE-dependency path tokens (SCOPE A): an ``examples/`` path reference, and the
# relocated-artifact token ``components/toy-converter`` (moved to the example — a surviving core ref
# by the OLD path is a leak). Bare ``libs/dotnet`` is intentionally NOT here (deferred to GEN-05).
_PATH_TOKENS = ("examples/", "components/toy-converter")

# A Python import of the example package.
_IMPORT_EXAMPLES = re.compile(r"^\s*(from|import)\s+examples\b")

# The single sanctioned instance-pointer datum: the ``harness/project.toml`` ``[instance] root``
# value line. ``root=""`` in this repo → no ``examples/`` reference exists to exempt, but the
# exemption is encoded so a downstream instance that sets ``root = "examples/<name>"`` (the one
# sanctioned place a core file names an instance) does not trip the guard.
_INSTANCE_ROOT_FILE = "harness/project.toml"


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


def _is_instance_root_line(rel_path: str, line: str) -> bool:
    """The one sanctioned exemption: the ``[instance] root = "..."`` datum in harness/project.toml."""
    return rel_path == _INSTANCE_ROOT_FILE and re.match(r"\s*root\s*=", line) is not None


def _scan_lines(rel_path: str, text: str) -> list[tuple[int, str]]:
    """Return ``(lineno, line)`` hits: an ``examples/`` or ``components/toy-converter`` path ref, or
    an ``import examples`` — skipping the single sanctioned ``harness/project.toml`` root line."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if _is_instance_root_line(rel_path, line):
            continue
        if any(tok in line for tok in _PATH_TOKENS) or _IMPORT_EXAMPLES.match(line):
            hits.append((lineno, line))
    return hits


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None  # binary/unreadable — no textual dependency to scan


def test_core_has_no_example_dependency() -> None:
    """No tracked file under tools/, harness/, libs/ path-references examples/ or the moved artifact."""
    offenders: list[str] = []
    for path in _tracked_core_files():
        text = _read_text(path)
        if text is None:
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for lineno, line in _scan_lines(rel, text):
            offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "core→example dependency leak (SCOPE A) — core planes must not depend on an instance:\n"
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


def test_instance_root_pointer_is_exempt() -> None:
    """The sanctioned harness/project.toml [instance] root datum is exempt even if it names examples/."""
    hits = _scan_lines(_INSTANCE_ROOT_FILE, 'root = "examples/log-parser"')
    assert not hits, "the sanctioned [instance] root pointer must be exempt from the guard"
