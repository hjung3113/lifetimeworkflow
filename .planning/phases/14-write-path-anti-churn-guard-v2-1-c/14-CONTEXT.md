# Phase 14: Write Path + Anti-Churn Guard (v2.1 C) - Context

**Gathered:** 2026-07-16
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; every choice logged in `14-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

Phase 13 shipped the **read half** of the `.memory/agreements/` PROCESS channel — `inject.py`
composes active agreements at priority-0 as directives the agent is told to honor. Phase 14 ships
the **write half**: a dedicated `/agree` command that is the sanctioned and only way an agreement is
added or retired, plus a `tools/harness_lint` provenance guard that fails when an entry lacks a
well-formed origin stamp.

**Plan this as a security control, not a formatting nicety.** Phase 13 converted a passive committed
data directory into an executable priority-0 instruction channel that is writable and *not*
path-denied (the accepted Q1 trade-off). Phase 13's defenses — title+rule-only render, fail-closed
status filter, N=6/M=700 cap, scope-limiting header (D-15..D-19) — are explicitly **interim**. This
phase is T-13-01's durable mitigation.

**In scope:** `/agree` add + retire write path; provenance/status/added frontmatter lint; source-side
command authoring.
**Out of scope:** emit round-trip to `.opencode/`/`.claude/` (Phase 15); `Related:` pointer
resolution (Phase 16 / MEM2-07); per-instance agreement overlays.

</domain>

<decisions>
## Implementation Decisions

### Provenance stamp shape — what "well-formed" means mechanically

- **D-01:** Well-formed = a **structural regex over frontmatter**, mirroring `_TEMPLATE.md` exactly
  and nothing more: `status:` ∈ {`active`, `retired`}; `added:` an ISO `YYYY-MM-DD`; `provenance:`
  matching `^added because \S` (the prefix plus a non-empty tail). No crypto, no signatures, no
  attestation — those would be theater against the threat model in D-03.

- **D-02:** **`added:` must be a QUOTED string, and the lint must require `str`.** `_TEMPLATE.md:3`
  currently ships `added: YYYY-MM-DD` **unquoted**, which YAML parses into a `datetime.date` object,
  not a string. This is the *same latent defect* Phase 13 hit and settled on the `updated:` stamp
  (13-01, open-question A6 — resolved by quoting so it round-trips as `str`). Fix `_TEMPLATE.md` to
  `added: "YYYY-MM-DD"` in this phase and make the lint assert `isinstance(value, str)`; a bare date
  object must FAIL, not be silently coerced. Precedent is binding — do not re-litigate it.

### Lint delivery surface

- **D-03:** **Honesty decision — do not oversell this phase. The lint enforces SHAPE, not TRUTH.**
  An agent can write a *well-formed but fabricated* provenance and the lint will pass it. ROADMAP
  SC2's phrasing — "so agents cannot auto-invent entries" — **overclaims**, and MEM2-04 inherits the
  same wording. What the guard actually buys: (a) an **omitted or malformed** stamp fails loud; (b)
  inventing an entry now requires *deliberately fabricating a quote attributed to the user*, which
  is a visible, auditable act in the git diff rather than a silent accident. This is the identical
  trust model ADR-0007 already accepted for `HARNESS_DEV_BYPASS` ("the guard is accident-prevention,
  not a sandbox"). Plan to that honest claim. **Do NOT build hook theater that pretends to enforce
  truth** — a PreToolUse hook adds no security here for exactly this reason.

- **D-04:** The lint ships as a **runnable module** `tools/harness_lint/provenance.py` exposing a
  pure `check`/`Violation` API plus a `main()` that exits 1 on violation — cloning the
  `tools/polyglot_lint/lint.py` shape (`Violation`, `lint_file`, `main`) verbatim rather than
  inventing a new one. Wire it into the `/lint` command so it is caught locally, and add a pytest
  test under `tools/harness_lint/tests/` so CI's `core-suite` is the non-bypassable gate. Both, not
  either — `/lint` is the fast local signal, pytest is the merge gate.

- **D-05:** The lint's file-selection predicate — the 3-layer fail-closed exclusion of `_`-prefixed
  files (`_TEMPLATE.md`), `README.md`, and non-`active` status — **MUST be shared with `inject.py`,
  not re-derived.** Two copies of this predicate will drift, and a drift here means the lint and the
  injector disagree about what an agreement *is*. Extract the existing filter from `inject.py` into
  one importable helper and have both call it. This is the D-02-style "single rule, reused" pattern
  the harness already applies to `normalize.core`. If extraction proves invasive, the fallback is a
  test asserting the two predicates agree over a shared fixture corpus — never two hand-kept copies.

- **D-06:** Reads are confined exactly as Phase 13's D-19: non-recursive `glob("*.md")` (never
  `rglob`), no symlink follow, confined to `agreements_dir`. Precedent: `tools/docs_sync._confine`,
  `golden_runner._confine`.

### `/agree` refusal contract

- **D-07:** **`/agree` refuses rather than inventing a stamp.** It requires an explicit
  `--because "<verbatim user feedback>"` argument; missing, empty, or whitespace-only → refuse with
  a dedicated exception and **CLI exit 3**, mirroring `tools/golden_runner/approve.py`'s
  `GoldenApprovalRefused` shape verbatim (the blank/whitespace rule mirrors the
  `GOLDEN_APPROVE_HUMAN` and `HARNESS_DEV_BYPASS` conventions). The `--because` value becomes the
  provenance tail, so the stamp cannot be *forgotten* — only deliberately forged, which is D-03's
  accepted residual risk.

- **D-08:** **`/agree` does NOT require `GOLDEN_APPROVE_HUMAN`.** Agreements are deliberately
  *not* constitution plane (Q1: committed-but-writable). Requiring the human token would reintroduce
  exactly the capture friction §2 rejected — "the trigger is a user typing feedback mid-work" — and
  would mislabel a working-style note as constitution ratification. `--because` is the gate; the
  user directing the write *is* the ratification.

- **D-09:** Retire = **flip `status:` to `retired` in place; never delete** (locked by Q5/§7b).
  `/agree --retire <slug>` performs the flip only. No file removal, no history rewrite — the
  retired entry stays as the audit trail, and `inject.py`'s fail-closed filter already excludes it.

### Emit boundary

- **D-10:** **Phase 14 is SOURCE-ONLY. Do not run the emitter.** Author
  `harness/commands/agree.md`; do **not** touch `.opencode/` or `.claude/`. This is load-bearing,
  not stylistic: `tools/harness_emit/tests/test_coexist.py:53-54` asserts **exactly 19** emitted
  commands in each runtime tree. Leaving the trees alone keeps that test green; emitting `/agree`
  makes it 20 and turns a currently-passing test red — pushing `harness_emit` past its sanctioned
  "no worse than 1 failed" baseline. Phase 15 owns the round-trip and owes the 19→20 bump.
  Precedent: Phase 10 (10-01/10-02 source-only; 10-03 emit).

- **D-11:** **`EXPECTED_COMMANDS` does not exist — do not create it to satisfy the SC's wording.**
  ROADMAP SC3 and MEM2-04 both name a constant that is absent from the codebase. The real
  touchpoints are: `tools/harness_lint/tests/test_commands.py`, which is **glob-driven** and
  therefore auto-covers `harness/commands/agree.md` with zero edits; and the hard command count in
  `test_coexist.py` (Phase 15, per D-10). SC3 is satisfied by authoring the command file and letting
  the existing glob lint pick it up. Inventing an `EXPECTED_COMMANDS` frozenset purely to match a
  mis-worded criterion would add a hand-maintained list the glob design deliberately avoids.

### ADR-0006 seed discrepancy

- **D-12:** `docs/adr/0006-*.md:92-93` claims the tier ships "`_TEMPLATE.md` + README + **one
  committed seed**". **There is no seed and there never was** (`96b8db2` added exactly the two
  files; `git ls-files .memory/agreements/` confirms). Resolve with a dated **`## Errata` note
  appended to ADR-0006** — *not* by shipping a seed, *not* by superseding.
  - **Not a seed:** fabricating an agreement to retroactively make the ADR true would require
    inventing user feedback — the exact T-13-01 / anti-invent violation this phase exists to
    prevent. The phase must not open by committing the sin it closes.
  - **Not ADR-0008:** supersede is the instrument for *changing a decision*
    (`docs/adr/README.md:16`). No decision changed; a factual claim about what shipped was wrong.
  - **Errata is defensible under append-only:** `docs/adr/README.md:14` forbids editing *decision
    content*. An appended, dated `## Errata` section leaves every decision word untouched.
  - Landing it is a constitution write → use the `HARNESS_DEV_BYPASS` path (ADR-0007) or raw shell.
    **Never forge `GOLDEN_APPROVE_HUMAN`.**

