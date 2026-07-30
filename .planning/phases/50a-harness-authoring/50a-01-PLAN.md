---
phase: 50a-harness-authoring
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tools/harness_lint/tests/test_harness_author.py
  - harness/skills/harness-author/SKILL.md
  - harness/skills/skill-creator/SKILL.md
  - tools/harness_lint/caps.py
  - harness/skills/brownfield-adoption/SKILL.md
  - tools/harness_emit/emit-manifest.json
  - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
  - .opencode/skill/harness-author/SKILL.md
  - .opencode/skill/skill-creator/SKILL.md
  - .claude/skills/harness-author/SKILL.md
  - .claude/skills/skill-creator/SKILL.md
  - AGENTS.md
autonomous: true
requirements: [MONO-10, MONO-11]

must_haves:
  truths:
    - "Opening harness/skills/harness-author/SKILL.md shows a Step-0 anti-sprawl question generalized to all three emitter-projected kinds (skills, commands, agents), not skills alone."
    - "Every path:line / anchor citation the skill body offers as a default resolves to a real location in this checkout, proven by an automated test that can fail."
    - "harness/skills/skill-creator/ no longer exists in the tracked tree, and no tracked file outside .planning/ mentions skill-creator afterward."
    - "caps.py's EXPECTED_SKILLS, test_skills.py::test_expected_skills_present_no_sprawl, and test_emit_determinism.py::test_emitted_skill_set_matches_expected all agree on the same 8-name frozenset containing harness-author, not skill-creator."
    - "python -m tools.harness_emit run twice in a row produces byte-identical .opencode/ and .claude/ trees, and skill-creator is absent from both while harness-author is present in both."
    - "The live command count stays 19 and no new tools/*/pyproject.toml or contracts/*.schema.json file exists after this phase."
  artifacts:
    - path: "harness/skills/harness-author/SKILL.md"
      provides: "the absorbed, widened (skills+commands+agents) meta-authoring skill with grounded path:line defaults"
    - path: "tools/harness_lint/tests/test_harness_author.py"
      provides: "citation-integrity, dangling-reference, and reachability proofs (Success Criteria 1 and 3)"
    - path: "tools/harness_lint/caps.py"
      provides: "EXPECTED_SKILLS pinned to the new 8-name set (harness-author, not skill-creator)"
    - path: "tools/harness_emit/emit-manifest.json"
      provides: "regenerated ownership manifest listing harness-author's emitted paths, no skill-creator entries"
  key_links:
    - from: "harness/skills/harness-author/SKILL.md"
      to: "tools/harness_lint/caps.py"
      via: "a path:line citation pointing at caps.py's cap constants/EXPECTED_SKILLS as authority, never restating a number"
      pattern: "caps\\.py:\\d"
    - from: "tools/harness_lint/caps.py::EXPECTED_SKILLS"
      to: "tools/harness_emit/tests/test_emit_determinism.py::test_emitted_skill_set_matches_expected"
      via: "shared frozenset import (tools.harness_lint.caps.EXPECTED_SKILLS)"
      pattern: "from tools.harness_lint.caps import.*EXPECTED_SKILLS"
    - from: "harness/skills/harness-author/SKILL.md"
      to: ".opencode/skill/harness-author/SKILL.md + .claude/skills/harness-author/SKILL.md"
      via: "tools.harness_emit.generate.emit() -> iter_skills -> render_markdown"
      pattern: "iter_skills\\(harness_dir"
---

<objective>
Absorb `harness/skills/skill-creator/` into a new, wider `harness/skills/harness-author/` skill that
covers all three emitter-projected artifact kinds (skills, commands, agents) instead of skills alone,
with every offered default cited as a `path:line`/stable-name anchor that a new automated test proves
resolves in this checkout (MONO-10). The rename/absorption lands as ONE change — directory
create+delete, the three-way `EXPECTED_SKILLS` pin, the `brownfield-adoption` cross-reference, and a
full re-emit — so the skill count is 8 before and 8 after, with zero new packages, commands, or
contracts (MONO-11).

