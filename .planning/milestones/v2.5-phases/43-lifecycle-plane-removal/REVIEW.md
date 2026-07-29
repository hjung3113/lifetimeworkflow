---
phase: 43-lifecycle-plane-removal
reviewed: 2026-07-28T00:00:00Z
depth: deep
diff_base: f589a67
files_reviewed: 41
files_reviewed_list:
  - tools/harness_emit/merge.py
  - tools/harness_emit/emit-manifest.json
  - tools/harness_emit/tests/test_coexist.py
  - tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr
  - tools/harness_emit/manifest.py
  - tools/harness_emit/generate.py
  - tools/memory_regen/inject.py
  - tools/memory_regen/tests/test_inject_assembler.py
  - tools/memory_regen/tests/__snapshots__/test_contracts_index.ambr
  - tools/contract_hash/hash.py
  - tools/contract_hash/tests/test_hash.py
  - tools/harness_lint/caps.py
  - tools/harness_lint/workspace_check.py
  - tools/harness_lint/tests/test_tests_are_isolatable.py
  - tools/harness_lint/tests/test_workspace_member_completeness.py
  - tools/harness_lint/tests/test_ci_lint_gate.py
  - tools/hooks/tests/test_settings_coexist.py
  - tools/docs_sync/tests/test_docs_sync_determinism.py
  - tools/docs_sync/tests/__snapshots__/test_docs_sync_determinism.ambr
  - tools/adoption_scan/scan.py
  - tools/adoption_scan/destinations.py
  - tools/adoption_scan/tests/test_install_completeness.py
  - tools/contract_graph/tests/test_query.py
  - tools/ruff_baseline/baseline.json
  - harness/agents/orchestrator.md
  - harness/commands/checkpoint.md
  - harness/commands/orient.md
  - harness/commands/review.md
  - harness/commands/verify-work.md
  - harness/opencode.json
  - harness/project.toml
  - harness/permission-matrix.json
  - contracts/.hashes/manifest.json
  - contracts/harness/task-control/gate-registry.json
  - .github/workflows/ci.yml
  - .claude/settings.json
  - AGENTS.md
  - README.md
  - README.ko.md
  - docs/how-to/task-lifecycle.md
  - docs/adr/0008-task-control-plane-lifecycle.md
findings:
  critical: 3
  warning: 12
  info: 6
  total: 21
status: issues_found
---

# Phase 43: Code Review Report — Lifecycle Plane Removal

**Reviewed:** 2026-07-28
**Depth:** deep (cross-file, emitted-artifact boundary, contract/manifest recompute, live simulation)
**Diff:** `f589a67..HEAD` (14 commits, 153 files, +199 / −12383 excluding `.planning/`)
**Status:** issues_found

## Summary

The mechanical core of the deletion is sound and I verified it rather than trusting it:

- `contracts/.hashes/manifest.json` recomputes **byte-exact** from the live tree (`build_manifest`
  → 9 entries, matching the committed file). The rebaseline is honest; `gate-registry.json` is
  genuinely intact (hash `dac0b5df21dd…` unchanged, `secret_patterns` array unmodified — the one
  half `tools/adoption_scan` still consumes).
- No surviving Python imports a deleted module. I enumerated and imported every `tools.*` package:
  zero failures. `grep -rnE "^\s*(from|import)\s+tools\.(task_control|task_packet|risk_router|
  evidence|handoff|discipline|capability|lifecycle_eval|hooks\.resume_gate)"` returns nothing.
- `tools/memory_regen/inject.py` is cleanly severed. `_active_context_pointer` (`:111-125`) is
  byte-identical to its pre-phase form, `import json` was correctly dropped with its only user, and
  the never-drop exemption tuple at `:152` lost `"task"` in the same edit as the section tuple. No
  half-wiring.
- The emitted trees match `harness/` source (I diffed all five repaired artifacts against
  `.claude/`; only the frontmatter-transform differences the emitter is supposed to introduce).
- The test-count edits I could falsify are honest and still strict: `EXPECTED_PAGES` and
  `EXPECTED_SKILLS` are compared with **set equality** (not subset), `_NEW_GATES` is exact, and the
  install-completeness floor was lowered 20→12 against a live value of **13** — a one-slot vacuity
  guard, correctly annotated "do not raise it back toward the live value."
