<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Human-docs dependency registry

> DERIVED reference — regenerated from `contracts/harness/docs/doc-dependencies.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

DOCSUP-01 shape contract for the PARSED form of docs/doc-dependencies.toml — the registry of source-set -> human-authored-doc review obligations. Constrains SHAPE ONLY. The five DOCSUP-01 semantic rejections (path escape, duplicate id across rows, empty selector on a required binding, derived/reference target, accepted-ADR edit policy) are NOT expressible in JSON Schema — they need cross-row uniqueness, a live filesystem, and glob-set membership — and are enforced by tools.docs_guard.registry, which is the registry's ONLY validator (the registry is TOML, so /contract-check's check-jsonschema step does not cover it). Self-contained Draft 2020-12 — no cross-file $ref.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| binding | array | no |  | The [[binding]] rows. Absent or empty is a shape-valid registry. |
