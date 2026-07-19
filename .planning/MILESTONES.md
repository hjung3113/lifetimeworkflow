# Milestones

## v2.2 Adaptive Task Control Plane (Shipped: 2026-07-19)

**Phases completed:** 6 phases (18–23), 21 plans

**Key accomplishments:**

- Ratified the task-packet contract set (TASK/STATE/EVIDENCE/HANDOFF JSON Schema Draft 2020-12) and the `.workflow/tasks/<task-id>/` instance slot, independent of `.memory/state/`, registered in the contract-drift hash gate (Phase 18).
- Deterministic 7-axis risk router (`harness/risk-policy.toml` + `tools/risk_router`) mapping to FAST/STANDARD/STRICT/CONTROLLED lanes with escalate-only instance overlay and auto-promotion reason codes, plus `/intake` (Phase 19).
- Atomic state manager (`tools/task_control` — flock + revision CAS, interrupted-write recovery), phase-oriented required-artifact gate, and fail-closed `/phase-gate` + `context-attestation.json` (Phase 20).
- Forgery-detecting evidence adapters (`tools/evidence`) that wrap the existing gates (record argv/exit/hash/status, never turn SKIPPED into PASSED), with secret/PII refusal and a HEAD-committed evidence+approval trust root at COMPLETE (Phase 21).
- Immutable HANDOFF snapshot + gated fresh-session resume (`tools/handoff`) with a revision-bound `resume_gate` PreToolUse hook (advance-only re-stamp on sanctioned transitions) (Phase 22).
- Human-ratified domain-neutral lifecycle fixtures (20, five per lane) + stress/negative suite, CI fan-in, `docs/how-to/task-lifecycle.md`, and structural ADR-0008 (Accepted) — 904 tests green, pushed to origin (Phase 23).

**Scoping:** sol-vs-fable debate panel, codex sol authored the merged design; locked human decisions A=`.workflow/tasks/`, B=6 phases. Deferred: signed external evidence attestation (P21 D-10), TCP-F01..F05, STRICT-rollback policy.

---

## v2.1 MEM2 — Process Memory & Provenance Reframe (Shipped: 2026-07-18)

**Phases completed:** 5 phases, 19 plans, 42 tasks

**Key accomplishments:**

- Scaffolded the committed, human-authored `.memory/agreements/` PROCESS tier (per-guideline `<slug>.md`: title + one-line rule + `status` + provenance stamp), reworded the distrust framing to *data authority* across all five echo surfaces (`.memory/README.md`, both state files, `two-plane-memory` SKILL, `AGENTS.md`), and ratified the memory-model change as ADR-0006 via the human-gated constitution path — an agent Write to `docs/adr/` is correctly denied; CODEOWNERS ratifies (Phase 12).
- Reframed the SessionStart injector into two distinct blocks — a never-dropped **priority-0** full-body working-agreements directive (capped, overflow→pointer) plus a **data-scoped** provenance banner ("which artifact wins a data conflict", not "distrust your own work") — and surfaced a **verbatim** `/checkpoint`-written `updated:` freshness stamp, all with `assemble()` determinism (delete+regen byte-identical, ≤4000 chars, no wall-clock) preserved (Phase 13).
- Added the sanctioned `/agree` write path — a zero-dep `tools/agree/` refusal-first writer that appends/retires an agreement **only on explicit user feedback** — backed by a `tools/harness_lint` provenance/anti-invent guard that fails any entry lacking a well-formed origin stamp, so agents cannot self-invent unsolicited entries (Phase 14).
- Round-tripped the full surface delta (`/agree` + updated skills + the `AGENTS.md` managed block) through the Phase-7 emitter to **both** runtimes (84 artifacts, zero emitter code change), settling the carried Phase-12/13 re-emit debt — emit-drift clean, **no model id**, GEN-04 core→example green, full suite passing (Phase 15).
- Shipped a **local, no-network, no-auth** memory web UI (127.0.0.1-only stdlib server, single inlined zero-asset page) over a machine-built **DERIVED pointer-index**, with **surface-and-confirm** referential integrity that reconciles pointers on edit/retire; browser round-trip verified live 5/5 (Phase 16).

---

## v2.0 Long-Horizon (Shipped: 2026-07-14)

**Phases completed:** 3 phases, 11 plans, 16 tasks

**Key accomplishments:**

- 1. [TDD sequencing] Prune test authored in Task 1 RED, not Task 2
- Read-mostly `curator` persona (edit+bash allow, write deny, no model id) plus `/refresh-memory` and a `/verify-work` freshness step, all round-tripped once through the Phase-7 emitter to both runtimes with GEN-04 green.
- Non-bypassable `stale-derived` CI job that regenerates docs/reference + .memory/derived/contracts-index.md and fails on any diff via the untracked-safe `git add -A` + `git diff --cached --exit-code` primitive, proven by a structural + negative-control test — completing MAINT-02.
- Authored the ECON-01/ECON-02 substrate — a fan-out-synthesize skill (decompose → dispatch N read-only explorer subtasks → recover schema-bounded citation-bearing summaries → orchestrator synthesizes), its co-located domain-neutral Draft 2020-12 return-contract JSON Schema, a thin /fan-out-synthesize command routing to the orchestrator, the anti-sprawl enumeration entry, and the Wave-0 structural gate.
- A dedicated `context-budget` skill (fan out vs work inline) wired at both named integration points — the orchestrator routing table/intake and `/orient` read-order — alongside the `fan-out-synthesize` substrate, so the delegate-vs-inline routing decision is a first-class, observable step (ECON-03).
- Round-tripped the fan-out-synthesize + context-budget surface through the Phase-7 emitter to both runtimes byte-identically, regenerated opencode.json/emit-manifest/AGENTS.md, and closed Phase 10 with a green gate (537 passed, GEN-04 green, emit-drift clean, 11 skills / 5 personas).
- 1. [Rule 3 - Blocking] Added tests/conftest.py + tests/__init__.py to the new uv member
- A repo:stage edge is proven to cross a repo boundary in the workspace layer, and a generalized GEN-04 guard proves the core references no workspace member with a key-scoped pointer exemption and live negative controls.
- The contract-first safety net now spans repo boundaries: cross-repo drift iterates each member's own baseline (no merge) and resolves every edge's contract in its producer, the golden runner resolves an edge-spanning case under a member root with a widened-not-removed `_confine` allowlist, and a separate `workspace` CI job in `gate.needs` enforces both (MREPO-03).
- Workspace-wide analysis is prose-wired to fan out one read-only worker per member repo with

workspace-level synthesis (no single context holds every repo), reusing the Phase-10 fan-out
substrate with NO new surface, and round-tripped byte-identical to both runtimes — closing out
Phase 11.

---
