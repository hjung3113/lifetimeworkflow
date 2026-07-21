<!-- DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync -->

# Brownfield adoption promotion approval record

> DERIVED reference — regenerated from `contracts/harness/adoption/approval.schema.json` by `python -m tools.docs_sync`. Do not hand-edit; change the contract and re-run `/docs-sync`.

ADOPT-06 approval record: a human's promotion decision on proposed contract/golden/adr/relationship-authority/conflict/unknown items, bound to an exact (draft_hash, task_revision, git_ref) tuple so ANY change to the draft content, the task's CAS revision, or the git ref invalidates the approval. Deliberately a NEW, self-contained schema (D-11, no cross-file $ref) — NOT an extension of attestation.schema.json, whose constraints[] shape is a structurally different constraint-source binding vocabulary.

| Property | Type | Required | Enum / Const | Description |
| --- | --- | --- | --- | --- |
| approved_at | string | yes |  | ISO-8601 UTC timestamp of the human ratification. |
| batch_id | string | yes |  | Identifies the adoption batch this approval decides over. |
| decisions | array | yes |  | One decision per reviewed item; a promotion with zero decisions is meaningless. |
| draft_hash | string | yes |  | SHA-256 of the draft content this approval was reviewed against; any draft change invalidates the approval. |
| git_ref | string | yes |  | The git commit the approval was reviewed against; any ref change invalidates the approval. |
| task_revision | integer | yes |  | The task's CAS revision at approval time; any later revision invalidates the approval. |
