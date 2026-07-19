<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Brownfield adoption mapping plan

> DERIVED reference — regenerated from `contracts/harness/adoption/plan.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

ADOPT-02 evidence-separated mapping plan for a brownfield target: proposed members/components/relationships/contract-candidates/test-commands/docs-destinations/agents-boundaries, each classified observed/inferred/unknown with evidence; unresolved ownership stays a question, never invented authority. Relationship candidates duplicate the Phase-24 contracts/harness/topology/relationship.schema.json shape (D-11, not $ref'd). Self-contained Draft 2020-12 — no cross-file $ref.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| proposals | array | yes |  |  |
| questions | array | yes |  |  |
| relationships | array | yes |  |  |
| target_ref | string | yes |  | Ties this plan to the same scan as the inventory's target_ref (same shape: a git ref, or the literal "unknown"). |
