# Phase 39: Decision Boundary - Research

**Researched:** 2026-07-26
**Domain:** Documentation-only ADR authorship in a constitution-gated append-only record (MADR 4.x)
**Confidence:** HIGH — every claim below is grounded in a real file path/line read this session; no
web research was needed (the MADR spec is not in question — the repo already has a working
`docs/adr/README.md` convention and 11 precedent records to imitate).

## Summary

Phase 39 authors zero code. It writes one new file (`docs/adr/0012-*.md`), edits the frontmatter
of three existing ADRs (0001, 0010, 0011 — `Status`/pointer fields only, never their decision
bodies), adds a table/entries to `.planning/STATE.md`, and touches nothing else. The single
mechanical obstacle is that **`docs/adr/**` is on the constitution plane** and `contract_guard.py`
denies any agent `Write`/`Edit` there unless a human has set `GOLDEN_APPROVE_HUMAN` in the session
env — so every ADR file touch in this phase must be gated behind a `checkpoint:human-verify` (or
the plan must instruct the agent to ask the human to export the token before the write). Nothing in
CI (`contract-drift`, `emit-drift`, `stale-derived`, `core-suite`, `golden`) reads ADR content, and
no test counts ADRs or asserts ADR-0001's four-member list against anything **except** one already-
existing pinned test (`test_every_declared_plane_member_is_independently_enforced`) that will
legitimately go stale the moment ADR-0012 supersedes ADR-0001's list — but that test targets
`CONSTITUTION_GLOBS` in `contract_guard.py`, which this phase does not touch, so it stays green
through Phase 39 and only needs updating in Phase 44 (when golden actually leaves the core). The
`docs-guard` CI job is **already RED** for an unrelated, pre-existing reason (`task-control-cli-
howto` binding staleness) — Phase 39 does not need to fix this and should not try to (it would be
a scope violation of "no gate/CI change").

**Primary recommendation:** Author ADR-0012 and the three status edits as a single
`checkpoint:human-verify` task (or a sequence of tasks each preceded by "ask the human to set
`GOLDEN_APPROVE_HUMAN`, run the write, then unset it") using the `/adr` command's scaffold
convention; record CER-03's three dispositions and the SEAL-05 withdrawal as new rows appended to
`.planning/STATE.md`'s existing `## Deferred Items` table (never edit the old RAT-4/RAT-5/security
rows — append a NEW row that supersedes them in meaning, consistent with append-only practice
already used in that file: see the `RESOLVED 2026-07-22` rows above).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| ADR authorship (new record) | Constitution plane (`docs/adr/`) | — | Human-owned, CODEOWNERS-gated, append-only per `docs/adr/README.md` |
| ADR status/frontmatter edit (0001/0010/0011) | Constitution plane (`docs/adr/`) | — | Same plane; edits are metadata-only, never decision-body edits |
| Carried-item disposition record (RAT-4/5, deny-spelling, SEAL-05) | Planning/derived-but-human-owned (`.planning/STATE.md`) | — | `.planning/**` is the GSD-owned lane, not the constitution plane — no `contract_guard` deny applies here, an agent may write it directly |
| CI verification (drift/emit-drift/stale-derived/core-suite/golden) | CI / Backend tooling | — | None of these read `docs/adr/**` content; this phase cannot regress them and must not attempt to fix the pre-existing unrelated `docs-guard` RED |

This phase touches no Browser/Client, Frontend-Server, API, CDN, or Database tier — it is
constitution-plane documentation plus one planning-plane record.

## Standard Stack

Not applicable — no packages, libraries, or code are installed or written by this phase. Skip
"Installation" and "Version verification."

### Core / Supporting / Alternatives Considered

N/A — decision-record-only phase.

## Package Legitimacy Audit

N/A — this phase installs no external packages. Table omitted per the protocol's own scope (the
gate applies only "whenever this phase installs external packages").

## Architecture Patterns

### System Architecture Diagram

