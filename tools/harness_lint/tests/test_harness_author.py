"""Structural gate for `harness/skills/harness-author/SKILL.md` (Phase 50a, MONO-10/MONO-11).

Proves Success Criteria 1 and 3 of `.planning/phases/50a-harness-authoring/50a-01-PLAN.md`:

1. Every `path:line`/anchor citation the skill body offers as a default actually resolves in this
   checkout (`test_citations_resolve_in_harness_author_skill`) — closing the "plausible-but-dead
   citation" failure mode CONTEXT.md's citation-anchoring decision exists to prevent
   (`50a-CONTEXT.md:38-39`).
2. No tracked file outside `.planning/` still names the absorbed `skill-creator` skill
   (`test_no_tracked_reference_to_skill_creator`), backed by a negative control proving the scan
   cannot silently no-op (`test_dangling_reference_scan_is_live`) — the repo's "checks that cannot
   fail" defect class (T-50a-03).
3. Everything `skill-creator` did stays reachable in the wider `harness-author` skill
   (`test_harness_author_reachability`).

Mirrors `test_core_no_example_dep.py`'s `git ls-files`-scoped scan idiom and single-assert-with-
joined-offenders pattern; NOT a copy — this module scans backtick-quoted inline citations inside a
single skill body, not whole-repo path tokens.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

# test_harness_author.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_HARNESS_AUTHOR_SKILL = _REPO_ROOT / "harness" / "skills" / "harness-author" / "SKILL.md"

# Tracked-file scan scope for the dangling-reference test — matches CONTEXT.md's "complete
# tracked-tree change-set" list, explicitly EXCLUDING .planning/ (append-only history, out of
# scope per RESEARCH.md Pitfall 2 / Assumption A2).
_SCAN_TARGETS = ("AGENTS.md", "CLAUDE.md", "harness", "tools", ".opencode", ".claude")

# This guard file itself holds the forbidden literal as documentation/negative-control text; it is
# EXCLUDED from the scanned set (mirrors test_core_no_example_dep.py's `_SELF` exemption), or the
# guard would flag itself.
_SELF = Path(__file__).resolve()

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)

# A backtick-quoted inline citation shaped `<relative/path.ext>[:anchor]` — the path segment must
# contain a dot-extension so plain identifiers (e.g. `` `EXPECTED_SKILLS` ``) are not mistaken for
# a path citation; those are validated separately via the reachability test instead.
_CITATION_RE = re.compile(
    r"`(?P<path>[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)(?::(?P<anchor>[A-Za-z0-9_.:-]+))?`"
)

_NUMERIC_RANGE_RE = re.compile(r"^(?P<start>\d+)-(?P<end>\d+)$")


def _strip_fences(text: str) -> str:
    """Remove fenced ```-delimited code blocks — a citation inside an illustrative fence is an
    example, not a claim about this checkout (mirrors test_core_no_example_dep.py's pointer-line
    exemption idiom, applied to fenced spans instead of single lines)."""
    return _FENCE_RE.sub("", text)


def _extract_citations(text: str) -> list[tuple[str, str | None]]:
    """Return (path, anchor) pairs for every backtick-quoted path-shaped citation in `text`."""
    return [(m.group("path"), m.group("anchor")) for m in _CITATION_RE.finditer(text)]


def _resolve_citation(path: str, anchor: str | None) -> str | None:
    """Return an offense string if the citation does not resolve, else None."""
    target = (_REPO_ROOT / path).resolve()
    if not target.is_file():
        return f"{path}:{anchor or ''}: path does not resolve to a tracked file"
    if anchor is None:
        return None
    range_match = _NUMERIC_RANGE_RE.match(anchor)
    if anchor.isdigit() or range_match:
        end = int(range_match.group("end")) if range_match else int(anchor)
        line_count = len(target.read_text(encoding="utf-8").splitlines())
        if line_count < end:
            return (
                f"{path}:{anchor}: file has only {line_count} lines, "
                f"citation requires at least {end}"
            )
        return None
    # Name-shaped anchor: a test name, ::node-id suffix, frontmatter key, or constant/frozenset
    # name. Strip a leading `::` pytest-node-id separator before the verbatim substring check.
    needle = anchor.split("::")[-1]
    text = target.read_text(encoding="utf-8")
    if needle not in text:
        return f"{path}:{anchor}: anchor name {needle!r} not found verbatim in file"
    return None


def _tracked_scan_files() -> list[Path]:
    """Tracked files under `_SCAN_TARGETS` (git ls-files), matching CONTEXT.md's change-set scope."""
    completed = subprocess.run(
        ["git", "ls-files", *_SCAN_TARGETS],
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


def _scan_for_skill_creator(rel_path: str, text: str) -> list[tuple[int, str]]:
    """Return (lineno, line) hits where `text` contains the literal `skill-creator` string."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "skill-creator" in line:
            hits.append((lineno, line))
    return hits


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def test_citations_resolve_in_harness_author_skill() -> None:
    """Every `path:line`/anchor citation offered as a default in harness-author's body resolves in
    this checkout (Success Criterion 1)."""
    assert _HARNESS_AUTHOR_SKILL.is_file(), (
        f"missing Wave-1 deliverable: {_HARNESS_AUTHOR_SKILL.relative_to(_REPO_ROOT)} does not exist"
    )
    text = _strip_fences(_HARNESS_AUTHOR_SKILL.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for path, anchor in _extract_citations(text):
        offense = _resolve_citation(path, anchor)
        if offense is not None:
            offenders.append(offense)
    assert not offenders, (
        "harness-author SKILL.md offers citations that do not resolve in this checkout:\n"
        + "\n".join(offenders)
    )


def test_no_tracked_reference_to_skill_creator() -> None:
    """No tracked file outside .planning/ still names the absorbed `skill-creator` skill."""
    offenders: list[str] = []
    for path in _tracked_scan_files():
        text = _read_text(path)
        if text is None:
            continue
        rel = path.relative_to(_REPO_ROOT).as_posix()
        for lineno, line in _scan_for_skill_creator(rel, text):
            offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, (
        "dangling reference to absorbed skill-creator skill — must move to harness-author:\n"
        + "\n".join(offenders)
    )


def test_dangling_reference_scan_is_live() -> None:
    """Negative control: a synthetic line containing `skill-creator` IS flagged, proving the scan
    cannot silently no-op (T-50a-03)."""
    hits = _scan_for_skill_creator(
        "tools/fake_module.py", "# stale reference to skill-creator here"
    )
    assert hits, "negative control failed: scan did not flag a synthetic skill-creator reference"


def test_harness_author_reachability() -> None:
    """Everything skill-creator's content did stays reachable in harness-author's body
    (Success Criterion 3): the anti-sprawl question, the name regex, the dir-name-match rule, the
    description-cap-by-reference, the shared-caps-across-runtimes sentence, and the verify
    command."""
    assert _HARNESS_AUTHOR_SKILL.is_file(), (
        f"missing Wave-1 deliverable: {_HARNESS_AUTHOR_SKILL.relative_to(_REPO_ROOT)} does not exist"
    )
    text = _HARNESS_AUTHOR_SKILL.read_text(encoding="utf-8")
    lowered = text.lower()

    missing: list[str] = []

    if not (
        ("why can't this live in" in lowered) or ("why not" in lowered and "existing" in lowered)
    ):
        missing.append("anti-sprawl Step-0 question stem")

    if r"^[a-z0-9]+(-[a-z0-9]+)*$" not in text:
        missing.append("name regex string ^[a-z0-9]+(-[a-z0-9]+)*$")

    if "directory" not in lowered or "name" not in lowered:
        missing.append("directory-name-equals-frontmatter-name rule")

    if not ("caps.py" in text and "description" in lowered):
        missing.append("description-cap-by-reference (caps.py near a description mention)")

    if not ("opencode" in lowered and ("claude" in lowered)):
        missing.append("shared-caps-across-both-runtimes sentence naming opencode and Claude")

    if "uv run pytest tools/harness_lint/tests/test_skills.py -x -q" not in text:
        missing.append("verify command string")

    assert not missing, (
        "harness-author SKILL.md is missing reachable content from the absorbed skill-creator:\n"
        + "\n".join(missing)
    )
