# `.memory/` — Two-Plane Context Memory (committed index)

This directory is the harness's **context-memory** root. It is split across the
non-constitution planes of the project's *four-plane* memory model. This README is
**committed**; it declares the boundary so agents and humans read the same rules
before consuming any context. It is not itself a derived artifact — edit it by hand
only to refine the plane declaration.

## Four planes at a glance

| Plane | Location | Ownership | Tracked in git? | Regenerated? |
|-------|----------|-----------|-----------------|--------------|
| **CONSTITUTION** | `contracts/`, `docs/adr/`, `docs/glossary.md` | Human-owned, CODEOWNERS-gated | ✅ committed | ❌ never (hand-authored) |
| **DERIVED** | `.memory/derived/` | Machine-owned (`tools/memory_regen`) | ❌ **gitignored** | ✅ every session |
| **STATE** | `.memory/state/` | Agent-authored volatile hints | ✅ committed | ❌ (small, survives sessions) |
| **PROCESS** | `.memory/agreements/` | Human-authored via feedback (curated) | ✅ committed | ❌ never |

## (1) CONSTITUTION plane — human-owned, immutable-to-agents (MEM-01)

The constitution plane is the **single source of truth**. Its three members are:

- `contracts/` — JSON Schema (Draft 2020-12) + YAML specs. The canonical contract text.
- `docs/adr/` — append-only Architecture Decision Records (supersede, never edit).
- `docs/glossary.md` — the shared domain vocabulary.

Approved equivalence baselines (`.verified`) are no longer a root `golden/` member: they live per
instance at `examples/<instance>/golden/` and are promoted only by a human `GOLDEN_APPROVE_HUMAN`
token ratified through the CODEOWNERS `/examples/*/golden/` route.

**These files are human-owned and CODEOWNERS-gated. Agents MUST NOT write to them.**
Contract changes are ratified by humans and accompanied by the golden / contract-drift gates.
The membership above is **declared by** [ADR-0001](../docs/adr/0001-walking-skeleton-golden-core.md)
§Decision, not by this file — this page restates it. ADR-0001's four-member membership is
superseded by [ADR-0012](../docs/adr/0012-ci-and-merge-as-decision-authority.md) clause (d), which
drops root `golden/`. The *runtime* enforcement is the
`contract-guard` hook (`tools/hooks/contract_guard.py`), which **is built and live**: a
PreToolUse(Write|Edit) onto any of the three members is denied unless a human `GOLDEN_APPROVE_HUMAN`
token is set, and CODEOWNERS gates it again at merge. Phase 2 established the boundary in prose;
Phase 4 made it non-bypassable.

`docs/glossary.md` is a single FILE on the plane, not the `docs/` tree — the rest of `docs/` is
agent-writable. Being gated does not remove it from the human-doc review corpus: ownership controls
*who may edit*, a doc-dependency binding controls *when a human owes a review*, and the glossary
carries both.

## (2) DERIVED plane — `.memory/derived/` — auto-regenerated, gitignored (D-04)

Everything under `.memory/derived/` is produced by `tools/memory_regen` (repo-map via
tree-sitter + PageRank, contracts-index via the Phase-1 hash/drift modules). It is:

- **DERIVED — do not hand-edit.** Every generated file carries a
  `DERIVED — do not hand-edit` header. Delete it and rerun the generator: the output is
  byte-identical (determinism is the correctness test, not `git diff` — the path is gitignored).
- **Gitignored** (`.memory/derived/` in `.gitignore`). The ephemeral container regenerates it at
  SessionStart, so it is never committed. Do not add tracked files under `derived/`.

## (3) STATE plane — `.memory/state/` — committed volatile state (D-03)

Small, agent-authored volatile context that must survive the ephemeral container across sessions:

- `state/activeContext.md` — what is in flight right now.
- `state/progress.md` — a terse running progress log.

State is **committed** (so it survives). The SessionStart injector injects only a *pointer* to
`activeContext`, never its body. On a **data conflict**, `contracts/` and `docs/adr/` are
authoritative over `.memory/state/`: this identifies which artifact wins a contradiction, not a
reason to distrust grounded work. Never store secrets, tokens, credentials, or PII here. Durable
decisions belong in append-only ADRs, not in state.

## (4) PROCESS plane — `.memory/agreements/`

Committed, human-authored working agreements captured from feedback. They are curated and never
regenerated; see [`.memory/agreements/README.md`](agreements/README.md) for the entry shape and the
link-never-restate rule.
