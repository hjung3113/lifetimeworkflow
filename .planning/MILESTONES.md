# Milestones

## v2.4 Gate Right-Sizing, Carried Debt, Lane Discipline (Closed PARTIAL: 2026-07-26)

**Phases:** 30–38 planned; **34, 35, 36, 37 shipped** (12 plans), **38 landed as code** (`bc9a6d9`,
never formalized as a phase), **30 partial** (contract pair only, `27ee704`), **31, 32, 33 cut**.

**Delivered:** `ruff check` became a required CI gate behind a ratcheting baseline with the vendored
tree excluded; the three carried-debt items reached honest dispositions (phase-27 verification authored
with an at-closeout honesty stamp, compile-the-graph-once decided, `DEF-05-02-1` proven already fixed
and the stale *record* corrected); the four discipline skills plus a STRICT+ adversarial panel became
executable lane requirements; capability-neutral routing with an enforced allowlist plus skill
`registry.lock` and its CI adapter landed. Suite at close: 1683 passed / 8 snapshots.

**Why it closed partial.** Mid-milestone the owner found the in-session gate wall over-regulated: it
slowed the dev loop and deadlocked the session twice. ADR-0011 re-pivoted Theme A from *harden the
denies* to **right-size them — dev-light, CI-strong**, cutting SEAL-02/03, and phase 38 shipped that as
code. The deeper diagnosis in ADR-0011's own Context — *every milestone's subject matter **is** gate
machinery, so "maintain consistency" drifted into "add more gates"* — then outgrew the milestone: the
remaining Theme A work (30's drift test, 33's ratification record) was more of exactly the thing the
pivot rejected. The owner restated the project's purpose, and the successor milestone **v2.5
De-ceremony** was scoped to delete rather than extend.

**Superseded by v2.5:** plans 30-02/03/04 are cut (`deny-domains.json`'s own `_note` says no hook reads
it and a drift test over it would prove a file equals itself); phase 33 is cut (`secret_scan` is
deleted outright, so SEAL-04 is moot, and SEAL-05's portable ratification record is replaced by one
recorded decision); ADR-0011 is accepted and its code-before-ratification recorded by v2.5 phase 39,
which also closes RAT-4, RAT-5 and the per-tool deny spelling as **obsolete-by-deletion** — all three
being one finding: every human-ratification gate here assumes reviewer ≠ author, and this repo has one
owner.

**Not archived:** phase directories for 30 and 34–37 stay in place — they hold the human-queue drafts
and verification records phase 39 discharges. `REQUIREMENTS.md` for v2.4 is archived at
`.planning/milestones/v2.4-REQUIREMENTS.md`.

## v2.3 Contract Graph, Brownfield Adoption, Living Docs (Shipped: 2026-07-22)

**Phases completed:** 10 phases (24, 25, 26, 26.1, 26.2, 27, 27.1, 27.2, 28, 29), 43 plans, 58 tasks

**Timeline:** 2026-07-19 → 2026-07-22 (3 days, 310 commits)

**Delivered:** Three orthogonal themes on top of the v2.2 task-control plane — a general contract
*graph* replacing the linear pipeline assumption, a deterministic brownfield *adoption* path that
can propose but never self-bless, and a *living-docs* gate that makes human review of prose an
enforceable, dated obligation instead of a hope.

**Key accomplishments:**

- **Theme A — contract graph.** A ratified Draft 2020-12 relationship record, an additive
  `[[contract_graph.relationships]]` TOML slot in both the project and workspace loaders, and a
  single deterministic lowering that folds every legacy `[pipeline].edges` entry into the graph and
  fails on duplicate-id / duplicate-semantic-edge / contradiction — with the three existing linear
  configs left byte-unchanged. Over it: a domain-neutral `compile_graph()` with three stable
  diagnostic slugs and cycle-safe `direct`/`reverse`/`transitive` queries returning ids *and* the
  connecting paths. The three EXISTING conductor surfaces (`/pipeline`, `pipeline-map`,
  `orchestrator`) were generalized to consume it — no new command, no new persona — with the linear
  render held byte-identical by a hardcoded literal-text regression. Ratified as ADR-0009.

- **Theme B — brownfield adoption.** A read-only deterministic inventory → evidence-classified
  (observed/inferred/unknown) plan → complete destination manifest → refuse-by-default apply,
  carried as an ordinary `.workflow/tasks/` task that reuses the v2.2 CAS, evidence and HANDOFF
  machinery rather than inventing an adoption authority plane. Promotion is bound to a fresh
  `(draft_hash, task_revision, git_ref)` triple, so any input change invalidates the approval.
  Shipped as one `/adopt` command plus a `brownfield-adoption` skill, proven by three checked-in
  domain-neutral fixture trees (polyglot-single, client-server, partial-collision) driven end to end,
  one of them deliberately CRLF/BOM-dirty.

