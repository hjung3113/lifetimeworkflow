# `.memory/` — Two-Plane Context Memory (committed index)

This directory is the harness's **context-memory** root. It is split across the
non-constitution planes of the project's *four-plane* memory model. This README is
**committed**; it declares the boundary so agents and humans read the same rules
before consuming any context. It is not itself a derived artifact — edit it by hand
only to refine the plane declaration.

## Four planes at a glance

| Plane | Location | Ownership | Tracked in git? | Regenerated? |
|-------|----------|-----------|-----------------|--------------|
| **CONSTITUTION** | `contracts/`, `docs/adr/`, `docs/glossary.md`, `golden/` | Human-owned, CODEOWNERS-gated | ✅ committed | ❌ never (hand-authored) |
| **DERIVED** | `.memory/derived/` | Machine-owned (`tools/memory_regen`) | ❌ **gitignored** | ✅ every session |
| **STATE** | `.memory/state/` | Agent-authored volatile hints | ✅ committed | ❌ (small, survives sessions) |
| **PROCESS** | `.memory/agreements/` | Human-authored via feedback (curated) | ✅ committed | ❌ never |

## (1) CONSTITUTION plane — human-owned, immutable-to-agents (MEM-01)

The constitution plane is the **single source of truth**. Its four members are:

- `contracts/` — JSON Schema (Draft 2020-12) + YAML specs. The canonical contract text.
- `docs/adr/` — append-only Architecture Decision Records (supersede, never edit).
- `docs/glossary.md` — the shared domain vocabulary.
- `golden/` — approved equivalence baselines (`.verified`), promoted only by human `/golden-approve`.

**These files are human-owned and CODEOWNERS-gated. Agents MUST NOT write to them.**
Contract changes are ratified by humans and accompanied by the golden / contract-drift gates.
This is a **declaration / marker** — the *runtime* enforcement that blocks agent writes to the
constitution plane is the Phase-4 `contract-guard` hook, which is **NOT built in this phase**.
Phase 2 establishes the boundary in prose; Phase 4 makes it non-bypassable.

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