Purpose: authoring a harness artifact stops being tribal knowledge — grounded, checkable defaults
replace recalled convention, and `harness/` stays the sole hand-edited source (`.opencode/`/`.claude/`
change only through re-emit).

Output: `harness/skills/harness-author/SKILL.md` (new), `harness/skills/skill-creator/` (deleted),
`tools/harness_lint/tests/test_harness_author.py` (new), updated `caps.py`/`brownfield-adoption/
SKILL.md`, a regenerated `emit-manifest.json` + `.ambr` snapshot + both emitted trees + `AGENTS.md`'s
managed block.
</objective>

<execution_context>
@/home/user/lifetimeworkflow/.claude/get-shit-done/workflows/execute-plan.md
@/home/user/lifetimeworkflow/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/phases/50a-harness-authoring/50a-CONTEXT.md
@.planning/phases/50a-harness-authoring/50a-RESEARCH.md
@AGENTS.md
</context>

<interfaces>
<!-- Skill/command/agent shape rules the new skill body must cite by path:line, and the discovery/
projection functions that make the "output lands under harness/ only" claim provable. Extracted so
no codebase exploration is needed to write harness-author/SKILL.md or the new test module. -->

From `tools/harness_lint/caps.py` (skill caps, lines 106-150; agent caps, lines 22-67):
```python
_NAME_MAX = 64
_DESC_MAX = 1024
_BODY_WARN_LINES = 500
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
_RESERVED_WORDS = ("anthropic", "claude")
_XML_CHARS = ("<", ">")
EXPECTED_SKILLS = frozenset({...8 names..., "skill-creator", ...})   # line 143 has the literal to swap
VALID_PERMISSION_KEYS = frozenset({...15 keys...})
EXPECTED_PERSONAS = frozenset({"orchestrator", "python-engineer", "code-reviewer", "explorer", "curator"})
READ_ONLY_PERSONAS = frozenset({"code-reviewer", "explorer"})
PLACEHOLDER_MODEL = "provider/explorer-tier"
```

From `tools/harness_lint/tests/test_commands.py` (command shape, lines 39-74):
```python
_AGENT_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
EXPECTED_COMMAND_NAMES = frozenset({...19 names including "impact"...})
def test_command_count_is_stable() -> None: assert len(_command_files()) == 19
```

From `tools/harness_emit/generate.py` (discovery + emit spine):
```python
def iter_skills(skills_dir) -> list[tuple[str, dict, str, Path]]: ...   # globs skills/*/SKILL.md
def iter_commands(commands_dir) -> list[tuple[str, dict, str]]: ...
def iter_agents(agents_dir) -> list[tuple[str, dict, str]]: ...
def emit(harness_dir=HARNESS_DIR, opencode_dir=OPENCODE_DIR, claude_dir=CLAUDE_DIR,
         manifest_path=MANIFEST_PATH, root=REPO_ROOT) -> list[Path]: ...
# emit() calls validate.check_skill_set({name for name,... in skills}) at line 362 BEFORE any write —
# a partial rename (dir renamed, caps.py not yet edited, or vice versa) raises HarnessEmitError.
```