- **Theme C — living documentation.** `docs/doc-dependencies.toml` binds stable source selectors to
  human-authored targets; a committed ledger records only binding id, exact reviewed digest and
  disposition — no timestamps, no human names, no prose copies, no model identifiers. The guard
  classifies FRESH / BROKEN / STALE_REQUIRED / STALE_ADVISORY / UNCOVERED, fails on the first two,
  warns on the third, and enforces uncovered-count non-regression. A derived staleness queue and a
  conditional one-line SessionStart pointer surface it without hand-editing anything. The
  `/docs-update` drive loop structurally excludes accepted ADRs, `docs/reference/**`,
  `.memory/derived/**`, contracts and goldens. Ratified as ADR-0010.

- **The human ratification actually happened, and the gate held afterwards.** The first
  `docs/.docs-review-ledger.toml` was hand-authored by the human outside an agent session
  (`c32c08d`) and ADR-0010 was accepted (`ad4e339`); `docs_guard` moved exit 1 → exit 0 with 8/8
  bindings FRESH. `ledger_guard.decide()` was then re-verified *after* the ledger existed and still
  DENYs under `{}`, `GOLDEN_APPROVE_HUMAN`, `HARNESS_DEV_BYPASS`, and both together — which is the
  only test of that gate that means anything. Phase-29 verification additionally drove the loop
  green → red → green in a throwaway worktree rather than trusting the green.

- **Four inserted phases closing adversarial-review findings, none deferred quietly.** 26.1
  tightened the generic secret pattern that was excluding this repo's own `ci.yml`; 26.2 then found
  that 26.1's charset-diversity requirement was *inert* under `re.IGNORECASE` and that its new digit
  requirement had opened a false-negative seam feeding the evidence-redaction path — the opposite
  direction of risk, and the more dangerous one. 27.1 and 27.2 closed path-normalization and
  confinement bypasses on the apply path and replaced a concurrency test that could not fail.

- **A constitution-plane drift repair that the gate itself caught.** ADR-0001 declares a FOUR-member
  constitution plane; the Phase-4 stack enforced three, leaving `docs/glossary.md` agent-writable
  while four documents said it was gated. The enforcement was fixed, never the ADR. Two internal
  audits had recommended the *opposite* repair by citing a then-`proposed` ADR-0010 over an
  `accepted` ADR-0001; an external audit caught the inversion. The lesson is recorded rather than
  smoothed over: check an ADR's Status before citing it.

**Gates at close:** 16/16 fan-in gates exit 0 — pytest 1500 passed / 8 snapshots, harness_lint 323,
docs_guard unit 252, cross-repo 31, golden 17, GEN-04 42, lifecycle-eval 20/20 fixtures, emit
round-trip 100 artifacts with an empty porcelain, contract-drift clean.

### Known Gaps

Known deferred items at close: 8 (see STATE.md Deferred Items). The load-bearing ones:

- **RAT-4** — the Phase-28 constitution-plane schema write landed via `HARNESS_DEV_BYPASS` per
  ADR-0007. A dev bypass is explicitly not a human ratification. Blocks nothing mechanically; it is
  an unclosed provenance obligation, and CODEOWNERS at PR merge is the real gate.
- **RAT-5** — ADR-0004/0005/0006/0007 remain unmerged to `main`. The durable repo-config half landed
  (`f009306` restored `main` as the default branch and made the CI gate required on it); the merge
  itself is outstanding. Structural, not neglect: a solo-authored PR cannot fire a CODEOWNERS gate
  whose sole owner is the author.
- **Constitution-plane write-denies are spelled per-tool.** The deny fires on the `Write|Edit`
  matcher, but `bash."uv *"` is an unprompted `allow`, so the same write spelled through bash
  resolves to `allow`. `contract_guard` shares the shape, so `contracts/**` and `golden/**` inherit
  it. Found by the phase-29 re-verification and recorded nowhere before that. Human decision at
  close: record now, repair next milestone. **Corrected 2026-07-22 by external review:** the claim
  above that ADR-0010 clause 3b "overclaims" was wrong. Clause 3b enumerates the surface each of its
  three layers covers and explicitly scopes layer 1 to `PreToolUse(Write|Edit)`; it never asserts
  universal coverage. The defect is a MISSING FOURTH LAYER for the bash surface, not ADR phrasing.
- **Phase 27 has no VERIFICATION.md.** Recorded as debt and deliberately NOT back-filled: a
  closeout-authored verification of a long-finished phase claims an authority it cannot have.
- **`ruff check .` is not a CI gate** and reports 617 pre-existing errors, ~180 of them in the
  vendored `docs/references/opencode-matt-workflows/**` tree missing from `extend-exclude`.

---

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
