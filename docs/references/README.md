# External reference material

Vendored, **read-only** reference projects kept here for study — not part of
this repo's live harness and not loaded by any runtime.

| Directory | What it is | Note |
| --- | --- | --- |
| `opencode-matt-workflows/` | An opencode workflow pack (flow-* agents/commands, adversarial-review, orchestrator design docs) captured 2026-07-16 | The `.opencode/` tree inside is **its own** config, not ours. Because it is nested under `docs/`, opencode does not pick it up — only a root-level `.opencode/` is live. Do not copy files out of it into the repo's real `.opencode/`/`.claude/` trees without going through the harness source in `harness/`. |

These trees are informational: harness edits still happen in `harness/` and are
emitted to the root `.opencode/` + `.claude/` surfaces, per the root `AGENTS.md`.