From `tools/harness_lint/tests/test_core_no_example_dep.py` (the `git ls-files`-scoped scan idiom to
mirror for the new citation/dangling-reference tests, lines 88-106, 140-154):
```python
def _tracked_core_files() -> list[Path]:
    completed = subprocess.run(["git", "ls-files", *_CORE_ROOTS], cwd=_REPO_ROOT,
                                capture_output=True, text=True, check=True)
    ...
def test_core_has_no_example_dependency() -> None:
    offenders = []
    for path in _tracked_core_files():
        text = _read_text(path)
        for lineno, line in _scan_lines(rel, text):
            offenders.append(f"{rel}:{lineno}: {line.strip()}")
    assert not offenders, ...
```
</interfaces>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Write the new structural gate module (RED — harness-author does not exist yet)</name>
  <files>tools/harness_lint/tests/test_harness_author.py</files>
  <read_first>
    - tools/harness_lint/caps.py (whole file — EXPECTED_SKILLS, cap constants)
    - tools/harness_lint/tests/test_core_no_example_dep.py (whole file — the `git ls-files`-scoped
      scan idiom to mirror; the negative-control-test pattern)
    - tools/harness_lint/tests/test_skills.py (whole file — parse_frontmatter usage, `_skill_files()`
      idiom)
    - harness/skills/skill-creator/SKILL.md (whole file — the load-bearing content that must remain
      reachable: the Step-0 question text, the name-regex string, the dir-name-match rule, the
      description-caps rule, the "SAME caps apply to both...runtimes" sentence, the verify command
      `uv run pytest tools/harness_lint/tests/test_skills.py -x -q`)
    - .planning/phases/50a-harness-authoring/50a-CONTEXT.md (lines 36-54 — citation-format decision:
      anchor on stable names, not bare line numbers, though a `path:line`/`path:line-range` form is
      also sanctioned per RESEARCH.md's own citation style)
    - .planning/phases/50a-harness-authoring/50a-RESEARCH.md (lines 345-373 — "Closest prior art for
      citation-integrity checking", the recommended regex/anchor-resolution shape and the fenced-code
      exemption)
  </read_first>
  <behavior>
    - `test_citations_resolve_in_harness_author_skill`: read
      `harness/skills/harness-author/SKILL.md`'s body (skip if file absent -> the test must FAIL, not
      skip, since the skill is a Wave-1 deliverable — use a plain assertion on `Path.is_file()` first
      so the failure message names the missing skill, not an import/collection error). Strip fenced
      ```-delimited code blocks before scanning. Extract every backtick-quoted citation shaped
      `` `<relative-path-with-a-dot-extension>[:anchor]` `` via regex (mirror
      `test_core_no_example_dep.py`'s `_scan_lines` line-based idiom, but operate on inline-code spans
      instead of raw tokens). For each citation: (a) assert the path resolves to a tracked file under
      repo root (`Path(_REPO_ROOT / path).is_file()`); (b) if the anchor is numeric or a
      `start-end` numeric range, assert the file has at least that many lines; (c) if the anchor is a
      name (e.g. a `test_*` function, a `::test_name` pytest node-id suffix, a frozenset/constant
      name, a frontmatter key), assert that name string is present verbatim in the file's text. On any
      failure, collect ALL offending citations and fail once with the full list (mirror
      `test_core_no_example_dep.py`'s single-assert-with-joined-offenders pattern) — never a first-hit
      `assert`.
    - `test_no_tracked_reference_to_skill_creator`: reuse the `git ls-files`-scoped scan idiom
      (`_tracked_core_files`-equivalent) scoped to exactly `AGENTS.md`, `CLAUDE.md`, `harness/`,
      `tools/`, `.opencode/`, `.claude/` (explicitly excluding `.planning/`, per RESEARCH.md Pitfall 2
      / Assumption A2). Assert no line in any of those tracked files contains the literal string
      `skill-creator`.
    - `test_dangling_reference_scan_is_live`: a negative control (mirror
      `test_negative_control_flags_synthetic_example_ref`) — feed the scan helper a synthetic line
      containing `skill-creator` and assert it IS flagged, proving the scan cannot silently no-op.
    - `test_harness_author_reachability`: assert `harness/skills/harness-author/SKILL.md`'s full text
      (frontmatter + body) contains, verbatim or near-verbatim as substrings, each of: the anti-sprawl
      question stem (`"why can't this live in"` or `"why not"` + `"existing"`, case-insensitive), the
      name regex string `^[a-z0-9]+(-[a-z0-9]+)*$`, the phrase confirming the directory-name-equals-
      frontmatter-name rule, a mention of the description length cap by reference (not restated
      number — assert the string `caps.py` appears near a `description` mention), the shared-caps
      sentence content (both runtimes share identical caps — assert a substring naming both `opencode`
      and `claude`/`Claude`), and the verify command string
      `uv run pytest tools/harness_lint/tests/test_skills.py -x -q`.
  </behavior>
  <action>
    Create `tools/harness_lint/tests/test_harness_author.py` implementing the four test functions in
    `<behavior>` above, module-level `_REPO_ROOT`/`_HARNESS_AUTHOR_SKILL` constants following the
    `parents[3]` idiom used by every sibling module in this directory, and a docstring naming which
    Success Criteria (1 and 3) and which CONTEXT.md decision (citation anchoring, `50a-CONTEXT.md:38-
    39`) this module proves. At this point `harness/skills/harness-author/SKILL.md` does not exist, so
    `test_citations_resolve_in_harness_author_skill`, `test_no_tracked_reference_to_skill_creator`
    (skill-creator is still present in the tree), and `test_harness_author_reachability` are all
    EXPECTED to fail; `test_dangling_reference_scan_is_live` is expected to pass immediately (it is a
    self-contained negative control, not conditioned on harness-author existing). Do not write
    `harness/skills/harness-author/SKILL.md` in this task.
  </action>
  <acceptance_criteria>
    - `uv run pytest tools/harness_lint/tests/test_harness_author.py -q` collects exactly 4 tests with
      zero collection errors.
    - `test_dangling_reference_scan_is_live` PASSES.
    - `test_citations_resolve_in_harness_author_skill`, `test_no_tracked_reference_to_skill_creator`,
      and `test_harness_author_reachability` FAIL with an assertion message that names the missing
      file / the still-present `skill-creator` reference — not an unrelated `ImportError` or
      `AttributeError`.
  </acceptance_criteria>
  <verify>
    <automated>uv run pytest tools/harness_lint/tests/test_harness_author.py -q</automated>
  </verify>
  <done>The new gate module exists, is collectible, and is RED on exactly the three tests whose
  precondition (harness-author authored, skill-creator gone) is not yet satisfied.</done>
</task>

<task type="auto">
  <name>Task 2: Author harness-author and absorb skill-creator (the one atomic change)</name>
  <files>harness/skills/harness-author/SKILL.md, harness/skills/skill-creator/SKILL.md, tools/harness_lint/caps.py, harness/skills/brownfield-adoption/SKILL.md</files>
  <read_first>
    - harness/skills/skill-creator/SKILL.md (whole file, 46 lines — the source being absorbed
      verbatim in substance, widened in scope)
    - harness/skills/context-budget/SKILL.md (whole file — a concise, `references/`-free full-body
      shape to mirror: 16-line frontmatter + focused body + a "Related" footer)
    - harness/skills/brownfield-adoption/SKILL.md (whole file, especially lines 14-21 — the two
      `skill-creator` mentions to edit: the sibling-skill enumeration and the closing
      "(skill-creator Step 0)" citation)
    - harness/commands/component.md:1-9 (command frontmatter shape example to cite)
    - harness/agents/curator.md:1-17 (agent frontmatter shape example to cite: `mode`, `permission`,
      `tools`)
    - tools/harness_lint/caps.py:106-150 (skill caps block + `EXPECTED_SKILLS` docstring lines 122-
      138 — the self-narrating history comment to append one line to, per RESEARCH.md Open Question 2)
    - tools/harness_lint/tests/test_agent_referential_integrity.py:1-20 (cite as the command-side
      cross-file check, for the "Step 3: verify" section's command-kind row)
    - tools/harness_lint/tests/test_harness_author.py (just written — the target the new skill body
      must satisfy)
  </read_first>
  <action>
    Create `harness/skills/harness-author/SKILL.md` with frontmatter `name: harness-author` and a
    verb-first `description` (routing trigger token "Use when…", disjoint from every sibling
    description, no reserved word/XML char) stating it covers skills+commands+agents authoring and
    absorbs skill-creator. Body structure, generalizing skill-creator's two-step shape to three kinds:
    (1) a "Step 0 (mandatory)" section restating skill-creator's anti-sprawl question generalized to
    "skill, command, OR agent" — enumerate the current sibling sets by citing `caps.py`'s
    `EXPECTED_SKILLS` (`caps.py:139-150`) and `test_commands.py`'s `EXPECTED_COMMAND_NAMES`
    (`test_commands.py:52-74`) rather than hardcoding the name lists inline (so the citation, not a
    restated list, is what could go stale-detectably); (2) a "Step 1: choose the kind and its shape"
    section with three subsections (skill/command/agent), each citing the exact caps/regex source by
    `path:line` or `path::test_name` from the Interfaces block above — NEVER restating a cap NUMBER
    (no literal `64`/`1024`/`500` in the body; point at `_NAME_MAX`/`_DESC_MAX`/`_BODY_WARN_LINES` by
    name+location instead) but DO reproduce the name-regex string verbatim (it is a shape, not a cap
    number) and state the shared-both-runtimes-caps fact in prose; (3) a "Step 2: author the source"
    section pointing at `harness/skills/`, `harness/commands/`, `harness/agents/` with one real
    existing-file citation each (`harness/commands/component.md:1-9`, `harness/agents/curator.md:1-
    17`, `harness/skills/context-budget/SKILL.md:1-16`); (4) a "Step 3: verify" section naming the
    exact runnable commands per kind (`uv run pytest tools/harness_lint/tests/test_skills.py -x -q`
    for skills, `tools/harness_lint/tests/test_commands.py -x -q` for commands plus
    `test_agent_referential_integrity.py` for the cross-file `agent:` resolution,
    `tools/harness_lint/tests/test_agents.py -x -q` for agents) followed by the emit round-trip
    (`python -m tools.harness_emit && git diff --exit-code -- .opencode .claude opencode.json
    AGENTS.md CLAUDE.md tools/harness_emit/emit-manifest.json`); (5) an explicit "Out of scope" line
    naming plugins and hooks (no single-file source shape today); (6) a "Related" footer citing
    `harness/skills/brownfield-adoption/SKILL.md` (sibling anti-sprawl example) and
    `tools/harness_lint/caps.py` (single source of truth). Keep the body well under the ~500-line warn
    threshold. Then, as the SAME change: delete `harness/skills/skill-creator/` entirely; in
    `tools/harness_lint/caps.py` swap the `"skill-creator"` string inside `EXPECTED_SKILLS`
    (`caps.py:143`) for `"harness-author"`, and append one line to the docstring above
    `EXPECTED_SKILLS` (`caps.py:122-138`) continuing its existing phase-by-phase narration convention,
    naming Phase 50a's absorption; in `harness/skills/brownfield-adoption/SKILL.md`, replace the
    `skill-creator` token in the sibling-skill enumeration (line 15) with `harness-author`, and replace
    the closing citation `(skill-creator Step 0)` (line 21) with `(harness-author Step 0)`. Per
    CONTEXT.md's "one change" decision, do not commit or leave any of these four file changes partial
    relative to each other.
  </action>
  <acceptance_criteria>
    - `harness/skills/skill-creator/` no longer exists on disk (`test -d harness/skills/skill-creator`
      exits non-zero).
    - `harness/skills/harness-author/SKILL.md` exists with a `name: harness-author` frontmatter key
      equal to its parent directory name.
    - `grep -c 'skill-creator' harness/skills/brownfield-adoption/SKILL.md` returns `0`.
    - `grep -c '"skill-creator"' tools/harness_lint/caps.py` returns `0` and
      `grep -c '"harness-author"' tools/harness_lint/caps.py` returns `1`.
  </acceptance_criteria>
  <verify>
    <automated>uv run pytest tools/harness_lint/tests/test_harness_author.py tools/harness_lint/tests/test_skills.py -q</automated>
  </verify>
  <done>All four tests in test_harness_author.py pass; test_skills.py::test_expected_skills_present_no_sprawl
  passes with the new 8-name set (harness-author replacing skill-creator).</done>
</task>

<task type="auto">
  <name>Task 3: Regenerate the derived plane, prove idempotency and zero-growth, commit</name>
  <files>tools/harness_emit/emit-manifest.json, tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr, .opencode/skill/harness-author/SKILL.md, .opencode/skill/skill-creator/SKILL.md, .claude/skills/harness-author/SKILL.md, .claude/skills/skill-creator/SKILL.md, AGENTS.md</files>
  <read_first>
    - tools/harness_emit/generate.py:320-458 (the `emit()` spine — validate-then-write,
      `manifest.prune_then_write` call at the end, `_merge_shared_markdown` for `AGENTS.md`)
    - tools/harness_emit/manifest.py (whole file — `prune_then_write` deletes prior-owned paths
      absent from the current emit, so the two `skill-creator` emitted-copy entries self-prune)
    - tools/harness_emit/tests/test_emit_determinism.py (whole file — `test_emitted_skill_set_matches_expected`,
      `test_projected_tree_matches_committed_snapshot`, the `--snapshot-update` regeneration step)
    - tools/harness_lint/tests/test_commands.py:93-101 (`test_command_count_is_stable` — pinned at 19,
      must not move)
    - AGENTS.md:101-110 (the HARNESS-MANAGED block that must list `harness-author`, not
      `skill-creator`, after re-emit — regenerated automatically, never hand-edited)
  </read_first>
  <action>
    Run `python -m tools.harness_emit` from repo root. This regenerates: both emitted skill copies
    (`.opencode/skill/harness-author/SKILL.md` + `.claude/skills/harness-author/SKILL.md` created;
    the two `skill-creator` emitted copies pruned by `manifest.prune_then_write` since they are no
    longer in the current emit set — do NOT `git rm` them by hand), `tools/harness_emit/emit-manifest.json`
    (the two `skill-creator` entries replaced with `harness-author` entries), and `AGENTS.md`'s
    HARNESS-MANAGED skills line. Then run
    `uv run pytest tools/harness_emit/tests/test_emit_determinism.py --snapshot-update` to regenerate
    `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr` (the 5 lines that embedded
    `skill-creator`), and inspect the diff to confirm only `skill-creator`->`harness-author` name
    changes are present (no unrelated content drift). Re-run `python -m tools.harness_emit` a second
    time into the SAME target trees and confirm `git status` shows no further changes (idempotency —
    MONO-10 criterion 2's "emit round-trip is byte-clean"). Run the full test suite
    (`uv run pytest -q`) and confirm zero failures. Confirm zero-growth: `git ls-files harness/skills/*/SKILL.md
    | wc -l` equals 8; `uv run pytest tools/harness_lint/tests/test_commands.py -q` still passes with
    the pinned count of 19; `git status --porcelain -- 'tools/*/pyproject.toml' 'contracts/'` shows no
    new package or contract files. Stage every file in this plan's `files_modified` plus Task 1/2's
    files (the new test module, the new skill, the deleted skill-creator directory, `caps.py`,
    `brownfield-adoption/SKILL.md`) and create ONE commit covering the entire absorption — per
    CONTEXT.md's "one change" decision, this must not be split across multiple commits.
  </action>
  <acceptance_criteria>
    - `python -m tools.harness_emit` exits 0 and, run a second consecutive time, produces no further
      `git diff` in `.opencode/`, `.claude/`, `opencode.json`, `AGENTS.md`, `CLAUDE.md`, or
      `tools/harness_emit/emit-manifest.json`.
    - `find .opencode .claude -iname '*skill-creator*'` returns no results; `find .opencode .claude
      -iname '*harness-author*'` returns exactly 2 `SKILL.md` paths.
    - `uv run pytest -q` reports zero failures.
    - `git ls-files harness/skills/*/SKILL.md | wc -l` reports `8`.
  </acceptance_criteria>
  <verify>
    <automated>python -m tools.harness_emit && git diff --exit-code -- .opencode .claude opencode.json AGENTS.md CLAUDE.md tools/harness_emit/emit-manifest.json && uv run pytest -q</automated>
  </verify>
  <done>Both runtime trees carry harness-author and no longer carry skill-creator; emit-manifest.json
  and the .ambr snapshot are regenerated and idempotent; the full suite is green; skills==8,
  commands==19, no new packages/contracts; the whole absorption lands in one commit.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|--------------|
