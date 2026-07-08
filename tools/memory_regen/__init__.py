"""memory_regen — the DERIVED-plane generators + shared injection assembler (MEM-03, HOOK-05).

A virtual uv-workspace member (sibling of contract_hash/, golden_runner/), invoked by module path
(`python -m tools.memory_regen.<entry>`). It owns the *machine-owned* plane of the two-plane memory
model: repo-map (tree-sitter parse → networkx PageRank → top-N elided defs) and contracts-index
(reusing the Phase-1 hash/drift modules), both written under `.memory/derived/` (gitignored,
regenerated every session), plus the single injection-contract assembler both runtime adapters call.

Wave 1 (this plan, 02-01) lands only the member skeleton + pinned toolchain + structural layout
test — the generators themselves arrive in the Wave-2 plans against this stable, resolved base.
"""