```
human (sets GOLDEN_APPROVE_HUMAN) ──▶ agent Write/Edit under docs/adr/**
                                              │
                                              ▼
                              tools/hooks/contract_guard.py::decide()
                              (CONSTITUTION_GLOBS = contracts/** , docs/adr/** ,
                               golden/** , docs/glossary.md)
                                              │
                          approved=True (token set) ──▶ ALLOW, write proceeds
                          approved=False (no token)  ──▶ DENY (PreToolUse)
                                              │
                                              ▼
                 docs/adr/0012-*.md (NEW, accepted)   docs/adr/0001-*.md (Status → superseded by 0012)
                 docs/adr/README.md (+1 index row)    docs/adr/0010-*.md (Status → superseded by 0012)
                                                       docs/adr/0011-*.md (Status → accepted, Date/Deciders filled)
                                              │
                                              ▼
                          .planning/STATE.md (append: RAT-4/RAT-5/deny-spelling
                          dispositions = obsolete-by-deletion; SEAL-05 = withdrawn)
                                              │
                                              ▼
               CI fan-in (drift / emit-drift / stale-derived / core-suite / golden / docs-guard)
               — none of these read docs/adr content; docs-guard is ALREADY RED pre-existing
               (unrelated task-control-cli-howto staleness) and stays exactly as red, not more.
```

### Recommended "Project Structure" (files this phase touches — no new directories)

```
docs/adr/
├── 0001-walking-skeleton-golden-core.md      # EDIT: Status → "superseded by 0012" (append pointer only)
├── 0010-human-docs-review-obligation-model.md # EDIT: Status → "superseded by 0012"
├── 0011-gate-right-sizing-dev-light-ci-strong.md # EDIT: Status proposed→accepted, fill Date/Deciders
├── 0012-<kebab-title>.md                      # NEW: the phase's one authored ADR
└── README.md                                  # EDIT: append one index row, flip 0010's Status cell

.planning/
└── STATE.md                                   # EDIT: append disposition rows (Deferred Items table)
```

### Pattern 1: Supersede-don't-edit (the only ADR-editing pattern this repo uses)

**What:** To change a past decision, write a NEW numbered ADR that cites the old one
(`Supersedes: NNNN`) and flip the OLD ADR's `Status` field to `superseded by NNNN` — the old
record's Context/Decision/Consequences body is never touched.
**When to use:** Exactly this phase's ADR-0001 and ADR-0010 edits.
**Example (the convention, from `docs/adr/README.md:14-19`):**
```
- **Supersede, don't edit.** To change a past decision, write a **new** ADR that references the
  old one and set the old ADR's `Status: superseded by NNNN` (and the new one's
  `Supersedes: NNNN`). The original stays in place as the historical record.
```
No prior ADR in this repo has actually BEEN superseded yet (all 11 existing records show
`Superseded by: —`), so Phase 39 is this repo's FIRST real exercise of the convention — there is no
in-repo precedent commit to imitate beyond the written rule itself. Follow the rule literally: only
the `Status` line (and the `Superseded by:` metadata line already present in every ADR's header,
e.g. ADR-0001 line 9 `- **Superseded by:** —`) changes; every other line of ADR-0001 and ADR-0010
stays byte-identical.

### Pattern 2: The `/adr` command's scaffold convention

**What:** `.opencode/command/adr.md` / `harness/commands/adr.md` define the next-ADR-number
algorithm and required MADR sections.
**When to use:** For authoring ADR-0012 itself.
**Example (source: `harness/commands/adr.md:16-24`):**
```
1. Determine the next number = highest existing `docs/adr/NNNN-*.md` + 1 (zero-padded to 4):
   !`ls docs/adr/ | grep -E '^[0-9]{4}-' | sort | tail -1`
2. Create `docs/adr/NNNN-<kebab-title>.md` from the MADR sections: Title, Status
   (`proposed` → `accepted`), Context and Problem Statement, Decision Drivers, Considered Options,
   Decision Outcome, Consequences, Links. Title/topic come from `$ARGUMENTS`.
3. Add a row to the `docs/adr/README.md` index — never remove a row.
```
Current highest ADR is `0011-gate-right-sizing-dev-light-ci-strong.md`, so the new file is
`docs/adr/0012-<kebab-title>.md` — confirmed by `ls docs/adr/` (11 numbered files, 0001–0011).

