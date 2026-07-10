# Walking Skeleton — LogParser Pipeline Harness

**Phase:** 1
**Generated:** 2026-07-08

## Capability Proven End-to-End

> One sentence: the smallest capability that exercises the full harness stack.

A developer/agent runs one command and the harness bootstraps .NET 10 + uv, spawns a fixture-grade .NET toy converter over the A-model CLI boundary from a Python golden-runner, normalizes both the converter output and the approved baseline through the ONE shared §4.3–4.6 canonicalization core, and reports PASS for a representation-only-different fixture but FAIL for a real value regression — while a schema change trips the RFC 8785 drift-hash gate. No byte-diff, no agent self-bless.

## Architectural Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Polyglot boundary | A-model: Python `subprocess.run([...], shell=False)` spawns .NET CLI; exchange via output FILE + exit code | Locked §0 — process/file/DB only, never in-process interop. Proves the real boundary the harness exists to guard. |
| Two canonicalizers (NEVER conflate) | (a) RFC 8785 JCS hasher = **Python-only** (`rfc8785` 0.1.4) over `.schema.json` files for drift; (b) §4.3–4.6 TSV comparator = **dual thin impl** (.NET + Python) cross-validated by a shared fixture corpus | RESEARCH Pitfall 1 + D-04/D-07. JCS is for JSON contract text; the §4-5 comparator is for TSV data. Zero .NET JCS code this phase. |
| Normalization core ownership | Language-neutral rule spec is canonical; `libs/python/normalize` + `libs/dotnet/Normalize` each implement it; `libs/normalize-fixtures/` `(raw,canonical)` corpus proves parity | D-04/D-05. Built once here, reused by the Phase-4 polyglot linter (POLY-01). |
| Drift gate P14 fix | §4.3–4.6 conventions materialized as `contracts/normalization/format-conventions.schema.json`; hash a MANIFEST of ALL `.schema.json` | RESEARCH Pattern 2 / P14 — mutating the null-token or BOM policy must bump the hash exactly like a column reorder. |
| Contract format | YAML spec (human-readable, seeded verbatim with TBD markers) + companion `.schema.json` (Draft 2020-12) = validated/hashed source of truth | D-06. Stack: `jsonschema` 4.26.0 / `check-jsonschema` 0.37.4 / `JsonSchema.Net` 9.2.2. |
| Golden human gate | `.received` (machine-proposed) / `.verified` (human-promoted) two-file split; `/golden-approve` refusal path is automated-tested | D-03 + P9 + A2. Hard CODEOWNERS/plugin enforcement DEFERRED to Phase 4/5. |
| Toolchain bootstrap | Idempotent cache-check `dotnet-install.sh --channel 10.0 --install-dir $HOME/.dotnet` + `uv sync`; wired as a NEW SessionStart entry APPENDED to `.claude/settings.json` (coexists with 2 GSD entries) | D-08/D-09 + P5. Ephemeral container self-heals; Docker/manual rejected. |
| Directory layout | `contracts/` `docs/` `libs/{python,dotnet,normalize-fixtures}` `components/toy-converter` `tools/{bootstrap,contract-hash,contract-drift,golden-runner}` + uv workspace root `pyproject.toml` | RESEARCH Recommended Project Structure (Phase-1 subset of ARCHITECTURE.md). |

## Stack Touched in Phase 1

- [x] Project scaffold — uv workspace root `pyproject.toml`, ruff/pyright/pytest, .NET 10 SDK bootstrap, `.gitignore`
- [x] One real cross-language call — Python golden-runner spawns .NET toy converter via A-model CLI (subprocess, exit code, output file)
- [x] One real read AND one real write — toy converter reads `input/seed.tsv`, writes normalized `--out` TSV; drift gate reads `.schema.json`, writes `.hashes/manifest.json`
- [x] One real interactive gate wired to the loop — `/golden-approve` `.received`→`.verified` refusal path
- [x] Documented local full-stack run command — `bash tools/bootstrap/verify.sh` then `uv run pytest` exercises bootstrap → seed → normalize → spawn → diff → drift

## Out of Scope (Deferred to Later Slices)

> Explicit — prevents later phases from re-litigating Phase 1's minimalism.

- Real parser/converter/normalization logic (50+ correction rules), real column set, domain-confirmed values — project Out of Scope; seeds stay `TBD` placeholders.
- Two-plane derived memory (`.memory/`, repo-map, contracts-index), AGENTS.md nearest-wins, session-start context injection — Phase 2.
- Full agent/command/skill surface, `opencode.json`, permission matrix, `/docs-sync`, `/strangler-step` — Phase 3.
- On-write hooks, polyglot-boundary linter enforcement, format-on-write, secret protection, contract-guard, commit gate — Phase 4 (the linter REUSES this phase's §4-5 core).
- CI matrix, CODEOWNERS hard gate, PR template — Phase 5.
- Single-source dual-runtime emitter — Phase 6.
- Any .NET-side JCS/RFC 8785 code — never needed (JCS is Python-only).

## Subsequent Slice Plan

Each later phase adds one vertical slice on top of this skeleton without altering its architectural decisions:

- Phase 2: Two-plane memory + rules — derived artifacts regenerate from the contracts/code this phase seeds; session-start injection surfaces drift state.
- Phase 3: Agents + commands + skills — `/golden`·`/golden-approve` graduate to the full command surface; migration commands gate behind this phase's now-trusted golden net.
- Phase 4: Plugins + hooks — the polyglot linter reuses this phase's §4-5 normalization core (built once here); contract-guard enforces the `.received`/`.verified` split at write time.
- Phase 5: CI + gates — GitHub Actions mirrors the in-session golden + drift gates; CODEOWNERS ratifies the constitution plane.
- Phase 6: Emitter — compiles the authored source into opencode + Claude Code artifacts.
