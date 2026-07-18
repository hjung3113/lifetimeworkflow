# Task packet slots

Each committed task lives at `.workflow/tasks/<task-id>/`, where `<task-id>` matches
`T-<UTCyyyymmddHHMMSS>-<kebab-slug>`. A packet contains `task.json`, `state.json`,
`evidence.json`, optional `handoff.json`, and immutable outputs under `artifacts/`.

This namespace is **committed volatile state**, not derived state. Do not regenerate it from
`.memory/`, and do not hand-copy packet data into contracts. The four schemas under
`contracts/harness/task-control/` are authoritative for packet shape.

`.memory/state/` may contain only an active task ID and HANDOFF pointer. Validation of a packet
must not read `.memory/state/`; memory regeneration must not require `.workflow/tasks/`. Deleting
either side therefore leaves validation/regeneration of the other unchanged.

Artifacts are immutable after they are indexed. `evidence.json` stores only their repository-
relative path, summary, and SHA-256 digest. Packet fields must not contain credentials, personal
data, provider names, or runtime identity metadata.