- **D-13:** The empty active set is **correct**, and the errata must say so plainly, so a future
  agent reading 0006 does not "repair" the dir by inventing an entry.

### Amendments from research (2026-07-16, post-`14-RESEARCH.md`)

Research contradicted three locked decisions. Each was **independently re-verified** before amending —
this is the adversarial pass working, not drift. The amendments below **supersede** the text above
where they conflict.

- **D-02:** **MECHANISM CORRECTED (supersedes the D-02 above), decision unchanged.** D-02 claimed `_TEMPLATE.md:3`'s
  `added: YYYY-MM-DD` parses to a `datetime.date`. **It does not** — verified live:
  `YYYY-MM-DD` is not a parseable date, so it yields `str` today. The hazard is real but *latent*:
  `added: 2026-07-16` (unquoted, what `/agree` will actually write) → `datetime.date`;
  `added: "2026-07-16"` → `str`. So the fix stands (quote the template, lint requires `str`), but
  the reason is "the template teaches a shape that becomes a date object once a real date is
  substituted" — not "the template is broken today." **Ordering constraint:** the `isinstance(str)`
  check MUST precede the regex, or the lint raises `TypeError` on a `date` object instead of failing
  cleanly. No `import datetime` anywhere (see D-17).

- **D-14:** **Resolves research OQ-1 — share LAYERS 1–4 ONLY; do NOT share the `status` filter.**
  Research found the `inject.py` predicate is **five layers, not three** (`inject.py:90-115`):
  L1 sorted `glob`, L2 `_`/README/symlink exclusion, L3 confine, L4 fail-closed parse — all
  *"what is an agreement file"* — plus **L5 `status != "active"`, which is the injector's RENDER
  POLICY, not identity.** Sharing L5 would make **D-01's own `status ∈ {active,retired}` rule
  unenforceable**: a `status: pending` typo would be skipped by the filter before the lint could flag
  it, and retired entries would go unlinted forever. Share L1–L4; let each caller apply its own status
  policy. Cost today: zero.

