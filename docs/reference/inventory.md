<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Brownfield adoption inventory

> DERIVED reference — regenerated from `contracts/harness/adoption/inventory.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

ADOPT-01 deterministic, read-only, size-capped inventory of a scanned brownfield target: enumerated included/excluded files, language/manifest/documentation/CI/test surface detection, and candidate process boundaries, each evidence-classified observed/inferred/unknown with evidence pointers into already-hashed included files. Self-contained Draft 2020-12 (D-11) — no cross-file $ref; duplicates evidenceRef/classification also carried by plan.schema.json and manifest.schema.json. Excluded entries structurally carry no content hash or excerpt (D-10).

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| candidate_process_boundaries | array | yes |  |  |
| ci_surfaces | array | yes |  |  |
| documentation_surfaces | array | yes |  |  |
| enumeration_mode | string | yes | git, builtin | Which enumeration path this run took (D-09) — self-describing so a run states whether git ls-files or the builtin denylist walk produced the result. |
| excluded | array | yes |  |  |
| included | array | yes |  |  |
| languages | array | yes |  |  |
| manifests | array | yes |  |  |
| max_file_bytes | integer | yes |  | The size cap used for this run — self-describing per the size-capped exclusion rule. |
| target_ref | string | yes |  | The scanned target's git ref, or the literal "unknown" when the target has no git — a fact about the INPUT, never a clock (no-timestamp determinism rule). |
| test_surfaces | array | yes |  |  |