- Suite is green at 982; ruff ratchet exits 0; no model identifiers in any commit or added line.

**But the deletion has a load-bearing hole.** The repo built a mechanism two phases ago
(`RETIRED_SIGNATURES`, Phase 41 / D-12) for exactly this situation, documented it as "Empty until
the next PreToolUse-hook deletion phase needs it," and then this phase — *the* next PreToolUse-hook
deletion phase — used it as a **local temporary** and reset it to `()` before committing. The
consequence is proven below (CR-01), not hypothesized. Alongside it, the constitution plane and the
shipped documentation still describe the deleted plane as live: a 107-line how-to that runs
non-existent modules (CR-02) and an ADR that remains `accepted` and unsuperseded (CR-03) while its
Phase-41 analogue was correctly superseded.

The residue sweep also confirms the prompt's hypothesis: the hyphen/underscore split let real
staleness through in both directions, including two prose survivals of `resume_gate` (underscore)
and a failure message that instructs developers to open a deleted directory.

---

## Critical Issues

### CR-01: `RETIRED_SIGNATURES` left empty — a re-emit can no longer remove the retired `resume_gate` hook, and the committed `settings.json` is unreproducible from committed source

**File:** `tools/harness_emit/merge.py:104-111` (and `:88-93`, `:243-245`)

**Issue.**
`merge_settings` classifies each existing `.claude/settings.json` hook group by matching its command
against `HARNESS_SIGNATURES`. Phase 43 removed `"tools.hooks.resume_gate"` from that tuple
(`:88-93`) and removed its group from `HARNESS_HOOK_GROUPS` — but left
`RETIRED_SIGNATURES: tuple[str, ...] = ()` at `:111`.

The module's own docstring states the failure this creates, verbatim:

> A plain signature-set diff (removing a signature from `HARNESS_SIGNATURES` alone) is **NOT enough
> to delete its group on re-emit**: a group whose command matches no *current* signature falls
> through as `sig is None` and is **mistaken for a GSD/human group (kept verbatim forever)** —
> silently defeating a deletion phase's whole point. […] Empty until the next PreToolUse-hook
> deletion phase needs it.

Phase 43 **is** that phase. Commit `ceebc4e`'s own message admits the workaround:

> re-emit: `.claude/settings.json` 8 -> 7 PreToolUse groups **via a transient RETIRED_SIGNATURES,
> reset to () afterwards**

I reproduced the resulting behaviour against the live emitter:

```
$ python -c "…merge_settings(settings_with_resume_gate_group)…"
PreToolUse count after re-emit: 8
resume_gate survived: True
```

**Concrete failure, who it breaks, when.**
Any repo that received the harness at v2.4 — the adoption targets `tools/adoption_scan` /
`tools/adoption_apply` exist to serve, plus any developer checkout or CI cache whose
`.claude/settings.json` predates `ceebc4e` — has the group
`{"matcher": "Write|Edit|Bash", … "uv run python -m tools.hooks.resume_gate"}` in its settings. On
the next `uv run python -m tools.harness_emit`:

1. `_group_signature(group, HARNESS_SIGNATURES)` → `None` (signature deleted).
2. `_group_signature(group, RETIRED_SIGNATURES)` → `None` (tuple empty).
3. `merge.py:246-247` keeps it **verbatim, forever**, as a "GSD/human group."

The orphan then fires on every Write, Edit, and Bash. Its guard prefix passes (`HARNESS_DEV_LIGHT`
unset in the product; `workspace_check.py` resolves fine), so it reaches
`uv run python -m tools.hooks.resume_gate` → `ModuleNotFoundError` → non-zero exit → **PreToolUse
denies the tool**. This is precisely the repo-wide outage `workspace_check.py:22-27` describes:
"file-write and shell tools stop working at the same moment, including the ones that would create
the missing file." Recovery requires a hand-edit of an emitted tree — itself a rule violation.

Secondarily, this breaks the single-source invariant the `emit-drift` gate claims to prove. The
committed `.claude/settings.json` (7 PreToolUse groups) **cannot be produced by the committed
emitter** from the pre-phase file; it was produced by a temporarily-modified emitter. `emit-drift`
passes today only because the deletion is already applied and the merge is idempotent on the
post-state. The source no longer encodes the retirement.