- **D-15:** **YAML-serialize `--because`; never f-string it into the template.** No prior decision
  covered this. A `"` or a newline in the user's verbatim feedback breaks the quoted scalar and can
  **forge sibling frontmatter keys** (e.g. inject `status: active` into a retired entry). Use a real
  YAML serializer for the `provenance:` value. This is a genuine injection surface on the write path,
  which is exactly what this phase exists to harden — do not treat it as cosmetic.

- **D-16:** **ROADMAP SC2's "follows the existing `stale-derived` gate pattern (regenerate → verify)"
  is a CATEGORY ERROR; D-04 wins.** The stale-derived gate regenerates *derived* artifacts and diffs
  them. Agreements are **never regenerated** (`.memory/agreements/README.md:4-5`) — there is nothing
  to regenerate, so the pattern cannot apply. D-04's runnable-lint + pytest shape is the correct
  reading of SC2's intent. Flag this so `/verify-work` does not fail the phase on SC2's literal
  wording. (Third mis-worded criterion in this phase's own source, after `EXPECTED_COMMANDS` (D-11)
  and "cannot auto-invent" (D-03) — treat ROADMAP SC wording as intent, not spec.)

- **D-17:** **Extraction moves code out from under a LIVE gate; widen it in the SAME task.**
  `tools/memory_regen/tests/test_inject_determinism.py:70-75` reads **`inject.py` as TEXT** and scans
  for 5 wall-clock tokens. Moving the predicate into `tools/harness_lint/agreements.py` silently
  removes it from that gate's scope. The extraction task MUST widen the no-wall-clock gate to cover
  the new module in the same commit — otherwise the phase quietly loses a Phase-13 guarantee. Also:
  `_agreements_block`'s name/signature is called directly by **7 tests** — extraction must preserve
  it or update all 7 deliberately.

- **D-18:** **Import direction is SETTLED: `memory_regen` → `harness_lint`.** `inject.py:15` already
  does `from tools.harness_lint import parse_frontmatter`, so putting the predicate in
  `tools/harness_lint/agreements.py` adds **zero new edges**. The reverse direction cycles AND drags
  `contract_drift` (`inject.py:14`) into a lint. Import the submodule directly — no `__init__.py`
  change, no PEP-562 collection hazard. This resolves D-05's "extraction vs fixture-parity" question
  in favor of **extraction**.

- **D-19:** **`/agree`'s home is a NEW `tools/agree/` member.** `tools/memory_regen` is **forbidden** by
  the tier's own contract (`.memory/agreements/README.md:4-5`: "never written by
  `tools/memory_regen`"). A new `tools/agree/` is auto-enrolled by the existing `tools/*` workspace
  glob; measured lockfile cost = **4 deterministic lines, zero resolution, zero guard tests**.
  Phase 2's D-01 `uv.lock` warning is about *external dependency* contention and does not apply.

