# 1. Walking-Skeleton Golden Core Architecture

*MADR 4.x · plane: constitution (human-owned, immutable, append-only)*

- **Status:** accepted
- **Date:** 2026-07-08
- **Deciders:** Phase 1 planning (Constitution + Golden Core)
- **Supersedes:** —
- **Superseded by:** —

## Context and Problem Statement

The harness must guard a polyglot (.NET 10 + Python) log-parsing pipeline where the risk is
**representation-level divergence** across the language boundary (encoding, newline, locale,
timezone, float representation, TSV null-vs-empty) and **silent contract drift**. Before any
component logic exists, we need to prove — end to end, one loop — that the safety net actually
closes: bootstrap → spawn across the boundary → normalize both sides through one shared core →
diff against an approved baseline → and trip a drift gate on schema change. The problem this ADR
records: *what is the minimal, locked architecture of that walking skeleton?*

## Decision Drivers

- Polyglot boundary must be exercised for real, not simulated (project constraint §0).
- Representation-only differences must PASS; real value regressions must FAIL (roadmap success criterion 3).
- Contract text drift — including cross-cutting §4-5 conventions, not just columns — must be detected (Pitfall P14).
- No agent may self-bless a golden baseline (Pitfall P9): machines gate, humans ratify.
- Byte-diff is unusable here — it false-reds on BOM/CRLF/locale/float-repr (Pitfall P4).
- Build once, reuse: the normalization core is reused by the Phase-4 polyglot linter (POLY-01).

## Considered Options

1. **Recorded-pairs only** — replay stored input/output pairs. *Rejected:* never exercises the live CLI boundary or bootstrap; not end-to-end.
2. **Representation-difference only** — synthesize BOM/CRLF/locale variants and normalize. *Rejected:* proves the comparator but not the A-model spawn, exit-code, or golden-approval flow.
3. **Full walking skeleton (chosen)** — Python golden-runner spawns a fixture-grade .NET toy converter over the A-model CLI boundary, normalizes converter output and the approved baseline through the ONE shared §4.3–4.6 core, PASS/FAIL on a representation-only vs real-regression fixture pair, while a schema change trips the RFC 8785 drift-hash gate.

## Decision Outcome

**Chosen: Option 3 — the full walking skeleton**, with these locked architectural decisions:

- **A-model CLI boundary.** Python `subprocess.run([...], shell=False)` spawns the .NET CLI; data is exchanged by **output file + exit code** only. Never in-process interop (project constraint §0).
- **Two canonicalizers, never conflated.**
  - (a) An **RFC 8785 / JCS** hasher — **Python-only** — over `.schema.json` files, for contract-text drift. **Zero .NET JCS code**, ever (JSON contract text lives on the Python side of the gate).
  - (b) The **§4.3–4.6 TSV comparator** — a **dual-language thin implementation** (`libs/python/normalize` + `libs/dotnet/Normalize`) cross-validated by a shared `(raw, canonical)` fixture corpus, for **data** equivalence.
- **Normalization core ownership.** A language-neutral rule spec is canonical; each language implements it thinly; shared fixtures catch per-language drift. Built once here, **reused by the Phase-4 polyglot linter** (POLY-01).
- **Golden human gate.** A two-file split: `.received` (machine-proposed) vs `.verified` (human-promoted). Promotion is `/golden-approve`; its refusal path is automated-tested. **Machines gate, humans ratify** — no agent self-bless (P9). Hard CODEOWNERS/plugin enforcement is DEFERRED to Phase 4/5.
- **Contract-first, schema as source of truth.** YAML spec (human-readable, seeded verbatim with TBD markers) + companion **JSON Schema Draft 2020-12** `.schema.json`, which is the validated/hashed source of truth. Code that disagrees with the schema is wrong.
- **Materialized §4-5 conventions for drift (P14 fix).** The §4.3–4.6 conventions are materialized as `contracts/normalization/format-conventions.schema.json`; the drift gate hashes a **manifest of ALL `.schema.json`**, so mutating the null-token or BOM policy bumps the hash exactly like a column reorder.
- **Two-plane split.** The **constitution plane** (`contracts/`, `golden/`, `docs/adr/`, `docs/glossary.md`) is human-owned and gated; the **derived plane** (repo-map, contracts-index, `docs/reference/`) is auto-regenerated and never hand-edited (added Phase 2+).

### Consequences

- **Good:** one real loop proves the boundary, the comparator, the golden-approval flow, and the drift gate together; the normalization core is available for reuse; the constitution plane is auditable and immutable via this ADR log.
- **Good:** representation-only fixtures PASS and real regressions FAIL, demonstrating the net neutralizes noise without hiding real change.
- **Bad / accepted:** the toy converter is fixture-grade (no real parser/50+ correction rules), and hard CODEOWNERS/hook enforcement of the golden split is deferred — the human gate is convention + automated-test this phase, not yet a hard gate.
- **Neutral:** JCS being Python-only means the .NET side never needs a canonicalization library for contract text.

## Links

- Records the constitution-plane + golden decisions materialized in `contracts/` and `golden/` (pattern: golden).
- Companion glossary: `docs/glossary.md`. MADR convention: `docs/adr/README.md`.
- Sources: `.planning/phases/01-constitution-golden-core/{01-CONTEXT.md (D-01..D-09), SKELETON.md}`.
