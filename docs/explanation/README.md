# Explanation

*Diátaxis quadrant: **understanding-oriented**. Hand-authored (constitution plane).*

Explanation is the discursive quadrant: the *why* behind the harness — background, rationale,
trade-offs, and the shape of the design. It complements the ADR log (`docs/adr/`), which records
*point-in-time decisions*; explanation pages give the connected, evolving narrative.

## Placeholder page stubs

- `why-contract-first.md` — why the schema (not the code) is the source of truth, and how drift is gated.
- `the-two-canonicalizers.md` — why the RFC 8785 JCS hasher (Python-only, for contract JSON) is **never** conflated with the §4.3–4.6 TSV comparator (dual-language, for data).
- `golden-equivalence.md` — why byte-diff fails on BOM/CRLF/locale/float-repr, and why a normalizing comparator is required.
- `two-plane-memory.md` — constitution plane (human-owned, gated) vs derived plane (auto-regenerated, never hand-edited).
- `the-a-model-boundary.md` — why language boundaries are process/file/DB only (CLI spawn + exit code), never in-process interop.

> Stubs only. This is a skeleton (DOCS-01); page bodies are authored as the harness grows.