### Anti-Patterns to Avoid

- **Editing an accepted ADR's decision body.** ADR-0001 and ADR-0010's Context/Decision/Consequences
  sections are locked; only `Status` (and the paired `Superseded by:`) may change.
- **Writing directly with the Write/Edit tool without a human-set `GOLDEN_APPROVE_HUMAN`.** This
  will be denied by `contract_guard.py::decide()` — see Pitfall 1 below.
- **"Fixing" the stale `CONSTITUTION_GLOBS` comment/test in `contract_guard.py` during this phase.**
  The four-member list, and the pinned test that asserts it, legitimately stay as-is until Phase 44
  physically relocates golden. Touching that file is a code change and out of this phase's
  non-goals ("no code deletion, no gate/CI change, no new mechanism").
- **Trying to make the already-RED `docs-guard` job green.** Its current failure
  (`task-control-cli-howto` staleness) is unrelated to anything this phase touches and repairing it
  is out of scope (would be a gate/CI-adjacent change this milestone explicitly defers).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Next ADR number / file scaffold | A custom numbering script | The existing `/adr` command's `ls docs/adr/ \| grep -E '^[0-9]{4}-' \| sort \| tail -1` algorithm | Already the sanctioned, tested convention; reinventing risks a number collision or non-kebab title |
| Constitution-plane write bypass | A workaround (e.g., writing outside `docs/adr/` then `mv`) | Ask the human to set `GOLDEN_APPROVE_HUMAN` for the write, per the existing `/golden-approve` / gate-model precedent | `contract_guard` denies the tool call itself; a `mv` after the fact still originated from a denied write and defeats the entire "machines gate, humans ratify" invariant this repo is built on |
| Carried-item disposition bookkeeping format | A new schema/table shape | The exact `.planning/STATE.md` `## Deferred Items` markdown-table row shape already used for RAT-4/RAT-5/the security finding (`| Category | Item | Status | Deferred At |`) | Keeps one format across the file instead of forking a second bookkeeping convention |

**Key insight:** every mechanism this phase would need (ADR scaffold, supersede convention, human
ratification token, STATE.md disposition table) already exists and is documented in this repo —
the entire phase is "use the existing mechanisms once, correctly," never "build something new,"
which matches the phase's own non-goals verbatim.

## Runtime State Inventory

Not applicable — this is not a rename/refactor/migration phase. No stored data, live service config,
OS-registered state, secrets, or build artifacts are touched. Skip.

## Common Pitfalls

### Pitfall 1: The agent cannot write `docs/adr/**` at all without a human-set token

