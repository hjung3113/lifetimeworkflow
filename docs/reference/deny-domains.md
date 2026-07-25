<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Harness path-deny domain registry

> DERIVED reference — regenerated from `contracts/harness/security/deny-domains.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

SEAL-01 shape contract for the DECLARATION of the harness's path-deny domains. Constrains SHAPE ONLY, and the instance it validates ENFORCES NOTHING: the hooks named by each record's owner_module/owner_constant remain the single source of truth, and no hook imports the instance (a registry the hooks read would make the phase-30 drift test a tautology). Two semantic rules are NOT expressible here — uniqueness of 'id' ACROSS records and uniqueness of 'owner_constant' ACROSS records, since uniqueItems compares whole objects rather than one field — and are enforced by tools.deny_domains.registry, mirroring the equivalent note in contracts/harness/docs/doc-dependencies.schema.json. Self-contained Draft 2020-12 — no cross-file $ref.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| _note | string | no |  | Prose the instance carries about its own standing: what it declares, what it does not enforce, and what is deliberately absent. |
| domains | array | yes |  | One record per ENFORCING path-deny domain. A domain that enumerates no paths (e.g. tools/hooks/commit_gate.py) is deliberately absent — see the instance's _note. |
| non_enforcing_glob_sets | array | no |  | Glob lists that resemble a deny domain but gate no tool call. Declared so a reader cannot mistake a same-named constant in a non-hook module for a deny domain. |
| version | const | yes | v1 | Registry format version. A shape change is a constitution-plane act, so this is a const rather than a free string. |