**Fix.**
```python
#: Signatures the harness used to own but no longer emits. […]
RETIRED_SIGNATURES: tuple[str, ...] = (
    "tools.hooks.resume_gate",  # Phase 43 (CER-07) — lifecycle-plane removal
)
```
Keep the entry permanently (it is a one-line, zero-runtime-cost migration record — removing it
re-arms the outage for any target that upgrades later than the next re-emit). Pair it with the test
in WR-10.

---

### CR-02: `docs/how-to/task-lifecycle.md` survives whole — 107 lines of shipped instructions that invoke seven deleted modules

**File:** `docs/how-to/task-lifecycle.md:1-107` (indexed from `docs/how-to/README.md:14`)

**Issue.**
Every executable line in this how-to targets a module this phase deleted:

| Line | Command | Module status |
|---|---|---|
| `:10` | `python -m tools.risk_router.intake --input intake.json --output .workflow/tasks/…` | deleted |
| `:20` | `python -m tools.task_control attest …` | deleted |
| `:21` | `python -m tools.task_control phase-gate …` | deleted |
| `:27` | `python -m tools.task_control transition …` | deleted |
| `:39` | `python -m tools.discipline … --phase EXECUTE` | deleted |
| `:55-56` | `python -m tools.capability list` / `route` | deleted |
| `:72` | `python -m tools.evidence capture …` | deleted |
| `:82-83` | `python -m tools.handoff generate` / `resume` | deleted |

It also asserts, as present-tense fact, declarations that no longer exist: `:34` cites
`harness/risk-policy.toml` and `harness/disciplines.toml` (both deleted this phase) and enumerates
per-lane discipline obligations; `:52` cites `harness/capabilities.toml` (deleted); `:94` names
"task-control tools" as the owner of `.workflow/tasks/` (directory deleted).