**What goes wrong:** An agent runs `Write`/`Edit` against `docs/adr/0012-*.md` (or 0001/0010/0011)
and the harness's own PreToolUse guard denies it.
**Why it happens:** `tools/hooks/contract_guard.py:53` — `CONSTITUTION_GLOBS = ["contracts/**",
"docs/adr/**", "golden/**", "docs/glossary.md"]` — and `decide()` (lines 70+) returns a deny dict
unless `approved` is `True`, which is only set when the env var `GOLDEN_APPROVE_HUMAN`
(`contract_guard.py:57`) is a non-empty, non-blank string set by a human in a gitignored
`.claude/settings.local.json` (per `harness/skills/gate-model/SKILL.md`'s "The ratification token"
section). **Agents must never fabricate this token.**
**How to avoid:** The plan must make every ADR-touching task a `checkpoint:human-verify` (or
equivalent instruction: "ask the human to export `GOLDEN_APPROVE_HUMAN=1` before this write, and to
unset it after"). Do not attempt the write and silently fall back to some other path.
**Warning signs:** A PreToolUse deny message citing `contract_guard` / "constitution plane" /
"GOLDEN_APPROVE_HUMAN".

### Pitfall 2: Treating ADR-0001's constitution-member-list supersession as a code change

**What goes wrong:** A planner reads "ADR-0012 supersedes ADR-0001's constitution-member list
(golden leaves the core)" and infers that `CONSTITUTION_GLOBS` in `contract_guard.py` (and the
matching test) must be edited THIS phase.
**Why it happens:** The roadmap's Phase 39 scope line and CER-01 both use the phrase "supersedes
ADR-0001's constitution-member list," which reads like an implementation instruction.
**How to avoid:** Re-read the phase's own Non-goals: "no code deletion, no gate/CI change, no new
mechanism... this phase is decision-record-only." The supersession is a DECLARATION in ADR-0012's
prose (and ADR-0001's `Status` flip) that golden WILL leave the core — the actual code move (and the
`CONSTITUTION_GLOBS` / `test_every_declared_plane_member_is_independently_enforced`
(`tools/hooks/tests/test_contract_guard.py:352-375`) update) happens in **Phase 44** ("relocate the
golden stack to `examples/log-parser/`"). Between Phase 39 and Phase 44, the repo is knowingly
inconsistent (ADR says golden leaves the core; code still enforces `golden/**` in the four-member
list) — this is expected and should be named explicitly in ADR-0012's Consequences section, not
hidden.
**Warning signs:** A task in the plan touching any `.py` file, `permission-matrix.json`, or the
pinned test in Phase 39.

### Pitfall 3: Assuming a docs-review-ledger binding forces a disposition for the ADR edits

**What goes wrong:** A planner assumes editing `docs/adr/0001-*.md` / `0010-*.md` / `0011-*.md` or
adding `0012-*.md` triggers a `docs/doc-dependencies.toml` binding obligation that must be
discharged via `docs/.docs-review-ledger.toml` in the same phase.
**Why it happens:** ADR-0010 documents an entire "ADR track" disposition vocabulary
(`REVIEWED_STILL_CURRENT` / `SUPERSEDING_ADR_REQUIRED`) for `docs/adr/**` targets, which sounds
like it applies broadly.
**How to avoid:** Read `docs/doc-dependencies.toml` directly — there is exactly **one** binding
whose target is under `docs/adr/**`: `contract-graph-adr-0009` (target
`docs/adr/0009-contract-relationship-graph-model.md`, sources
`tools/contract_graph/{compile,query}.py`). No binding targets ADR-0001, ADR-0010, ADR-0011, or a
future ADR-0012. Verified live: `uv run python -m tools.docs_guard` output lists 8 bindings total
and none references 0001/0010/0011/0012. So none of this phase's edits create a NEW docs-guard
obligation. (`docs-guard` IS currently red, but for the unrelated `task-control-cli-howto` binding
— see Pitfall 4.)
**Warning signs:** A task that tries to add a `[[binding]]` row or a `[[reviewed]]` ledger row for
an ADR file.

### Pitfall 4: Blaming this phase for the already-RED `docs-guard` CI job

**What goes wrong:** Running `uv run python -m tools.docs_guard` locally shows `docs-guard: FAILED`
and a planner assumes this phase broke it or must fix it as part of Success Criteria 6 ("the
existing suite... stay green").
**Why it happens:** The failure reason (`stale-digest: binding task-control-cli-howto was reviewed
at digests that no longer match the working tree`) is pre-existing and unrelated to ADRs — verified
live this session (exit path shows `FAILED` on `task-control-cli-howto`, nothing else).
**How to avoid:** Success Criterion 6 says "no contract, gate, or emitted artifact changes **from
this phase**" — i.e., this phase must not make things WORSE, not that every gate must already be
green before it starts. Do not add a task to repair `docs-guard`'s pre-existing red state; that is
explicitly out of scope for a "no gate/CI change" phase and belongs to a different, unscoped
concern.
**Warning signs:** A task that touches `docs/how-to/task-lifecycle.md` or the docs-review ledger to
try to turn `docs-guard` green.

## Code Examples

### ADR frontmatter block shape (verified against all 11 existing ADRs)

```markdown
# N. Title

- **Status:** accepted
- **Date:** 2026-07-26
- **Deciders:** kimhyojung (CODEOWNERS)
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement
## Decision Drivers
## Considered Options
## Decision Outcome
## Consequences
## Links
```
Source: `docs/adr/0001-walking-skeleton-golden-core.md:1-9` and `docs/adr/0010-...md:1-9` (both
follow this exact shape; 0010 additionally carries a `- **Complements:**` line, which is optional
per-ADR, not part of the pinned template).

### The exact supersede edit for ADR-0001 (metadata-only)

```diff
- **Status:** accepted
+ **Status:** superseded by 0012
...
- **Superseded by:** —
+ **Superseded by:** [0012](0012-<kebab-title>.md)
```
Everything else in the file (lines 11-62 of `docs/adr/0001-walking-skeleton-golden-core.md`) is
untouched.

### The exact fill-in edit for ADR-0011 (currently `proposed`, empty `Date`/`Deciders`)

```diff
- **Status:** proposed
+ **Status:** accepted
- **Date:** —
+ **Date:** 2026-07-26
- **Deciders:** —
+ **Deciders:** kimhyojung (CODEOWNERS)
```
Add a new subsection (or a `Consequences` addendum, never editing existing prose) recording that its
code landed in commit `bc9a6d9` ("feat(hooks): guard commands degrade instead of deadlock, and dev
can opt out") BEFORE this ratification — verified via `git show --stat bc9a6d9`, which is exactly
the `HARNESS_DEV_LIGHT` / workspace-degrade implementation ADR-0011 describes in its own body.

### `docs/adr/README.md` index row + status flip

```diff
| [0010](0010-human-docs-review-obligation-model.md) | Human-Docs Review Obligation Model: ... | proposed |
+| [0010](0010-human-docs-review-obligation-model.md) | Human-Docs Review Obligation Model: ... | superseded by 0012 |
+| [0011](0011-gate-right-sizing-dev-light-ci-strong.md) | Gate right-sizing — dev-light, CI-strong | accepted |
+| [0012](0012-<kebab-title>.md) | <Title> | accepted |
```
Note ADR-0011 has **no row at all yet** in `docs/adr/README.md` (the index currently lists only
0001–0010 — verified: `grep` of the README shows rows through `[0010]` only, and ADR-0011 is missing
entirely). This phase must add ADR-0011's missing index row in addition to the 0012 row and 0010's
status flip.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| ADR-0010's "in-session guard wall" enforcement model (heavy, per-tool denies) | ADR-0011's "dev-light, CI-strong" model (`HARNESS_DEV_LIGHT` opt-out + workspace-degrade) | ADR-0011 code landed `bc9a6d9` (2026-07-26), ratification pending until this phase | Phase 39 formally closes the loop: ratifies ADR-0011, declares the SEAL-02/03 in-session bash-deny work (which ADR-0011 already implicitly cut) as closed via CER-03/SEAL-05 withdrawal |
| Human-ratification-gate proliferation (RAT-4, RAT-5, per-tool deny spelling repair, SEAL-05 portable ratification record) | "CI + the merge are the authority" (ADR-0012) | This phase | Every future v2.5 deletion phase cites ADR-0012 instead of re-litigating whether a human-ratification mechanism is still owed |

**Deprecated/outdated:** SEAL-05's "portable ratification record" concept (a checkable provenance
artifact independent of a git host assigning a reviewer) is explicitly withdrawn, not deferred —
recorded in `.planning/ROADMAP.md:339` and this phase's own success criteria; do not resurrect it as
a future-phase carryover.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | ADR-0012's exact kebab-title is left to the planner/executor to choose at authoring time (e.g. `0012-ci-and-merge-as-decision-authority.md`) — no title is pre-ordained in ROADMAP.md/REQUIREMENTS.md beyond the content it must carry | Code Examples, Pattern 2 | Low — any reasonable kebab-title satisfies CER-01/02; only the numbering and content are load-bearing |
| A2 | "Deciders: kimhyojung (CODEOWNERS)" is the correct Deciders value for ADR-0011 and ADR-0012, matching the pattern used by ADR-0010 (`docs/adr/0010-...md:7`) | Code Examples | Low-Medium — if the actual human ratifier differs, the plan should let the human confirm the exact name/handle at write time rather than hardcode it |

**If this table is empty:** N/A — two low-risk naming assumptions are listed above; nothing else in
this research is unverified.

## Open Questions

1. **Exact ADR-0012 title/kebab-slug**
   - What we know: it must cover CI+merge-as-authority, the DEV/PRODUCT boundary + operative rule,
     the ADR-0001/ADR-0010 supersession, ADR-0011 acceptance, and the bash-residual declaration —
     five substantive topics in one ADR (per the roadmap's explicit "adopt as ONE ratified unit"
     style already used by ADR-0010).
   - What's unclear: whether the planner should split this into multiple Decision Outcome
     subsections (mirroring ADR-0010's numbered-clause style) or keep it a single flat narrative
     (mirroring ADR-0001's style).
   - Recommendation: mirror ADR-0010's "adopted as ONE ratified unit, N clauses" structure — this
     phase already has 5 clearly enumerable clauses (CI+merge authority, DEV/PRODUCT boundary +
     operative rule, ADR-0001 supersession, ADR-0010 retirement + ADR-0011 acceptance, bash-residual
     declaration) and that structure has an in-repo precedent to imitate exactly.

2. **Whether "bash surface... permanent residual by design" needs its own Decision Driver citing
   ADR-0011's already-accepted acceptance of the same gap**
   - What we know: ADR-0011's own "What this deliberately accepts" section (lines 61-69) already
     names the exact residual: `HARNESS_DEV_LIGHT` sessions leave `secret_scan` and `ledger_guard`
     unscreened in-editor, and `.planning/STATE.md:308` independently documents the underlying
     per-tool-deny-spelling gap (`"uv *": "allow"` in `harness/permission-matrix.json:9` bypasses the
     `Write|Edit`-only matcher).
   - What's unclear: whether ADR-0012 should cite ADR-0011 directly (as a `Complements:` or
     `Supersedes:` link) or treat the bash-residual declaration as a wholly new, independent finding.
   - Recommendation: cite ADR-0011 via a `Complements:` frontmatter line (matching ADR-0010's own use
     of that field), since ADR-0012 is not changing ADR-0011's decision — only formally ratifying it
     and layering the "permanent by design" framing on top of a gap ADR-0011 already named as
     accepted.

## Environment Availability

Skipped — this phase has no external tool/service/runtime dependency. It edits Markdown files and
appends to a Markdown state file; the only "tool" involved is the agent's own Write/Edit capability
and the human-gated `GOLDEN_APPROVE_HUMAN` token, both already covered above.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (existing `core-suite` CI job: `uv run pytest`) — but this phase adds **no new automated test**, because its deliverable is prose/frontmatter, not executable behavior |
| Config file | root `pyproject.toml` / `pytest.ini` (pre-existing, unchanged) |
| Quick run command | `uv run python -m tools.docs_guard` (confirms no NEW docs-review obligation was created) and `grep -n "^- \*\*Status:\*\*" docs/adr/0001-*.md docs/adr/0010-*.md docs/adr/0011-*.md docs/adr/0012-*.md` (confirms the four frontmatter edits landed) |
| Full suite command | `uv run pytest` (core-suite) + `uv run python -m tools.contract_drift.drift` (drift) — both must stay exactly as green/red as they were before this phase (verified pre-phase: drift/emit-drift/stale-derived/core-suite/golden all pass; `docs-guard` is pre-existing RED for an unrelated reason) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CER-01 | ADR-0012 exists, `Status: accepted`, names deleted surfaces + ADR-0001/0010 supersession + bash-residual declaration | manual (grep-assisted) | `grep -l "accepted" docs/adr/0012-*.md && grep -c "supersed" docs/adr/0012-*.md` | ✅ Wave 0 — file doesn't exist yet, created by this phase's own task |
| CER-01 (ADR-0011 accept) | ADR-0011 has non-empty `Date`/`Deciders`, records `bc9a6d9` code-before-ratification | manual (grep-assisted) | `grep -E "^\- \*\*(Date\|Deciders):\*\* [^—]" docs/adr/0011-*.md` | ✅ — file exists, edited in place |
| CER-02 | ADR-0012 states DEV/PRODUCT boundary + operative rule | manual (read-through) | `grep -i "no product capability may be" docs/adr/0012-*.md` | ✅ Wave 0 — created by this phase |
| CER-03 | RAT-4/RAT-5/deny-spelling recorded obsolete-by-deletion; SEAL-05 withdrawn (not deferred) in STATE.md | manual (grep-assisted) | `grep -i "obsolete-by-deletion" .planning/STATE.md && grep -i "SEAL-05" .planning/STATE.md \| grep -i withdrawn` | ✅ — file exists, appended |
| SC-5 (roadmap) | ADR-0001/0010 carry superseded-by pointer, bodies unedited | manual diff review | `git diff docs/adr/0001-*.md docs/adr/0010-*.md` — reviewer confirms only frontmatter lines changed | ✅ |
| SC-6 (roadmap) | Suite/contract-drift stay green; no contract/gate/emitted-artifact change | automated | `uv run pytest && uv run python -m tools.contract_drift.drift && uv run python -m tools.harness_emit` (then `git diff --exit-code` on emitted trees) | ✅ — pre-existing CI jobs, unmodified |

### Sampling Rate

- **Per task commit:** the grep-assisted manual commands above (fast, seconds).
- **Per wave merge:** `uv run pytest` (core-suite) + `uv run python -m tools.contract_drift.drift` +
  `uv run python -m tools.harness_emit` (confirm zero emitted-artifact drift, since ADR edits should
  never affect emission).
- **Phase gate:** Full suite green (excluding the pre-existing, out-of-scope `docs-guard` red) before
  `/gsd:verify-work`.

### Wave 0 Gaps

None — this phase is prose/frontmatter-only and has no automated-test infrastructure gap. The
"tests" are grep-assisted content checks a human or the plan-checker runs directly; no new
`tests/test_*.py` file, fixture, or framework install is needed or appropriate for a decision-record
phase.

## Security Domain

`security_enforcement` is not explicitly set to `false` in `.planning/config.json`, so this section
is included, but scoped honestly: this phase performs no runtime code change, so most ASVS
categories do not apply. The one relevant control is **access control over the constitution plane
itself** (who may write `docs/adr/**`), which this phase must respect, not implement.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | No auth surface touched |
| V3 Session Management | No | N/A |
| V4 Access Control | Yes | The existing `contract_guard.py` PreToolUse deny + `GOLDEN_APPROVE_HUMAN` human-ratification token (already-built control; this phase must operate WITHIN it, never bypass or weaken it) |
| V5 Input Validation | No | No new input-handling code |
| V6 Cryptography | No | N/A |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Agent self-blessing a constitution-plane write (fabricating or working around the human ratification requirement) | Elevation of Privilege | `contract_guard.py`'s deny-unless-`GOLDEN_APPROVE_HUMAN` gate — never set the token programmatically; always require an actual human action per session |
| Silent in-place edit of an "accepted" ADR's decision body (repudiation of the historical record) | Repudiation | The append-only/supersede-don't-edit convention (`docs/adr/README.md:14-19`); the plan must diff-review that ADR-0001/0010 edits touch ONLY frontmatter lines |

## Sources

### Primary (HIGH confidence — direct repository reads this session)

- `.planning/ROADMAP.md:172-306` — the v2.5 milestone block, binding constraint, DEV/PRODUCT
  boundary paragraph, Phase 39 detail section, and success criteria
- `.planning/REQUIREMENTS.md:1-43` — CER-01/02/03 exact text, the binding constraint, the four goal
  functions
- `.planning/STATE.md:122-134,282-312` — SEAL-05/RAT-4/RAT-5/security-finding original wording and
  the exact `## Deferred Items` table shape to append to
- `.planning/research/v2.5-scoping-FINAL.md:1-40` — the panel's DEV/PRODUCT scope table and the
  operative rule's exact wording
- `docs/adr/0001-walking-skeleton-golden-core.md` (full read) — current `Status: accepted`, the
  four-member constitution-plane declaration at line 48
- `docs/adr/0010-human-docs-review-obligation-model.md` (full read) — current `Status: proposed`,
  the ADR-track disposition vocabulary, the docs-plane agent-authority boundary
- `docs/adr/0011-gate-right-sizing-dev-light-ci-strong.md` (full read) — confirmed `Status:
  proposed`, `Date: —`, `Deciders: —`
- `docs/adr/README.md` (full read) — index convention, confirmed ADR-0011 has no row yet
- `tools/hooks/contract_guard.py:1-110` — `CONSTITUTION_GLOBS`, `decide()`, `GOLDEN_APPROVE_HUMAN`
  gating logic
- `tools/hooks/tests/test_contract_guard.py:352-375` — the pinned four-member mutation-proof test
- `harness/permission-matrix.json:2` — the note confirming ADR-0001:48 as the four-member source
- `harness/skills/gate-model/SKILL.md` — the human-ratification-token mechanics, hook table
- `docs/doc-dependencies.toml` (full read) — confirmed only one `docs/adr/**`-targeted binding
  (`contract-graph-adr-0009`), none for 0001/0010/0011
- `docs/.docs-review-ledger.toml` (partial read) — ledger row shape, ADR-track disposition comment
- Live command: `uv run python -m tools.docs_guard` — confirmed current RED state is
  `task-control-cli-howto` staleness, unrelated to ADRs
- `.github/workflows/ci.yml:140-410` — confirmed drift/golden/emit-drift/stale-derived/core-suite
  job commands, none touching `docs/adr/**`
- Live command: `git show --stat bc9a6d9` — confirmed the ADR-0011 code-before-ratification commit
  and its content
- `tools/adoption_scan/destinations.py:1-50,136-137` — `_CATEGORY_GLOBS` provenance and the
  `CONSTITUTION_GLOBS`/`is_gsd_owned` import-not-retype rule
- `tools/harness_emit/generate.py:30-50` — confirmed `generate.py` projects the checkout into itself
  (the emitter, distinct from the install-channel `_CATEGORY_GLOBS`)
- `.planning/milestones/v2.4-REQUIREMENTS.md:45-49,122-125` — SEAL-05's original exact text and
  status-table format
- `.planning/config.json` — confirmed `nyquist_validation: true`, `security_enforcement` absent
  (treated as enabled)

### Secondary / Tertiary

None — no web research was performed; every claim traces to a direct repository read or a live
command run this session.

## Metadata

**Confidence breakdown:**
- Standard stack: N/A — no packages/code this phase
- Architecture: HIGH — every mechanism (ADR scaffold, supersede convention, constitution-plane gate,
  docs-guard binding scope) verified against live file content and a live command run
- Pitfalls: HIGH — all four pitfalls are grounded in a specific file:line or a live command output,
  not inferred

**Research date:** 2026-07-26
**Valid until:** Effectively indefinite for the mechanics described (ADR convention, contract_guard
gating) since they are stable constitution-plane rules; re-verify only if a later phase (40+) is
observed to have changed `contract_guard.py`, `docs/doc-dependencies.toml`, or the CI workflow
before Phase 39 actually executes.
