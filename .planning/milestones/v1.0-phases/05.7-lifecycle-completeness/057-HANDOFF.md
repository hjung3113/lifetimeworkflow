# Phase 5.7 — Session Handoff

**RESOLVED 2026-07-09 (next session).** Phase 5.7 is COMPLETE: research→plan→execute all done. See
057-RESEARCH.md, 057-VALIDATION.md, 057-01/02-PLAN.md, 057-01/02-SUMMARY.md. Non-example
`uv run pytest` green (402); `EXPECTED_SKILLS` 4→8; GEN-04/05 prose guard clean; LIFE-01..11 shipped.
The steps below are retained as the historical handoff record.

---

**Written:** 2026-07-09 (end of a long session — context budget). Phase 5.7 was **designed** this session; **research → plan → execute** are for the NEXT session.

## Where things stand
- Phases 1–5 + 5.5 COMPLETE and pushed (`origin/claude/data-pipeline-harness-8aypct`). Full non-example suite green (361 passed).
- The template core is domain- and (non-Python-)language-neutral; log-parser lives in `examples/log-parser/`. GEN-04 guard enforces core→example no-dependency (code + prose).
- Phase 5.7 (Lifecycle Completeness) is DESIGNED: `057-CONTEXT.md` (with the embedded adversarial audit), ROADMAP §Phase 5.7, REQUIREMENTS §LIFE (LIFE-01..11).

## Next session — exact steps
1. **Read** `057-CONTEXT.md` (the `<audit_findings>` + `<decisions>` are the ground truth; no need to re-run the audit).
2. **Research** → produce `057-RESEARCH.md` (gsd-phase-researcher). Verify per-item: reused tools for `/contract-check` (`tools/contract_drift`/`contract_hash`), the 7 canonicalization axes for `golden-debug` (from `libs/normalize-spec.md` + CLAUDE.md table + `libs/python/normalize/core.py`), the `project.toml [[languages]].persona` flow for the language-engineer template, and — CRITICAL — how adding new commands/skills/personas breaks the `tools/harness_lint` anti-sprawl / referential-integrity / GEN-04-prose-guard tests (Phase 5.5's repeated RED). Enumerate every EXPECTED_* set + guard token that each new asset must be added to.
3. **Plan** → `057-NN-PLAN.md` + `057-VALIDATION.md` (gsd-planner). Suggested waves: MUST-HAVE first (LIFE-01..05), SHOULD-HAVE after (LIFE-06..11). Each plan MUST update the harness_lint expected-lists IN THE SAME WAVE as the asset it adds (Phase 5.5 lesson). New commands' frontmatter `agent:` must name a real CORE persona (referential-integrity). New assets must be domain-neutral (GEN-04 prose guard — no examples/ or domain tokens).
4. **Check** (gsd-plan-checker) → revise until 0 blockers.
5. **Execute** wave-by-wave (gsd-executor). No constitution-plane writes expected (harness/ + docs non-adr) → NO `GOLDEN_APPROVE_HUMAN` token needed. If the planner decides to record a lifecycle-completeness ADR, that ADR write DOES need the approval path (a human sets `GOLDEN_APPROVE_HUMAN` in a gitignored `.claude/settings.local.json` env, per DEF-05-SESSION-TOKEN; removed after).

## Locked constraints (do not violate)
- Domain-neutral (log-parser specifics stay in `examples/`); GEN-04 guard clean (code + prose).
- Skill caps: name ≤64 / desc ≤1024 / body <500 (progressive disclosure, `references/`).
- `code-reviewer` read-only; least-privilege permissions (new commands wrap existing tools, no new broad scopes).
- Reuse existing `tools/` (no re-implementation). No model identifiers in artifacts. `git mv` for any moves.
- Do NOT rewrite ADEQUATE assets: `golden-testing`, `docs-sync`, `adr`, `strangler-step`, `component`, `/golden*`, `/test`.
- Keep the non-example `uv run pytest` suite green as the phase-wide invariant.

## After 5.7
Phase 6 (CI + Gates, generic config-derived matrix — .NET egress runs for real on GitHub runners; involves a real PR + CODEOWNERS identity decision) → Phase 7 (dual-runtime emitter).