**Concrete failure, who it breaks, when.**
This repo's product *is* its documentation surface. An agent oriented by `/orient` reads `AGENTS.md`
and the Diátaxis tree; `docs/how-to/README.md:14` advertises this page as the recipe for "create,
gate, evidence, handoff, fresh-session resume, and completion." The first command a reader runs
fails with `No module named tools.risk_router`. Worse than a dead command: `:13` ("Do not select a
lower lane manually"), `:24`, `:30`, `:42`, `:50` and `:59` state *policy* an agent is likely to try
to comply with — it will search for a lane, a discipline record schema, and a capability allowlist
that no longer exist, and burn a session concluding the repo is broken.

Note that `tools/docs_guard` was removed in Phase 41, so no gate catches this. That is exactly why
the sweep had to be manual and exactly what it missed.

**Fix.** Delete `docs/how-to/task-lifecycle.md` and its index entry:
```diff
-- `task-lifecycle.md` — create, gate, evidence, handoff, fresh-session resume, and completion without crossing generator- or human-owned boundaries.
```
(`docs/how-to/README.md:14`). The Ownership-boundaries table at `:88-95` contains two still-true
rows (`harness/` → generator; `contracts/`/`golden/`/`docs/adr/` → CODEOWNERS) that already appear
in `AGENTS.md` and the `two-plane-memory` skill — no content needs relocating.

---

### CR-03: ADR-0008 remains `Accepted` and unsuperseded while the plane it decides is deleted — the constitution plane now contradicts the repo

**Files:** `docs/adr/0008-task-control-plane-lifecycle.md:5,9` · `docs/adr/README.md:37`

**Issue.**
ADR-0008 still reads:

```
- **Status:** Accepted — ratified by human/CODEOWNERS.
- **Superseded by:** —
```

and `docs/adr/README.md:37` lists it as `accepted`. Its decision clauses are now false statements
about the repo:

- `:33` — "The task namespace is `.workflow/tasks/<task-id>/`" — directory deleted.
- `:34` — "`.memory/state/` may retain only an active-task pointer" — pointer logic deleted from
  `inject.py`; `/checkpoint` no longer writes it.
- `:52` — names `tools/task_packet/`, `tools/risk_router/`, `tools/task_control/`,
  `tools/evidence/`, `tools/handoff/` as the "runtime-neutral implementation" — all deleted.

**Why this is a defect and not bookkeeping.** This repo's own precedence rule, restated in
`inject.py`'s `BANNER`, in `harness/agents/orchestrator.md:37` ("Contracts are the single source of
truth; if code diverges from `contracts/`, the code is wrong"), and in `CLAUDE.md`, is that
**contracts and accepted ADRs win a data conflict against code.** An agent that reads ADR-0008 —
which the SessionStart read-order actively steers it toward on any contract/decision question — is
instructed by the highest-authority plane in the repo to treat the deleted lifecycle as
authoritative and the deletion as the error.

**The precedent was set two phases ago and not followed.** Phase 41 removed the docs-review plane
and correctly marked its ADR: `docs/adr/README.md:35` shows ADR-0010 as `superseded by 0012`, and
ADR-0001 likewise at `:29`. ADR-0012 §(b) even *enumerates* Phase 43's deletions at `:108-111`.
Phase 43 shipped the deletion without the matching status change.

**Concrete failure.** An agent asked "where do task packets live / do I need a phase-gate before
EXECUTE?" resolves against `docs/adr/0008`, finds an `accepted`, unsuperseded decision with no
`Superseded by`, and either fabricates the missing tooling or refuses to proceed. A human auditing
governance sees an accepted, in-force decision with zero implementation.

**Fix.** ADRs are append-only and CODEOWNERS-gated, so this is a *proposal*, not an agent edit — but
it must be raised in this phase's PR, not deferred:

```diff
 - **Status:** Accepted — ratified by human/CODEOWNERS.
+- **Status:** Superseded by [ADR-0012](0012-ci-and-merge-as-decision-authority.md) — the plane this
+  ADR decides was removed whole in v2.5 Phase 43 (CER-07).
 - **Superseded by:** —
+- **Superseded by:** [ADR-0012](0012-ci-and-merge-as-decision-authority.md)
```
and in `docs/adr/README.md:37`, change the Status cell to `superseded by 0012`, matching rows 0001
and 0010.

---

## Warnings

### WR-01: The ruff ratchet was left 161 findings slack — three rule classes silently reset to zero and can return unnoticed

**File:** `tools/ruff_baseline/baseline.json:5-13`

The baseline still records `total: 245`. Live count after deleting 7021 LOC:

```
$ python -m tools.ruff_baseline
ruff ratchet: 84 findings (baseline 245)
  improved    B007: baseline 1 -> found 0      improved    E501: baseline 156 -> found 84
  improved    B904: baseline 1 -> found 0      improved    E701: baseline 18  -> found 0
  improved    B905: baseline 1 -> found 0      improved    E702: baseline 67  -> found 0
  improved    F841: baseline 1 -> found 0
PASS — and findings went DOWN. Record the shrink so it cannot come back:
    uv run python -m tools.ruff_baseline --update
```

**Failure scenario.** The ratchet's contract (`baseline.json:2`) is "per-rule finding counts that
may only SHRINK." Until re-recorded, a future PR can reintroduce 18 `E701`s, 67 `E702`s, a `B904`
bare-except-chain and a `B905` unzipped `zip()` — the exact defect classes DEBT-01 was convened to
ratchet down — and the `lint` CI job stays green. This is a gate weakened *by this phase*, and the
tool prints the remedy on every run.

**Fix.** `uv run python -m tools.ruff_baseline --update` in this phase's branch; commit
`baseline.json` (`total: 84`, `counts: {"E501": 84}`).

### WR-02: `README.ko.md:11` — navigation anchor points at a section this phase deleted

```
… · [v2.2 Task Control Plane](#v22--adaptive-task-control-plane) · [빠른 시작](…) …
```
The `## v2.2 — Adaptive Task Control Plane` heading was removed at `README.ko.md:51`. On GitHub the
link silently no-ops (scrolls nowhere). **Fix:** drop the ` · [v2.2 Task Control Plane](#…)` segment
from the nav line.

### WR-03: Both READMEs assert "nothing remains" — provably false

**Files:** `README.md:201` · `README.ko.md:98`

> "Nothing from it remains in the repository; this entry is kept as milestone history only."
> "저장소에 남은 산출물 없음 — 마일스톤 이력으로만 기록."

Still present: `contracts/harness/task-control/gate-registry.json` (deliberately deferred to Phase
44), `docs/adr/0008-task-control-plane-lifecycle.md`, `docs/how-to/task-lifecycle.md` (CR-02),
`docs/explanation/next-milestone-task-control-plane.md` (479 lines of design authority),
`docs/explanation/task-lifecycle-shadow-metrics.md`, and `harness/project.toml`'s `risk_overlay`
slot (WR-07).

**Failure scenario.** A reader (or an agent doing Phase 44 scoping) takes the README at its word,
skips the residue sweep, and Phase 44 inherits an unbounded surface. **Fix:** replace with the
truthful form — "The tooling, commands, skills, and six of its seven contracts were removed;
`gate-registry.json` and ADR-0008 remain pending Phase 44."

### WR-04: `test_tests_are_isolatable.py` failure message sends developers to a deleted directory

**File:** `tools/harness_lint/tests/test_tests_are_isolatable.py:108` (also `:19`, `:23`, `:26-27`, `:33`)

```python
"Fix with either idiom: add tools/<pkg>/tests/conftest.py (copy lifecycle_eval's), or "
```

`tools/lifecycle_eval/` was deleted this phase. **Failure scenario:** a developer adds a new
`tools/<pkg>/tests/` without wiring, hits this assertion, and the *only* remediation instruction the
gate gives points at a path that does not exist — turning a self-repairing gate into a dead end.
The docstring is stale in four more places: `:19` lists `pytest tools/lifecycle_eval` among CI's
scoped invocations (no such CI step remains), `:23` and `:26-27` narrate `lifecycle_eval` /
`task_control` history, `:33` names `lifecycle_eval` as a live example of the accepted idiom.

**Fix:** `(copy harness_lint's)` at `:108`; `(``harness_lint``)` at `:33`; drop
`pytest tools/lifecycle_eval` from `:19`. The history at `:21-29` is a deliberate narrative record
and may stay, but should be past-tensed so it does not read as a live path.

### WR-05: `docs/how-to/README.md:14` indexes the dead how-to

Companion to CR-02 — listed separately because it must be removed even if CR-02's page is retained
in some reduced form. It advertises "create, gate, evidence, handoff, fresh-session resume" as an
available recipe.

### WR-06: Two orphaned `docs/explanation/` pages for the deleted plane

**Files:** `docs/explanation/task-lifecycle-shadow-metrics.md` (whole) ·
`docs/explanation/next-milestone-task-control-plane.md` (whole, ~479 lines)

The shadow-metrics page defines six metrics (`lane_override`, `ceremony_count`,
`evidence_completeness`, `handoff_reconstruction_time`, …) whose collection boundaries are "packet
metadata," "evidence index at a fixed state revision," and "eval harness" — none of which exist.
`next-milestone-task-control-plane.md` is the *design authority* ADR-0008 cites at `:50`; it
specifies `/phase-gate`'s single source (`:194`), the `tools/evidence/` adapter (`:235`), the
`tools/handoff/` generator (`:276`), and an acceptance list (`:225`, `:306`) that can never pass.

**Failure scenario.** These are the two documents an agent lands on when asked "how does this repo
measure lifecycle ceremony?" or "what was the task-control design intent?" and both read as current
intent, not history. **Fix:** delete both, or relocate under a clearly-marked historical path and
add a one-line superseded banner. (Note: `docs/explanation/` is *not* on the constitution plane —
`CONSTITUTION_GLOBS` is `contracts/**`, `docs/adr/**`, `golden/**`, `docs/glossary.md` — so this is
an agent-writable repair.)

### WR-07: `risk_overlay` config slot survives with zero consumers

**File:** `harness/project.toml:21-24`

```toml
# TCP-05 risk-policy overlay slot.  A downstream instance may point this at its own
# declarative TOML overlay; the core does not discover or reference instance paths.
risk_overlay = ""
```

`grep -rn "risk_overlay"` across the whole repo (excluding `.planning/`) returns **this line only**.
Its sole reader was `tools/risk_router/router.py`'s overlay loader, deleted this phase.

**Failure scenario.** `harness/project.toml` is the documented "language/toolchain SINGLE SOURCE OF
TRUTH" that downstream projects override when vendoring the harness. A vendoring team reads
`:21-24`, points `risk_overlay` at their own TOML, and nothing happens — silently, with no error,
because no code reads the key. The comment promises behaviour ("a downstream instance may point this
at…") the harness can no longer deliver. **Fix:** delete `:21-24`.

### WR-08: `resume_gate` prose survives in two live source files — the underscore-spelling sweep missed them

**Files:** `tools/harness_lint/workspace_check.py:22` · `tools/harness_lint/tests/test_workspace_member_completeness.py:13-14`

Both enumerate the repo's PreToolUse guards as `(contract_guard, secret_scan, commit_gate,
resume_gate)`. There are now three. `workspace_check.py` is the bare-`python3` outage-recovery
module whose entire value is being accurate about the guard wall when the workspace is broken; a
stale roster there is exactly the wrong place for it. Neither reference is functional (both are
docstrings) so no test fires. **Fix:** drop `resume_gate` from both lists.

### WR-09: `test_query_source_never_imports_task_evidence_plane` is now permanently vacuous

**File:** `tools/contract_graph/tests/test_query.py:71-80`

```python
for forbidden in ("import tools.task_packet", "import tools.evidence",
                  "import tools.task_control", "import tools.handoff"):
    assert forbidden not in source, forbidden
```

All four modules are deleted, so `query.py` *cannot* import them — the assertion can never fail for
a real reason. This is distinguishable from a legitimate negative control: a negative control
asserts a name is absent from output that a live mechanism could still produce. Here no mechanism
could. The sibling `test_query_source_performs_no_file_io` (`:83-87`) remains a genuine invariant and
should stay.

**Failure scenario.** The D-03 "no task-evidence coupling" invariant is now *claimed* by a green test
that proves nothing — the "claimed control that does not exist" pattern this milestone was convened
to remove (`test_tests_are_isolatable.py:29-31` names it explicitly). **Fix:** delete the test and
its `:64` section comment, or narrow the D-03 header to the file-I/O half that still bites.

### WR-10: The `RETIRED_SIGNATURES` deletion path has zero test coverage, and this phase removed the one fixture that could have exercised it

**Files:** `tools/harness_emit/merge.py:243-245` · `tools/harness_emit/tests/test_coexist.py:119-193`

`grep -rn "RETIRED\|retired_signatures" tools/ --include="*.py"` finds only `merge.py` itself. The
drop-branch at `:243-245` is never executed by any test. Phase 43 then deleted the `resume_gate`
tuple from `_SEED_SETTINGS` (`test_coexist.py`, `-178,-188` in the diff) — the only fixture in the
repo that seeded a settings file carrying a hook the emitter no longer emits.

**Failure scenario.** This is why CR-01 shipped green. With the fixture removed and no
retired-signature test, nothing in the suite can observe that a formerly-owned group now survives a
re-emit forever. The next deletion phase repeats the bug with the same green suite.

**Fix (couple this with CR-01):**
```python
def test_a_retired_harness_group_is_dropped_on_re_emit() -> None:
    seed = copy.deepcopy(_SEED_SETTINGS)
    seed["hooks"]["PreToolUse"].append(
        {"matcher": "Write|Edit|Bash",
         "hooks": [{"type": "command",
                    "command": _GUARD_PREFIX + "uv run python -m tools.hooks.resume_gate",
                    "timeout": 15}]}
    )
    merged = merge_settings(seed)
    cmds = [h["command"] for g in merged["hooks"]["PreToolUse"] for h in g["hooks"]]
    assert not any("resume_gate" in c for c in cmds)
    assert len(merged["hooks"]["PreToolUse"]) == 7
```

### WR-11: `README.ko.md:81` — stale repository-layout line

```
docs/                # Diátaxis + adr/(0001–0008) + glossary + how-to/task-lifecycle.md
```
ADRs now run 0001–0012, and `task-lifecycle.md` is the dead page from CR-02 — held up here as *the*
example of the `docs/` tree. The English twin (`README.md:139`) was already generic and needed no
edit; only the Korean side was missed. **Fix:** `# Diátaxis (tutorials/how-to/reference/explanation)
+ adr/ + glossary`.

### WR-12: `REVIEW_FABLE.md` at the repo root is now a review of files that do not exist

**File:** `REVIEW_FABLE.md:12,24,27,32,37,44,55,57`

A tracked, root-level document (from Phase 18, commit `e8cc23e`) whose every finding anchors into
deleted code: `contracts/harness/task-control/evidence.schema.json:73`,
`tools/task_packet/transitions.py:26-63`, `tools/task_packet/tests/fixtures/negative/cases.json`,
`test_task_packet.py:1328-1350`, `tools/task_packet/validate.py`, and a `.workflow/tasks` plane
classification at `:57`. It also carries an open recommendation (`:27`) to promote
`transitions.json` — a contract this phase deleted.

Pre-existing, but this phase is what made it 100% false, and it sits at the repository root where it
is the most visible non-README document. **Fix:** delete it (its findings were discharged or made
moot), or move it under `.planning/milestones/`.

### WR-13: `tools/adoption_scan/destinations.py` still carries dead `.workflow/tasks/**` exclusion machinery

**File:** `tools/adoption_scan/destinations.py:20-22,60,133-140,186,301`

`_EXCLUDED_PREFIX: tuple[str, str] = (".workflow", "tasks")` (`:186`) plus ~20 lines of comment
justifying the omission of a directory that no longer exists, and a `proposed_sha=None` worked
example keyed on `.workflow/tasks/T-0001/task.json` (`:60`, `:301`). `test_dispositions.py:30,314-317`
still asserts against synthetic `.workflow/tasks/` destinations, so the tests pass on fixtures alone.

Functionally harmless (an exclusion for a non-existent path excludes nothing), but it is ~25 lines of
prose telling the next reader that a live plane is being deliberately scoped out. **Fix:** remove
`_EXCLUDED_PREFIX` and its rationale block, or reduce the comment to one line marking it a retired
guard kept defensively.

### WR-14: `/review` lost result durability with no successor, but keeps the promise that depended on it

**File:** `harness/commands/review.md:47-48`

The deleted paragraph routed findings through `tools.evidence.capture add-finding` with severity +
disposition + `E-*` reference, and ended "An open blocker or major finding prevents COMPLETE."
Removing it is consistent with CER-07, but step 4 still says:

> Re-run `/review` until no blocker/major remains, then `/verify-work`.

There is now no mechanism — file, state entry, or gate — by which anyone can know whether a prior
`/review` produced blockers. The findings live only in the conversation, so "until no blocker/major
remains" is unverifiable across a session boundary, and the natural agent behaviour on resume is to
assume the review was clean.

**Fix:** either state the new reality plainly ("findings are session-local; carry them into
`/checkpoint`'s `activeContext.md` if the work spans sessions") or drop the "re-run until" clause.
Silence is the worst option because it reads as an enforced loop.

### WR-15: `test_the_scan_finds_the_members_it_claims_to` now loops over a single-element tuple

**File:** `tools/harness_lint/tests/test_tests_are_isolatable.py:125-126`

```python
for expected in ("tools/harness_lint/tests",):
```

A one-element `for` is a code smell that hides how much the negative control lost (it was two
members; `lifecycle_eval` was the other). The count guard at `:122` (`>= 10`, live value 19) still
carries the anti-vacuity weight, so this is a readability/intent defect rather than a hole. **Fix:**
inline the single assertion, or restore a second live member (e.g. `tools/memory_regen/tests`) so
the enumeration is still cross-checked at more than one point.

---

## Info

### IN-01: `gate-registry.json`'s `gates` block now has zero consumers

**File:** `contracts/harness/task-control/gate-registry.json:2-45`

Only `secret_patterns` (`:47-56`) is read, by `tools/adoption_scan/scan.py:57`. The five `gates`
entries (`lint`, `tests`, `contract-drift`, `golden`, `derived-freshness`) existed to give
`tools/evidence/capture.py` its exact-argv registry; that consumer is deleted. The file is
correctly retained and hashed for Phase 44, but half of it is now dead constitution-plane data.
Worth naming explicitly in the Phase 44 scope so it is not re-justified as live.

### IN-02: ADR-0012 §(b) says Phase 43 deletes "the 7 task-control contracts"; 6 were deleted

**File:** `docs/adr/0012-ci-and-merge-as-decision-authority.md:108` vs `:117`

`:117` simultaneously assigns `gate-registry.json` to Phase 44. The ADR pre-emptively excuses this
at `:122-125` ("a later phase narrowing or widening its own scope … does NOT falsify this ADR"), so
no supersession is required — recorded so a future reader does not treat `:108` as a delivery gap.

### IN-03: `test_every_job_is_in_the_fan_in` is subset-only and cannot catch a stale `gate.needs` entry

**File:** `tools/harness_lint/tests/test_ci_lint_gate.py:72-80`

`assert declared <= fan_in` verifies every job is in the fan-in, but not that every fan-in entry is a
real job. Had this phase removed the `lifecycle-eval` *job* and forgotten its `gate.needs` entry, the
suite would have stayed green (GitHub Actions would have errored at workflow parse instead). The
phase got both halves right (`ci.yml:329`), but the gate is one-directional. Consider
`assert declared == fan_in`. Also stale: the docstring at `:10` cites "``lifecycle-eval``'s prose"
as a reason to parse rather than grep — the reasoning still holds via `polyglot_lint`, but the
example is gone.

### IN-04: `tools/harness_emit/generate.py:361` comment says "real tree = 9"; the tree is 12

Pre-existing (the set was 17 before this phase, so the comment was already wrong), surfaced here
because `EXPECTED_SKILLS` was edited two lines away in `caps.py`.

### IN-05: `harness/commands/verify-work.md:25` runs a bare repo-wide `ruff check .`

Pre-existing and out of this phase's scope, but it directly contradicts
`test_ci_lint_gate.py:51-61`'s rationale ("a bare `ruff check .` … would make the job PERMANENTLY
red"). With 84 live findings, `/verify-work` step 1 fails and the command's own instruction ("stop
at the first hard failure") halts the remaining four gates. Worth a follow-up ticket — the
in-session gate should mirror CI's `python -m tools.ruff_baseline`.

### IN-06: `harness/agents/orchestrator.md:43` heading "Intake → decompose" retains the deleted command's name

Reads as ordinary English now that `/intake` is gone, so it is not a dangling reference — but the
heading was named for the command. Low-cost rename to "Receive → decompose" removes the residual
association. Everything else in the repaired orchestrator checks out: steps renumbered 1-7 with no
gap, the routing table's "two dimensions" intro matches the body intro at `:22-25`, no row cites a
deleted skill, and the closing line survives intact.

---

## Verified-clean (things I tried to break and could not)

Recorded so the next reviewer does not re-spend the budget:

- **Contract manifest honesty** — `build_manifest(CONTRACTS_DIR)` reproduces
  `contracts/.hashes/manifest.json` exactly; 9 entries; `gate-registry.json` hash unchanged from
  pre-phase. `DATA_CONTRACT_PATHS` (`hash.py:30-33`) correctly retains `gate-registry.json` and
  `deny-domains.json`, and `test_hash.py:97-109` adds a real negative control: the fixture still
  *writes* `transitions.json`, so its absence from the result proves the `DATA_CONTRACT_PATHS` entry
  was dropped — not merely that the fixture stopped creating it. Good test hygiene.
- **`inject.py`** — `_active_context_pointer` untouched byte-for-byte; `import json` removed with its
  only user; `assemble`'s never-drop exemption (`:152`) lost `"task"` in the same edit as the
  section tuple (`:138-145`). No orphan constant, no half-wiring.
- **Emitted-tree integrity** — all 21 commands, 12 skills, 5 plugins and the 5 repaired artifacts
  match `harness/` source; `emit-manifest.json` prunes correctly (`manifest.py:64-80` deletes
  paths that leave the owned set, so a downstream `.opencode/plugin/resume-gate.ts` *is* removed —
  `settings.json` is the sole un-pruned surface, hence CR-01's narrow scope).
- **Test-edit integrity** — `EXPECTED_PAGES` (`==`, `test_docs_sync_determinism.py:118,146`),
  `EXPECTED_SKILLS` (`==`, `test_emit_determinism.py:103` and `validate.py:182-183`), `_NEW_GATES`
  and the 7/4 slot counts are all exact-set or exact-count comparisons; none was relaxed to a
  subset. The install-completeness floor 20→12 sits one below the live 13.
- **No dangling imports** — every `tools.*` package imports cleanly; CI, `pyproject.toml`,
  `workspace.toml`, `opencode.json`, `harness/permission-matrix.json` and `AGENTS.md` carry zero
  references to the deleted plane.
- **Model-identity rule** — no model identifier in any commit subject/body or added source line.
- **Surface growth** — no new gate, tool, contract, or dependency introduced. `uv.lock` shrank.

---

_Reviewed: 2026-07-28_
_Reviewer: gsd-code-reviewer_
_Depth: deep_
