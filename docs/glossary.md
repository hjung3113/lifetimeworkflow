# Glossary — Ubiquitous Language

*owner: TBD · status: seed · plane: constitution (human-owned)*

> The single place a term is defined. Other docs reference this file rather than redefining
> terms. This is a **seed** (DOCS-01): harness-level vocabulary now, domain vocabulary grows
> as contracts are seeded. Domain framing is aligned with the parserimprove GLOSSARY.

## Harness / safety-net terms

| Term | Definition |
|------|------------|
| **Walking skeleton** | The smallest end-to-end slice that exercises the whole harness stack (bootstrap → spawn → normalize → golden diff → drift gate) rather than any one component in full. Phase 1's deliverable. |
| **Golden equivalence** | Equivalence checked by diffing an approved baseline against fresh output **after normalization**, so intended differences surface and representation-only differences do not. Never a raw byte-diff. |
| **Normalized comparison** | Comparison performed only after both sides pass through the shared §4.3–4.6 canonicalization core, neutralizing encoding/newline/locale/timezone/float-representation noise. |
| **§4.3–4.6 conventions** | The cross-cutting canonicalization rules: UTF-8 with BOM stripped, forced LF, InvariantCulture `.` decimals, tolerance-aware float compare, deterministic key/row ordering, UTC ISO-8601 timestamps, explicit TSV escape + null-vs-empty token. The single shared comparator core. |
| **Two canonicalizers (never conflated)** | (a) an **RFC 8785 / JCS** hasher (Python-only) over `.schema.json` files, for contract-text drift; (b) the **§4.3–4.6 TSV comparator** (dual-language, cross-validated by shared fixtures), for data equivalence. JSON contract text and TSV data use different canonicalizers. |
| **RFC 8785 / JCS** | JSON Canonicalization Scheme — deterministic serialization (sorted keys, normalized whitespace/numbers) of a `.schema.json` so it can be SHA-256 hashed reproducibly for the drift gate. |
| **Contract-drift gate** | The gate that recomputes the JCS SHA-256 of each contract schema (including the materialized §4-5 conventions schema) and fails when a hash moves without a paired golden update; classifies the change breaking vs non-breaking. |
| **`.received` / `.verified`** | The two-file golden split: `.received` is machine-proposed output; `.verified` is the human-promoted, approved baseline. Promotion requires a human `GOLDEN_APPROVE_HUMAN` ratification, gated again by CODEOWNERS at merge. |
| **Machines gate, humans ratify** | Automation may propose (`.received`) and block, but only a human promotes a baseline to `.verified`. No agent self-blesses a golden (Pitfall P9). |
| **A-model boundary** | The polyglot boundary shape used by this project: Python spawns the .NET CLI via `subprocess` (`shell=False`), exchanging data by **output file + exit code** — process/file/DB only, never in-process object passing. |
| **Constitution plane** | Human-owned, gated source of truth: `contracts/`, `docs/adr/`, `docs/glossary.md` (ADR-0001's fourth member, root `golden/`, is superseded by ADR-0012 clause (d); instance baselines live at `examples/<instance>/golden/`). Changed only through review (CODEOWNERS) and the golden/drift gates. |
| **Derived plane** | Auto-regenerated, never hand-edited artifacts (e.g. `.memory/` repo-map, contracts-index, `docs/reference/`). Rebuilt from the constitution plane; editing by hand is forbidden (added Phase 2+). |

## Domain terms (seeded from parserimprove GLOSSARY; expand as contracts land)

| Term | Definition |
|------|------------|
| **Standard log spec** | Company-internal standard log format (TSV). Equipment makers are asked to emit logs in this shape. |
| **Converter** | The .NET component that transforms a non-standard (maker-specific) log into the standard log spec format. |
| **Value normalization** | Aligning maker-/model-specific representations (aliases, codes, module types) into one consistent form. Distinct from correction. |
| **Correction / enrichment** | Filling log defects — supplying missing values and fixing wrong ones. A separate step from value normalization. |
| **Golden (equivalence) file test** | Diffing the existing parser's output against the new output for a real log input, to detect unintended differences. |
| **Polyglot boundary** | The point where .NET (parser/converter) and Python (scheduler/collector/config-parser) exchange data only via process/file/DB. |

> Terms are added here as they enter the harness. Do not redefine a term elsewhere — link here.
