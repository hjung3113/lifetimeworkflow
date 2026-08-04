<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Brownfield adoption disposition manifest

> DERIVED reference — regenerated from `contracts/harness/adoption/manifest.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

ADOPT-03 complete destination/disposition manifest for a brownfield target: exactly one of create/preserve/conflict/marker-merge/derived-regenerate/human-ratification-required assigned to every harness destination (D-03/D-04 total rule chain), plus a separate excluded[] array recording GSD-owned lanes by reason so "excluded" is distinguishable from "missed". Self-contained Draft 2020-12 — no cross-file $ref (D-11).

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| dispositions | array | yes |  |  |
| excluded | array | yes |  |  |
| installed | array | no |  | Optional (MONO-12): the installed-file records this manifest's dispositions were resolved against, copied verbatim from the target's .harness/adoption/installed.json. Absent on a first-ever adopt and on every Phase-52-era manifest — this array is never added to `required`, so older documents stay valid. |
| target_ref | string | yes |  | Ties this manifest to the same scan as the inventory's target_ref (same shape: a git ref, or the literal "unknown"). |
