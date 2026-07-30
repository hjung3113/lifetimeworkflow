"""Structural gate for `harness/skills/harness-author/SKILL.md` (Phase 50a, MONO-10/MONO-11).

Proves Success Criteria 1 and 3 of `.planning/phases/50a-harness-authoring/50a-01-PLAN.md`:

1. Every `path:line`/anchor citation the skill body offers as a default actually resolves in this
   checkout (`test_citations_resolve_in_harness_author_skill`) — closing the "plausible-but-dead
   citation" failure mode CONTEXT.md's citation-anchoring decision exists to prevent
   (`50a-CONTEXT.md:38-39`). A numeric-range citation whose trailing `` (`NAME`) `` parenthetical
   names a construct must also contain that construct within the cited lines, not merely have
   "enough" lines (`_resolve_citation`'s `name` parameter) — this closes the "citation points at
   the wrong part of the file" blind spot (REVIEW.md WR-03) that let two off-by-N citations ship
   green despite the file being long enough to pass a length-only check.
2. No tracked file outside `.planning/` still names the absorbed `skill-creator` skill
   (`test_no_tracked_reference_to_skill_creator`), backed by a negative control proving the scan
   cannot silently no-op (`test_dangling_reference_scan_is_live`) — the repo's "checks that cannot
   fail" defect class (T-50a-03). A single narrow, explicitly-commented exemption
   (`_HISTORY_EXEMPT_REFERENCE`, REVIEW.md WR-07) lets `caps.py`'s own history docstring narrate
   the retired skill by name without tripping this gate, without hiding any OTHER dangling
   reference — proven by `test_history_exemption_does_not_widen_to_other_skill_creator_lines`.
3. Everything `skill-creator` did stays reachable in the wider `harness-author` skill
   (`test_harness_author_reachability`) — via content checks that require same-line/same-sentence
   co-occurrence for keyword-pair rules (closing REVIEW.md WR-06's under-strict direction: scattered
   unrelated keyword occurrences must NOT satisfy a rule) while tolerating meaning-preserving
   rewording of exact-string rules (closing WR-06's over-strict direction).

Mirrors `test_core_no_example_dep.py`'s `git ls-files`-scoped scan idiom and single-assert-with-
joined-offenders pattern; NOT a copy — this module scans backtick-quoted inline citations inside a
single skill body, not whole-repo path tokens.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable
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

# A SINGLE, hard-coded (relative-path, 1-based-lineno) exemption for `caps.py`'s own EXPECTED_SKILLS
# history docstring (REVIEW.md WR-07): that comment narrates the retired `skill-creator` skill's
# absorption BY NAME — matching every other entry in the same history comment's established
# convention of literally naming the skill(s) it affects — and is historical prose, not a live
# pointer to the deleted skill. Scoped to exactly this one line so it can never shadow a genuine
# dangling reference anywhere else, including a different line of the SAME file; both halves of
# that claim are proven below by test_history_exemption_targets_the_documented_skill_creator_mention
# and test_history_exemption_does_not_widen_to_other_skill_creator_lines. Do not widen this to a
# whole-file or pattern-based skip — a second real dangling reference in caps.py must still fail.
_HISTORY_EXEMPT_REFERENCE: tuple[str, int] = ("tools/harness_lint/caps.py", 137)

_FENCE_RE = re.compile(r"```.*?```", re.DOTALL)

# A backtick-quoted inline citation shaped `<relative/path.ext>[:anchor]`, optionally followed by a
# backtick-quoted parenthetical construct name — `` `path:line` (`NAME`) `` — the path segment must
# contain a dot-extension so plain identifiers (e.g. `` `EXPECTED_SKILLS` ``) are not mistaken for
# a path citation; those are validated separately via the reachability test instead. The trailing
# name group lets a numeric-range citation be checked against the construct it claims to point at
# (REVIEW.md WR-03).
_CITATION_RE = re.compile(
    r"`(?P<path>[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)(?::(?P<anchor>[A-Za-z0-9_.:-]+))?`"
    r"(?:\s*\(`(?P<name>[A-Za-z0-9_]+)`\))?"
)

_NUMERIC_RANGE_RE = re.compile(r"^(?P<start>\d+)-(?P<end>\d+)$")


def _strip_fences(text: str) -> str:
    """Remove fenced ```-delimited code blocks — a citation inside an illustrative fence is an
    example, not a claim about this checkout (mirrors test_core_no_example_dep.py's pointer-line
    exemption idiom, applied to fenced spans instead of single lines)."""
    return _FENCE_RE.sub("", text)


def _extract_citations(text: str) -> list[tuple[str, str | None, str | None]]:
    """Return (path, anchor, trailing-parenthetical-name) triples for every backtick-quoted
    path-shaped citation in `text`."""
    return [
        (m.group("path"), m.group("anchor"), m.group("name")) for m in _CITATION_RE.finditer(text)
    ]


def _resolve_citation(path: str, anchor: str | None, name: str | None = None) -> str | None:
    """Return an offense string if the citation does not resolve, else None.

    `name`, when given, is the construct named in a citation's trailing `` (`NAME`) `` parenthetical
    (e.g. `` `caps.py:144-155` (`EXPECTED_SKILLS`) ``). For a numeric-range anchor, the cited lines
    must contain `name` verbatim — not merely exist in a long-enough file (REVIEW.md WR-03).
    """
    target = (_REPO_ROOT / path).resolve()
    if not target.is_file():
        return f"{path}:{anchor or ''}: path does not resolve to a tracked file"
    if anchor is None:
        return None
    range_match = _NUMERIC_RANGE_RE.match(anchor)
    if anchor.isdigit() or range_match:
        start = int(range_match.group("start")) if range_match else int(anchor)
        end = int(range_match.group("end")) if range_match else int(anchor)
        lines = target.read_text(encoding="utf-8").splitlines()
        if len(lines) < end:
            return (
                f"{path}:{anchor}: file has only {len(lines)} lines, "
                f"citation requires at least {end}"
            )
        if name is not None:
            window = "\n".join(lines[start - 1 : end])
            if name not in window:
                return (
                    f"{path}:{anchor}: named construct {name!r} not found within cited lines "
                    f"{start}-{end} (the range exists but points at the wrong part of the file)"
                )
        return None
    # Name-shaped anchor: a test name, ::node-id suffix, frontmatter key, or constant/frozenset
    # name. The real pytest node-id shape is `path.py::test_name` (a literal double colon
    # immediately after the path). `_CITATION_RE` consumes exactly the FIRST of those two colons as
    # the path/anchor separator, so the captured anchor for that shape is `:test_name` (single
    # leading colon retained). Strip exactly one leading colon before the `::`-split so both that
    # real shape AND the embedded shape (`path.py:Class::method`, no leading colon) resolve
    # correctly (REVIEW.md WR-05).
    normalized = anchor[1:] if anchor.startswith(":") else anchor
    needle = normalized.split("::")[-1]
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
    """Return (lineno, line) hits where `text` contains the literal `skill-creator` string,
    excluding the single narrow exemption in `_HISTORY_EXEMPT_REFERENCE` (REVIEW.md WR-07)."""
    hits: list[tuple[int, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        if "skill-creator" not in line:
            continue
        if (rel_path, lineno) == _HISTORY_EXEMPT_REFERENCE:
            continue
        hits.append((lineno, line))
    return hits


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def test_citations_resolve_in_harness_author_skill() -> None:
    """Every `path:line`/anchor citation offered as a default in harness-author's body resolves in
    this checkout, INCLUDING the constraint that a named numeric-range citation's range actually
    contains that construct (Success Criterion 1 + WR-03)."""
    assert _HARNESS_AUTHOR_SKILL.is_file(), (
        f"missing Wave-1 deliverable: {_HARNESS_AUTHOR_SKILL.relative_to(_REPO_ROOT)} "
        "does not exist"
    )
    text = _strip_fences(_HARNESS_AUTHOR_SKILL.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for path, anchor, name in _extract_citations(text):
        offense = _resolve_citation(path, anchor, name=name)
        if offense is not None:
            offenders.append(offense)
    assert not offenders, (
        "harness-author SKILL.md offers citations that do not resolve in this checkout:\n"
        + "\n".join(offenders)
    )


def test_verify_command_citations_are_seen_by_citation_gate() -> None:
    """REVIEW.md WR-04 regression: the Step-3 verify-command test-module paths must be extractable
    as citations by `_CITATION_RE` (previously they carried trailing CLI flags inside the SAME
    backtick span — `` `test_skills.py -x -q` `` — so the path-char class excluded the space and
    the whole citation never matched, silently bypassing
    `test_citations_resolve_in_harness_author_skill` for all three verify-command paths)."""
    # The broken shape must still fail to match — proves the regex genuinely excludes it rather
    # than this test being vacuous.
    broken = "`tools/harness_lint/tests/test_skills.py -x -q`"
    assert _extract_citations(broken) == [], (
        "a path+flags citation packed into one backtick span unexpectedly matched — this test's "
        "premise (the WR-04 failure mode) no longer holds, update it"
    )
    text = _strip_fences(_HARNESS_AUTHOR_SKILL.read_text(encoding="utf-8"))
    cited_paths = {path for path, _, _ in _extract_citations(text)}
    for expected in (
        "tools/harness_lint/tests/test_skills.py",
        "tools/harness_lint/tests/test_commands.py",
        "tools/harness_lint/tests/test_agents.py",
    ):
        assert expected in cited_paths, (
            f"{expected} is not seen as a citation by the gate — the WR-04 blind spot has returned"
        )


def test_pytest_node_id_citation_resolves_end_to_end() -> None:
    """REVIEW.md WR-05 regression: the real pytest node-id shape `path.py::test_name` must resolve.
    Exercised end-to-end (regex extraction + resolution) against the actual citation the skill body
    now carries, so the path is proven live rather than latent."""
    text = "`tools/harness_lint/tests/test_agents.py::test_expected_personas_present_no_sprawl`"
    citations = _extract_citations(text)
    assert len(citations) == 1, f"expected exactly one citation, got {citations}"
    path, anchor, name = citations[0]
    assert anchor == ":test_expected_personas_present_no_sprawl", (
        f"unexpected captured anchor shape: {anchor!r} — _CITATION_RE's separator consumption "
        "assumption in the doc-comment above may have changed"
    )
    offense = _resolve_citation(path, anchor, name=name)
    assert offense is None, f"pytest node-id citation should resolve, got: {offense}"

    body = _strip_fences(_HARNESS_AUTHOR_SKILL.read_text(encoding="utf-8"))
    assert "test_agents.py::test_expected_personas_present_no_sprawl" in body, (
        "the skill body no longer carries a `::`-shaped pytest node-id citation — WR-05's "
        "real-shape exercise has gone latent again"
    )


def test_numeric_range_citation_validates_named_anchor_location() -> None:
    """REVIEW.md WR-03 regression: a numeric-range citation whose named construct does NOT
    actually start/end within the cited range must be rejected — even though the file has more
    than enough lines to pass a length-only check. This is exactly the blind spot that let the
    confirmed WR-01 drift ship green: a length-only check cannot distinguish "cites the wrong part
    of the file" from "cites the right part". `100-115` is a real, in-bounds range of
    `caps.py` — but it covers the read-only-invariant helper and the skill-name caps, not
    `EXPECTED_SKILLS` (which lives at `144-155`)."""
    offense = _resolve_citation("tools/harness_lint/caps.py", "100-115", name="EXPECTED_SKILLS")
    assert offense is not None, (
        "citation for a real, in-bounds range that does NOT contain EXPECTED_SKILLS was wrongly "
        "accepted — the strengthened WR-03 gate did not catch it"
    )
    assert (
        _resolve_citation("tools/harness_lint/caps.py", "144-155", name="EXPECTED_SKILLS") is None
    ), "the CORRECT current range for EXPECTED_SKILLS was rejected — check for line drift"


def test_no_tracked_reference_to_skill_creator() -> None:
    """No tracked file outside .planning/ still names the absorbed `skill-creator` skill, apart
    from the single narrow, documented exemption (REVIEW.md WR-07)."""
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


def test_history_exemption_targets_the_documented_skill_creator_mention() -> None:
    """REVIEW.md WR-07 regression: the exemption's hard-coded (path, lineno) must point at a line
    that actually contains `skill-creator` right now. If `caps.py`'s history comment moves or is
    reworded, this test catches the stale exemption before it can silently exempt the wrong line
    (or a line that no longer needs exempting at all)."""
    path, lineno = _HISTORY_EXEMPT_REFERENCE
    text = (_REPO_ROOT / path).read_text(encoding="utf-8")
    lines = text.splitlines()
    assert 1 <= lineno <= len(lines), f"{path}: exemption line {lineno} is out of range"
    assert "skill-creator" in lines[lineno - 1], (
        f"{path}:{lineno}: exemption no longer points at a line containing 'skill-creator' — "
        "update _HISTORY_EXEMPT_REFERENCE, or the exemption is now stale"
    )


def test_history_exemption_does_not_widen_to_other_skill_creator_lines() -> None:
    """REVIEW.md WR-07 regression: the exemption is scoped to EXACTLY one line. A second,
    unrelated `skill-creator` mention in the SAME file at a DIFFERENT line must still be flagged —
    proving the exemption cannot be (ab)used to hide a genuine dangling reference."""
    exempt_path, exempt_lineno = _HISTORY_EXEMPT_REFERENCE
    synthetic = "\n".join(
        ["placeholder"] * (exempt_lineno - 1)
        + ["# skill-creator (the documented, exempted history mention)"]
        + ["# a totally separate, un-exempted skill-creator reference"]
    )
    hits = _scan_for_skill_creator(exempt_path, synthetic)
    hit_linenos = {lineno for lineno, _ in hits}
    assert exempt_lineno not in hit_linenos, "the documented exemption line was still flagged"
    assert (exempt_lineno + 1) in hit_linenos, (
        "a second, unrelated skill-creator reference on a different line was wrongly exempted — "
        "the exemption has widened beyond its single hard-coded line"
    )


# ---- reachability content checks (REVIEW.md WR-06) -------------------------------------------
#
# Each check below targets ONE specific failure mode: a future edit that silently DROPS one of
# skill-creator's six carried-forward guarantees while leaving unrelated, scattered occurrences of
# the check's individual keywords elsewhere in the body (the under-strict direction WR-06 found:
# "directory" and "name" each occur several times outside the actual rule sentence, so an
# anywhere-in-document keyword-pair check could not tell real content loss from noise). Each check
# is ALSO tolerant of a meaning-preserving rewording — different flag order, an equivalent regex
# written with different anchors, a line-wrap — so it does not fail on harmless edits (the
# over-strict direction WR-06 found in the prior byte-exact checks).


def _lines_lower(text: str) -> list[str]:
    return [ln.lower() for ln in text.splitlines()]


def _has_anti_sprawl_stem(text: str) -> bool:
    """Targets: loss of the Step-0 anti-sprawl question itself."""
    lowered = text.lower()
    return ("why can't this live in" in lowered) or ("why not" in lowered and "existing" in lowered)


def _has_name_regex_semantics(text: str) -> bool:
    """Targets: loss of the name-shape rule (lowercase alnum segments joined by single hyphens).
    Matches the regex's CHARACTER-CLASS semantics rather than one frozen literal, so `^...$` and
    `\\A...\\Z` anchor variants both satisfy it."""
    return "[a-z0-9]" in text and "-[a-z0-9]" in text


def _has_dir_name_rule(text: str) -> bool:
    """Targets: loss of "directory name equals frontmatter name" — the actual rule sentence, not
    scattered unrelated occurrences of "directory" and "name" elsewhere in the body."""
    return "directory name equals the frontmatter" in text.lower()


def _has_description_cap_reference(text: str) -> bool:
    """Targets: loss of the description-is-capped-by-caps.py pointer — requires `caps.py` and
    `description` to co-occur on the SAME line, not merely appear anywhere in the document."""
    return any("caps.py" in ln and "description" in ln for ln in _lines_lower(text))


def _has_shared_caps_sentence(text: str) -> bool:
    """Targets: loss of the "same caps for both runtimes" sentence — requires `opencode` and
    `claude` to co-occur on the SAME line."""
    return any("opencode" in ln and "claude" in ln for ln in _lines_lower(text))


def _has_verify_command(text: str) -> bool:
    """Targets: loss of the runnable skill-verify command — requires `test_skills.py` and `-x -q`
    to co-occur on the SAME line, tolerant of surrounding wording/wrapping changes (e.g. quoting
    the path separately from the flags, per the WR-04 fix)."""
    return any("test_skills.py" in ln and "-x -q" in ln for ln in _lines_lower(text))


_REACHABILITY_CHECKS: dict[str, Callable[[str], bool]] = {
    "anti-sprawl Step-0 question stem": _has_anti_sprawl_stem,
    "name-regex semantics (lowercase-alnum segments joined by single hyphens)": (
        _has_name_regex_semantics
    ),
    "directory-name-equals-frontmatter-name rule": _has_dir_name_rule,
    "description-cap-by-reference (caps.py and description co-occurring on one line)": (
        _has_description_cap_reference
    ),
    "shared-caps-across-both-runtimes sentence (opencode and Claude co-occurring on one line)": (
        _has_shared_caps_sentence
    ),
    "verify command (test_skills.py and -x -q co-occurring on one line)": _has_verify_command,
}


def test_harness_author_reachability() -> None:
    """Everything skill-creator's content did stays reachable in harness-author's body (Success
    Criterion 3): the anti-sprawl question, the name regex, the dir-name-match rule, the
    description-cap-by-reference, the shared-caps-across-runtimes sentence, and the verify command.

    This test is designed to catch REAL content loss (a rule sentence deleted while leaving
    unrelated scattered occurrences of its keywords behind) while NOT breaking on a
    meaning-preserving rewording of the surviving content — see the module-level comment above
    `_lines_lower` for the full rationale (REVIEW.md WR-06)."""
    assert _HARNESS_AUTHOR_SKILL.is_file(), (
        f"missing Wave-1 deliverable: {_HARNESS_AUTHOR_SKILL.relative_to(_REPO_ROOT)} "
        "does not exist"
    )
    text = _HARNESS_AUTHOR_SKILL.read_text(encoding="utf-8")

    missing = [desc for desc, check in _REACHABILITY_CHECKS.items() if not check(text)]

    assert not missing, (
        "harness-author SKILL.md is missing reachable content from the absorbed skill-creator:\n"
        + "\n".join(missing)
    )


def test_dir_name_rule_check_rejects_scattered_unrelated_keywords() -> None:
    """WR-06 regression (under-strict direction): 'directory' and 'name' occurring in unrelated
    sentences elsewhere in a document must NOT satisfy the check — only the actual rule phrase
    does. This is the exact gap WR-06 found (both words already occur several times outside the
    rule sentence in the real skill body)."""
    scattered = (
        "Before creating anything, answer out loud. Adding a directory is a bigger decision than "
        "renaming a file. The name of a good skill is memorable."
    )
    assert not _has_dir_name_rule(scattered), (
        "scattered unrelated 'directory'/'name' occurrences wrongly satisfied the check"
    )
    assert _has_dir_name_rule("the directory name equals the frontmatter `name`.")


def test_description_cap_reference_check_requires_same_line_cooccurrence() -> None:
    """WR-06 regression (under-strict direction): `caps.py` and `description` appearing on
    DIFFERENT lines must not satisfy the check."""
    scattered = "See tools/harness_lint/caps.py for every cap.\nEvery description needs a trigger."
    assert not _has_description_cap_reference(scattered)
    assert _has_description_cap_reference("capped by `caps.py:_DESC_MAX`, the description must...")


def test_shared_caps_sentence_check_requires_same_line_cooccurrence() -> None:
    """WR-06 regression (under-strict direction): `opencode` and `claude` appearing on DIFFERENT
    lines must not satisfy the check."""
    scattered = "This works the same in opencode.\nClaude has its own tools list too."
    assert not _has_shared_caps_sentence(scattered)
    assert _has_shared_caps_sentence("caps apply to both opencode and Claude runtimes.")


def test_name_regex_semantics_check_tolerates_anchor_rewording() -> None:
    """WR-06 regression (over-strict direction): a semantically equivalent regex written with
    `\\A`/`\\Z` anchors instead of `^`/`$` must still satisfy the check."""
    reworded = r"the name regex is \A[a-z0-9]+(-[a-z0-9]+)*\Z"
    assert _has_name_regex_semantics(reworded)


def test_verify_command_check_tolerates_flag_and_wrapping_rewording() -> None:
    """WR-06 regression (over-strict direction): quoting the path separately from its flags (the
    WR-04 fix's own shape) must still satisfy the check — the exact prior literal
    `uv run pytest tools/harness_lint/tests/test_skills.py -x -q` is not required verbatim."""
    reworded = (
        "Run `uv run pytest` against `tools/harness_lint/tests/test_skills.py` using `-x -q`."
    )
    assert _has_verify_command(reworded)