| Repo-internal only | This phase authors Markdown/Python inside an already-trusted checkout; no external input, no network call, no new dependency is introduced. |
| Generated vs. authored trees | `harness/` is the trusted hand-edited source; `.opencode/`/`.claude/` are machine-generated projections that must never be hand-edited (a tampering surface if that discipline is broken). |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-50a-01 | Tampering | `.opencode/skill/**`, `.claude/skills/**`, `tools/harness_emit/emit-manifest.json` | mitigate | Task 3's action forbids hand-editing generated paths; `manifest.prune_then_write` performs the delete safely; a local emit-drift-equivalent check (`git diff --exit-code`) is run as part of `<verify>` so a hand-edit or a missed regenerate is caught before commit. |
| T-50a-02 | Tampering | `tools/harness_lint/caps.py::EXPECTED_SKILLS` (the pinned anti-sprawl gate) | mitigate | The three-way pin (`caps.py`, `test_skills.py`, `test_emit_determinism.py`) is verified as ONE assertion set in Task 2/3, not three independent edits — an incomplete edit fails loudly (`HarnessEmitError` at `generate.py:361-362`) before any write, per RESEARCH.md's "no valid intermediate commit state" finding. |
| T-50a-03 | Repudiation | New citation-integrity test (`test_harness_author.py`) | mitigate | The test collects and reports ALL offending citations by name (never a bare `assert False`), and carries its own negative-control test (`test_dangling_reference_scan_is_live`) proving the scan cannot silently no-op — closing this repo's known "checks that cannot fail" defect class for this new gate. |
| T-50a-SC | Supply chain | N/A | accept | This phase installs zero packages (no `uv add`, no new `pyproject.toml`); the npm/pip/cargo package-legitimacy gate does not apply. |
| T-50a-04 | Elevation of privilege / scope creep | `harness-author`'s stated scope | mitigate | The skill body explicitly states plugins/hooks are out of scope (no single-file source shape today) and cites zero `examples/` paths, keeping GEN-04 (core never depends on an instance) green — enforced by the existing `test_core_no_example_dep.py` suite, unchanged by this phase. |

