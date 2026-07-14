# Requirements: v2.1 MEM2 — Process Memory & Provenance Reframe

**Defined:** 2026-07-14
**Core Value:** 계약(contracts)을 단일 정본으로 두고, 폴리글랏 표현차·전환 리스크를 하네스가 자동으로 강제·검증한다 — 이 강제 구조가 도메인·언어에 묶이지 않고 재사용된다.
**Design source:** `.planning/MEMORY-UPGRADE-PROPOSAL.md` (§7 operator refinements are AUTHORITATIVE, supersede §2/§5 on conflict).
**Kickoff decisions (2026-07-14):** Q1=committed-but-writable · Q2=dedicated `/agree` · Q3=per-guideline files · Q4=capped full-body · Q5=retire via per-file status · Q6=agent-side freshness (no fixed threshold).

## v1 Requirements

Requirements for milestone v2.1. Each maps to exactly one roadmap phase (phases 12+, numbering continued).

### Process Channel (the new 4th memory tier)

- [ ] **MEM2-01**: An agent (or user) can record a working-agreement as a **per-guideline file** `.memory/agreements/<slug>.md` (§7b) carrying a defined entry shape — title, one-line rule, `status` (active/retired), and a provenance stamp ("added because <user feedback>", added-date). The channel is committed, user-authored, and curated (added on feedback, retired explicitly); it is a committed human-authored tier like `state/`, NOT a regenerated derived artifact. Entries **link** to ADRs/Key-Decisions and never restate project decisions (§7c).

### Provenance Reframe (scope "provisional/verify" to DATA only)

- [ ] **MEM2-02**: At SessionStart the injector (`tools/memory_regen/inject.py`) emits **two distinct blocks**: (a) a full-body **working-agreements directive** section (new priority-0, never-dropped, honored as a directive) composed from the active `.memory/agreements/*` files, **capped** (N entries / M chars; overflow degrades to a pointer per Q4) so it cannot crowd out drift+index; and (b) a **data-scoped** provenance banner that reads as "which artifact wins a data conflict" — NOT "distrust/retract your own grounded work". The activeContext pointer is reworded to a progress-log pointer. `assemble()` determinism (`inject.py:20-22`, delete+regen byte-identical) and the ~4000-char budget (`inject.py:105`) are preserved.

- [ ] **MEM2-03**: The distrust framing is reworded to *data authority* (not behavior) everywhere it is echoed: `.memory/README.md`, `.memory/state/activeContext.md`, `.memory/state/progress.md`, `harness/skills/two-plane-memory/SKILL.md`, and `AGENTS.md`. After the change, no session-start surface tells an agent to "confirm before trusting" its own grounded working context.

### Write Path & Guards

- [ ] **MEM2-04**: A dedicated **`/agree`** command appends or retires a working-agreement **only in response to explicit user feedback** (retire = flip the file's `status` to retired, per Q5/§7b). A `tools/harness_lint` check enforces that every entry carries a provenance/origin stamp and that agents cannot auto-invent unsolicited entries (provenance is present + well-formed). `/agree` is added to `EXPECTED_COMMANDS`.

- [ ] **MEM2-05**: Progress state (`.memory/state/activeContext.md`, `progress.md`) carries an `updated: <ISO-date>` stamp written by `/checkpoint`. `assemble()` surfaces the stamp **verbatim** (no wall-clock inside `assemble()`, preserving determinism); freshness is judged **agent-side** against the session date (no fixed threshold, no hook-wrapper wall-clock code, per Q6). Progress stays tight by design — in-flight + remaining + a short last-N-done summary; full completed history lives in git, not memory (§7a).

### ADR & Emit Round-Trip

- [ ] **MEM2-06**: The model change is recorded as **ADR-0006** (append-only, next number, authored via the human-ratified constitution path — an agent Write to `docs/adr/` is correctly denied). Every new/changed agent, skill, and command (the `/agree` command, updated skills, updated `AGENTS.md` managed block) round-trips through the Phase-7 emitter (`tools/harness_emit`) to **both** runtimes (`.opencode/` + `.claude/`) with **no model id**; emit-drift is clean, `EXPECTED_COMMANDS`/counts updated, and GEN-04 core→example independence stays green.

### Memory Management Tooling

- [ ] **MEM2-07**: A lightweight **local** web tool lets a user view/edit/retire memory items (progress + per-guideline agreements) with **pointer-aware** UX: it surfaces "what points to this item" (docs/skills/`inject.py` pointers that reference memory files) and keeps references consistent on edit/retire, so memory hygiene is systematized, not manual. Scope: local only (no external network, no auth surface); operates on the committed memory files + a machine-built **derived pointer-index** (treated like other derived artifacts — generated, not hand-maintained).

## v2 Requirements

Deferred to future milestones. Tracked but not in this roadmap.

### Process Channel

- **MEM2-F1**: Per-instance agreement overlays (like `project.toml` overlays, ADR-0003) for `examples/*` — open-Q3 deferred; MVP is one global core channel (§6 Q3).

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Promoting `.memory/agreements/` into the constitution plane (path-deny + CODEOWNERS) | Q1 decided committed-but-writable; provenance-lint is the guard. Constitution-plane gating costs unacceptable capture friction (token dance per capture). Revisit only if tamper-resistance becomes a hard requirement. |
| Restating project decisions in the PROCESS channel | §7c — decisions live in `docs/adr/` + PROJECT.md `## Key Decisions`; the channel links, never duplicates (single-source-of-truth). |
| Ever-growing done-log in progress memory | §7a — full completed history is git commits; progress memory stays tiny (in-flight + remaining + last-N-done). Retires the bloated `.planning/STATE.md` pattern. |
| Hook-wrapper / `assemble()` wall-clock staleness comparison | Q6 decided agent-side freshness with no fixed threshold; determinism forbids wall-clock in `assemble()`. |
| Remote/hosted or authenticated memory UI | MEM2-07 is local-only, read-mostly-then-edit; no network or auth surface. |

## Traceability

Which phases cover which requirements. **Filled by the roadmapper during roadmap creation.**

| Requirement | Phase | Status |
|-------------|-------|--------|
| MEM2-01 | — | Pending |
| MEM2-02 | — | Pending |
| MEM2-03 | — | Pending |
| MEM2-04 | — | Pending |
| MEM2-05 | — | Pending |
| MEM2-06 | — | Pending |
| MEM2-07 | — | Pending |

**Coverage:**
- v1 requirements: 7 total (MEM2-01..07)
- Mapped to phases: 0 (roadmapper pending)
- Unmapped: 7 ⚠️

**Suggested phase breakdown (from proposal §5 + §7d; roadmapper to confirm/refine):**
- Phase A — Model + ADR + doc reframe: MEM2-01, MEM2-03, ADR from MEM2-06
- Phase B — Injector reframe + channel wiring: MEM2-02, MEM2-05
- Phase C — Write path + anti-churn guard: MEM2-04
- Phase D — Emit round-trip + gates: MEM2-06 (emit portion)
- Phase E — Local memory web UI: MEM2-07

---
*Requirements defined: 2026-07-14 for milestone v2.1 (MEM2)*
*Last updated: 2026-07-14 at milestone start*