- **D-20:** **`secret_scan` will fire on plans that quote `approve.py:57` verbatim.** The researcher's
  first write of `14-RESEARCH.md` was **denied** by `secret_scan` because it quoted that line and
  matched `token = <16+ chars>` (`secret_scan.py:47`). It reworded rather than bypassed — correct.
  Downstream plans/summaries quoting `approve.py`'s token logic will hit the same deny. **Reword; do
  not bypass, and do not weaken `secret_scan` to accommodate a doc.** (It is also a live, unplanned
  demonstration of D-03's shape-not-truth model.)

### Claude's Discretion

- Module/file naming, argument parser layout, and test decomposition within the shapes fixed above.
- ~~Whether the shared predicate (D-05) lands as an extraction or a fixture-parity test~~ —
  **resolved by D-18: extraction**, subject to D-17's gate-widening obligation.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Authoritative design source
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §7 — **AUTHORITATIVE; supersedes §2/§5 on conflict.**
  §7b (one file per guideline, essence only) and §7c (link ADRs, never restate) drive this phase.
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §2 "Properties of the PROCESS channel" — property 2
  ("an agent **must not invent** entries") is the requirement D-03 scopes honestly.
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §6 Q1/Q2 + "Location & gating" — why the channel is
  committed-but-writable and why provenance-lint (not a write-lock) is the guard.
- `.planning/REQUIREMENTS.md` — MEM2-04 is this phase's requirement (line 24).

### Ratified decisions
- `docs/adr/0006-process-memory-channel-and-provenance-reframe.md` — the four-plane model + the
  agreements tier. **Carries the D-12 seed error.**
- `docs/adr/0007-constitution-gate-dev-enforce-decoupling.md` — `HARNESS_DEV_BYPASS`; the landing
  path for D-12's errata, and the precedent for D-03's honest trust model.
- `docs/adr/README.md` §13-19 — append-only / supersede-don't-edit, the constraint D-12 reasons from.

### Inherited threat + decision register
- `.planning/phases/13-injector-reframe-channel-wiring-v2-1-b/13-RESEARCH.md` § Security Domain —
  T-13-01..06. **T-13-01 line 766 is this phase's reason to exist**; line 783 explicitly assigns the
  provenance lint to Phase 14.
- `.planning/phases/13-injector-reframe-channel-wiring-v2-1-b/13-CONTEXT.md` D-15..D-19 — the interim
  mitigations this phase durably replaces.
- `.planning/phases/13-injector-reframe-channel-wiring-v2-1-b/.continue-here.md` — **BLOCKING
  CONSTRAINTS**, especially the red-`harness_emit` trap (see `<code_context>`).

### Channel + surfaces
- `.memory/agreements/README.md` — the tier's own contract (frontmatter requirements, no-secrets
  line, "the `/agree` write path and provenance lint arrive in Phase 14").
- `.memory/agreements/_TEMPLATE.md` — the shape D-01 regexes against; **carries the D-02 unquoted-date defect**.
- `.memory/README.md` — the four-plane declaration (PROCESS row, line 16).

### Code precedents to clone (do not invent new shapes)
- `tools/golden_runner/approve.py` — `GoldenApprovalRefused` + exit-3 refusal; the D-07 model.
- `tools/polyglot_lint/lint.py` — `Violation` / `lint_file` / `main` runnable-lint shape; the D-04 model.
- `tools/memory_regen/inject.py` — the fail-closed agreements filter D-05 must share, and the
  byte-identity/no-wall-clock invariants any change here must preserve.
