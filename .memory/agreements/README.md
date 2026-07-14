# PROCESS agreements

`.memory/agreements/` is the PROCESS/agreements channel: a committed, human-authored and curated
tier like `.memory/state/`. It is not derived: it is never regenerated, is never written by
`tools/memory_regen`, and does not collide with `.memory/derived/`. It is also not constitution, so
it is not path-denied. This is the D-Q1 committed-but-writable posture for MEM2-01.

Create one `<slug>.md` file per working guideline using [`_TEMPLATE.md`](_TEMPLATE.md). Its YAML
frontmatter must contain `status:` (`active` or `retired`), `added:` (an ISO date), and
`provenance:` (`"added because <verbatim user feedback>"`). Its body contains a title, one-line
working-style or methodology rule, and a `Related:` link. Retire an agreement with
`status: retired`; never delete it.

An agreement is working-style or methodology only. A project or architecture decision belongs in
`docs/adr/` and `.planning/PROJECT.md` Key Decisions; link to those sources with `Related:`, never
restate the decision (§7c).

The `/agree` write path and provenance lint arrive in Phase 14; they are intentionally out of scope
for this scaffold.
