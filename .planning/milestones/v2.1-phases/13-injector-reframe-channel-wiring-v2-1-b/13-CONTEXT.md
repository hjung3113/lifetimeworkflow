# Phase 13: Injector Reframe + Channel Wiring (v2.1 B) - Context

**Gathered:** 2026-07-15
**Status:** Ready for planning
**Source:** Operator ratification during `/gsd:plan-phase 13 --auto --chain` (discuss-phase skipped; open items surfaced by `13-RESEARCH.md` and ratified inline)

<domain>
## Phase Boundary

`inject.py` stops being a "distrust your own work" banner and becomes a **two-block** SessionStart
payload: (a) a full-body, never-dropped **working-agreements directive** composed from the active
`.memory/agreements/*` set, and (b) a separate **data-scoped provenance banner** that answers "which
artifact wins a data conflict". The activeContext pointer is reworded to a progress-log pointer and
carries a **verbatim** `updated:` freshness stamp written by `/checkpoint`.

Determinism (delete+regen byte-identical) and the ~4000-char budget survive both changes.

This phase consumes the `.memory/agreements/` channel scaffolded in Phase 12. It is the **read** half
of the channel; the **write** half (`/agree`, provenance lint) is Phase 14.

</domain>

<decisions>
## Implementation Decisions

### Cap + budget (ratifies open-Q4)

- **D-01**: The agreements block is capped at **N=6 entries / M=700 chars**. Derived from measured
  section sizes — base 3216 after the SC1 rewording (banner 133→316, pointer 117→200), leaving 784 of
  the 4000 budget; header 76 + 6×97 = 658 ≤ 700 → total 3917, **repo-map survives**. M=800 → 4017 →
  repo-map evicted every session. 700 is the arithmetic knee.
- **D-02**: `N` and `M` are **named module constants**, so re-ratification is a one-line edit.
- **D-03**: Overflow degrades **whole-block → pointer**. Never partial. **No count is interpolated into
  the pointer text** — a varying count would churn bytes and weaken the byte-identity guarantee.

### Priority order (SC1)

- **D-04**: Resulting order: `0` agreements directive (NEW, never-dropped, self-capped) → `1`
  data-provenance banner (reworded) → `2` drift → `3` contracts-index → `4` repo-map → `5` progress-log
  pointer (+ verbatim stamp).
- **D-05**: The never-drop tuple becomes `("agreements", "banner", "drift")`.
- **D-06**: Agreements-at-0 **retires the D-02 "banner-first" invariant** from the original injection
  contract. This is a consequence of the already-ratified SC1, not a new decision — but it must be
  recorded, not silently absorbed.

### Determinism (SC2) — the net must be BUILT, not "preserved"

- **D-07**: `inject.py:20-22` *claims* delete+regen byte-identity but **no test asserts it**. The
  safety net is **built first (Wave 1, before the reframe)** — modelled on
  `tools/docs_sync/tests/test_docs_sync_determinism.py:43`. `assemble()` is verified deterministic
  today, so the test lands green as a real net rather than a rubber stamp.
- **D-08**: `glob()` returns **filesystem order** — iteration is explicitly `sorted()`. Asserted by a
  test that creates fixtures in non-alphabetical order.
- **D-09**: `assemble()` gains an **`agreements_dir` parameter** (peer of `derived_dir`/`state_dir`,
  `inject.py:105-109`) as a testability prerequisite — the real active set is empty, so cap/order/overflow
  tests cannot be hermetic without it.

### Freshness stamp (MEM2-05 / SC3)

- **D-10**: `/checkpoint` writes `updated: <ISO-date>` into `.memory/state/activeContext.md` and
  `progress.md`. `assemble()` surfaces it **verbatim** — read from the file, never computed.
- **D-11**: **No wall-clock anywhere** — not in `assemble()`, not in the hook wrappers. Enforced by
  static tests against `inject.py`, `memory-inject.sh`, and `session-inject.ts`. Freshness is judged
  **agent-side** against the session date; no fixed threshold (Q6).
- **D-12**: Absent stamp (no frontmatter / missing key / missing file) degrades **gracefully with no
  raise**.
- **D-13**: `/checkpoint` is **prose-only** (`checkpoint.md:6`, no runnable) — the stamp mandate is an
  instruction edit verified structurally, which materially shrinks that task.

### Tight progress (SC4 / §7a)

- **D-14**: `checkpoint.md` mandates in-flight + remaining + a short last-N-done summary, and
  **forbids done-log accumulation** — git holds the full completed history.

### T-13-01 mitigations — all four ratified

- **D-15**: **Scope-limiting header** — the agreements block header states these are working-style
  directives that **never override `contracts/`, `docs/adr/`, or the gates**, so a planted agreement
  cannot self-authorize constitution writes.
- **D-16**: **Render title + one-line rule only.** The `provenance` field is **never rendered** —
  unbounded verbatim user text, the widest injection surface and the likeliest place a secret is pasted.
- **D-17**: **Fail-closed status filter** — composes iff `status == "active"`. Missing/malformed status
  is **excluded, not defaulted-in**. 3-layer exclusion also drops `_TEMPLATE.md` (which ships
  `status: active`) and `README.md`.