- `tools/harness_lint/frontmatter.py` — `parse_frontmatter`; the shared parser to reuse, not re-roll.
- `tools/docs_sync/generate.py` `_confine` — the confinement precedent for D-06.
- `harness/commands/golden-approve.md`, `harness/commands/adr.md` — command-authoring precedents.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/harness_lint/frontmatter.py::parse_frontmatter` — the shared frontmatter parser; the lint
  must delegate to it rather than slicing `---` fences itself (the convention `test_commands.py`
  already follows).
- `tools/polyglot_lint/lint.py` — a complete runnable-lint template: `Violation` dataclass,
  `lint_file`, `main` returning exit 1. Clone the shape.
- `tools/golden_runner/approve.py` — a complete refusal template: a dedicated exception → exit 3,
  with the blank/whitespace-is-not-a-signal rule already implemented.
- `tools/memory_regen/inject.py` — already contains the exact 3-layer exclusion predicate D-05 needs.

### Established Patterns
- **Lints are pytest tests.** `tools/harness_lint/` holds no runnable lint today — only `caps.py`,
  `frontmatter.py`, and a `tests/` tree. D-04 adds the first runnable module there; follow
  `polyglot_lint`'s layout, not a new one.
- **Glob-driven gates over hand-kept lists.** `test_commands.py` discovers `harness/commands/*.md`
  so new commands need no test edit (D-11 depends on this).
- **Blank/whitespace is never a signal.** `GOLDEN_APPROVE_HUMAN`, `HARNESS_DEV_BYPASS`, and
  `approve.py` all treat empty/blank as absent. D-07 must mirror it.
- **Constitution writes need the dev-bypass path, never a forged token** (ADR-0007).

### Integration Points
- `/lint` command macro ← the new runnable provenance lint (D-04).
- `tools/harness_lint/tests/` ← the CI gate via `core-suite`.
- `inject.py`'s filter ← the shared predicate (D-05). Touching `inject.py` means **re-verifying
  Phase 13's byte-identity determinism test and the no-wall-clock static gate** — both are live and
  must stay green.
- `harness/commands/agree.md` ← auto-covered by the glob lint; **NOT** emitted (D-10).

### ⚠ BLOCKING CONSTRAINT inherited from Phase 13 — carried into every plan
`uv run pytest tools/harness_emit` is **exactly 1 failed / 46 passed**
(`test_projected_tree_matches_committed_snapshot`) and **that is CORRECT**. It is Phase 12/13's
deferred re-emit debt and **belongs to Phase 15**. Confirmed live this session: full `uv run pytest`
= **1 failed / 620 passed**, that one failure only.

- **Never run `--snapshot-update` on `tools/harness_emit/tests/__snapshots__/`.** Regenerating that
  `.ambr` blesses the un-emitted tree and **steals Phase 15's gate** — the phase would then "pass"
  while never verifying the round-trip it exists to verify.
- Phase 14's green gate: `tools/memory_regen` + `tools/harness_lint` all pass, with `harness_emit`
  **no worse than 1 failed**.
- CI `core-suite` + `emit-drift` are red on PR #3 for this same single reason. Do not "fix" them.

### ⚠ Agents must never author `.memory/agreements/*` content
Agreements are written **only** on explicit user feedback (§2 property 2). The active set is
legitimately **empty** today — that is correct behavior, not a bug (and see D-12/D-13). To exercise
the lint or the injector, use `tmp_path` fixtures and the `assemble(agreements_dir=...)` parameter.
**Never write to the real dir to "test" it.**

</code_context>

<specifics>
## Specific Ideas

- Mirror `approve.py`'s refusal *wording style* too: a `REFUSED:` prefix naming the missing signal
  and the path to supply it. The refusal message is a teaching surface, not just an error.
- The `/agree` command description must carry a routing trigger ("Use when…") — `test_commands.py`
  enforces `_ROUTING_TRIGGERS` on every command's description.
- Keep the agreement body shape exactly as `_TEMPLATE.md` documents (title + one-line rule +
  `Related:`); `/agree` fills the template, it does not invent a new layout.

</specifics>

<deferred>
## Deferred Ideas

- **Emit round-trip of `/agree` + the reworded Phase 12/13 skills to both runtimes** → **Phase 15**
  (MEM2-06). Includes the `test_coexist.py` 19→20 command-count bump and settling the red
  `harness_emit` snapshot. Explicitly NOT this phase (D-10).
- **`Related:` pointer target resolution / referential integrity** → **Phase 16** (MEM2-07). The
  local memory web UI is the pointer-aware surface; §7d assigns "what points to this item" there.
  This phase's lint checks frontmatter only, never link targets.
- **Lint checking `Related:` *presence* in the body** → deferred with the above; ROADMAP SC2 scopes
  the guard to the provenance/origin stamp, and widening it here is scope creep.
- **Per-instance agreement overlays** (`examples/*` overlays à la `project.toml` / ADR-0003) →
  out of scope; §6 Q3's MVP answer is one global core set. Revisit only if an instance needs it.
- **A PreToolUse hook enforcing provenance at write time** → deliberately NOT deferred-for-later but
  **rejected** (D-03): it cannot enforce truth, so it would be security theater at real cost.

</deferred>

---

*Phase: 14-write-path-anti-churn-guard-v2-1-c*
*Context gathered: 2026-07-16*
