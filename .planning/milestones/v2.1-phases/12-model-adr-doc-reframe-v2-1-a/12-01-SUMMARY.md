---
phase: 12-model-adr-doc-reframe-v2-1-a
plan: 01
status: complete
---

# Plan 12-01 Summary

Created the committed, human-authored `.memory/agreements/` PROCESS tier with a frontmatter-based
per-guideline template and its tier documentation. The template and documentation encode the §7c
working-style-only rule: link to ADRs and PROJECT.md Key Decisions; never restate a project decision.

Updated `.memory/README.md` to declare four planes and state the data-authority rule: on a data
conflict, `contracts/` and `docs/adr/` are authoritative over state. Updated the source
`harness/skills/two-plane-memory/SKILL.md` with the agreements tier and matching data-authority
wording.

Validation ran the plan's structural assertions: the template and tier README exist, frontmatter and
`Related:` fields are present, agreements is not ignored or generated, the shared docs contain no
epistemic-distrust wording, and no injector or generated runtime files were edited.

## Deferred

`harness/skills/two-plane-memory/SKILL.md` is the harness source. Re-emitting it to `.opencode/` and
`.claude/` runtime copies is deferred to Phase 15; those generated copies were intentionally not
edited here.