</threat_model>

<verification>
Full-suite gate: `uv run pytest -q` (all tests including the new `test_harness_author.py` module) must
be green. Emit-drift equivalent: `python -m tools.harness_emit && git diff --exit-code -- .opencode
.claude opencode.json AGENTS.md CLAUDE.md tools/harness_emit/emit-manifest.json` must show no diff.
Structural counts: `git ls-files harness/skills/*/SKILL.md | wc -l` == 8;
`uv run pytest tools/harness_lint/tests/test_commands.py::test_command_count_is_stable -q` passes
(19, unchanged). Dangling-reference sweep: `git grep -n 'skill-creator' -- AGENTS.md CLAUDE.md
harness/ tools/ .opencode/ .claude/` returns no hits.
</verification>

<success_criteria>
1. `harness/skills/harness-author/SKILL.md` exists; every `path:line`/anchor citation it offers as a
   default resolves in this checkout, proven by `test_harness_author.py::test_citations_resolve_in_harness_author_skill`.
2. `.opencode/` and `.claude/` contain the emitted `harness-author` skill and no `skill-creator`
   remnant; two consecutive `python -m tools.harness_emit` runs produce byte-identical output
   (`git diff --exit-code` clean).
3. `harness/skills/skill-creator/` is deleted; `test_harness_author.py::test_no_tracked_reference_to_skill_creator`
   and `::test_harness_author_reachability` both pass; `git ls-files harness/skills/*/SKILL.md | wc -l`
   == 8 both before (historically) and after this phase.
4. No new file under `tools/*/pyproject.toml`, no new `harness/commands/*.md` beyond the pre-existing
   19, no new `contracts/**/*.schema.json` — verified by the existing command-count gate and a
   `git status` check in Task 3.
</success_criteria>

<output>
Create `.planning/phases/50a-harness-authoring/50a-01-SUMMARY.md` when done
</output>
