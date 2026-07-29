# How-To Guides

*Diátaxis quadrant: **task-oriented**. Hand-authored, agent-writable — NOT constitution plane
(`docs/how-to/**` is absent from `CONSTITUTION_GLOBS`; the resolver resolves it to `allow`).*

How-to guides answer "how do I accomplish X?" for a reader who already knows the basics.
They are recipes for a specific goal, not lessons and not exhaustive reference.

## Placeholder page stubs

- `add-a-contract.md` — seed a YAML spec + companion Draft 2020-12 `.schema.json`, register it with the drift-hash manifest.
- `record-a-decision.md` — add the next numbered MADR ADR under `docs/adr/` (append-only, supersede-not-edit).
- `run-the-full-stack-locally.md` — `bash tools/bootstrap/verify.sh` then `uv run pytest` to exercise bootstrap → normalize → spawn → diff → drift.

> Stubs only. This is a skeleton (DOCS-01); page bodies are authored as the harness grows.