- **D-18**: **Add a no-secrets line to `.memory/agreements/README.md`** — parity with
  `.memory/state/activeContext.md:5`, which already carries one. Agreements are committed *and now
  injected verbatim*.
- **D-19**: Reads are **confined** to `agreements_dir`: non-recursive `glob("*.md")` (not `rglob`), no
  symlink follow, no traversal. Precedent: `tools/docs_sync` `_confine`, `golden_runner._confine`.

### Re-enable injection

- **D-20**: **Delete `.memory/.inject-disabled` in Phase 13's final plan, AFTER the reframe is green.**
  Also strip the obsolete `TEMPORARY DISABLE` block (`memory-inject.sh:22-31`) and the
  `activeContext.md:12-13` note. Both committed surfaces promise Phase 13 does this.

### Claude's Discretion

- Exact wording of the reworded `BANNER`, `ACTIVE_HEADER`, and the agreements block header — subject to
  the tested constraints (banned phrases absent; `DATA`/`contract`/`adr` present; scope-limit stated).
- Internal function decomposition within `inject.py`.
- Fixture shape beyond the required (≥1 active, ≥1 retired, `_TEMPLATE.md` decoy, no-frontmatter file,
  non-alphabetical creation order).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design source (authoritative)
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §7 — operator refinements; **supersedes §2/§5 on conflict**.
  7a tight progress · 7b per-guideline files · 7c reference-don't-duplicate ADRs · 7d Phase-16 web UI.
- `.planning/phases/13-injector-reframe-channel-wiring-v2-1-b/13-RESEARCH.md` — 948 lines; the
  18-site change enumeration, measured budget arithmetic, threat model.
- `.planning/phases/13-injector-reframe-channel-wiring-v2-1-b/13-VALIDATION.md` — the per-task
  verification map.

### Code under change
- `tools/memory_regen/inject.py` — the central 148-line file. One file ⇒ **one plan owns it**.
- `tools/memory_regen/tests/test_inject_assembler.py` — `:19-34`, `:71`, `:116-122` go **planned-red**.
- `.claude/hooks/memory-inject.sh` — `:22-31` disable block, `:40` `|| echo ''` silent-blank path.
- `harness/plugins/session-inject.ts` — opencode twin; authored, execution deferred.
- `harness/commands/checkpoint.md` — prose-only; `:6`.
- `.memory/state/activeContext.md`, `.memory/state/progress.md`, `.memory/agreements/`.

### Prior art / patterns
- `tools/docs_sync/tests/test_docs_sync_determinism.py:43` — the determinism-test model.
- `tools/memory_regen/frontmatter.py:40` — `parse_frontmatter`; reuse (handles CRLF).

### Rules
- root `AGENTS.md`; `harness/skills/two-plane-memory/SKILL.md`;
  `harness/skills/python-conventions/SKILL.md`; `harness/skills/gate-model/SKILL.md`.
- `docs/adr/0006-process-memory-channel-and-provenance-reframe.md` (landed, Phase 12).

</canonical_refs>

<specifics>
## Specific Ideas

- **Suite baseline is already red and that is CORRECT.** `uv run pytest tools/harness_emit` is
  **1 failed, 46 passed** on a clean tree *before any Phase 13 work*
  (`test_projected_tree_matches_committed_snapshot`, inherited from Phase 12's deferred re-emit).
  Phase 13's gate = `tools/memory_regen` + `tools/harness_lint` green, `harness_emit` **no worse than
  1 failed**.
- **`_TEMPLATE.md` ships `status: active`** — a naive glob injects `<One-line working-style or
  methodology rule.>` as a live directive. The active set today is **zero**, so every cap/order test
  needs `tmp_path` fixtures.
- **Decompose by file ownership, not by requirement** — `inject.py` is one file; two plans editing it
  would conflict.
- `_load_yaml` may return a bare date as `datetime.date` — **quote the stamp**; verify at task level.

</specifics>

<deferred>
## Deferred Ideas

- `/agree` write path + provenance/anti-invent lint → **Phase 14** (MEM2-04). T-13-01's *durable*
  mitigation is the lint; Phase 13 ships render-shape + cap + fail-closed filter instead.
- Re-emitting `.opencode/` + `.claude/`; **fixing the red emit snapshot** → **Phase 15** (MEM2-06).
  Do **not** regenerate the `.ambr` — that blesses Phase 12's un-emitted tree and steals Phase 15's gate.
- Local memory web UI + pointer index → **Phase 16** (MEM2-07).
- Authoring real agreement content → Phase 14 / operator. Agents **must not invent** entries (§2).
- Per-instance agreement overlays → v2 (MEM2-F1).
- Wall-clock staleness threshold → **never** (Q6, explicitly out of scope).
- Promoting agreements to the constitution plane → **never** (Q1).

</deferred>

---

*Phase: 13-injector-reframe-channel-wiring-v2-1-b*
*Context gathered: 2026-07-15 via operator ratification (plan-phase inline)*
