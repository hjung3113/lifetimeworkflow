# Upstream skills

These OpenCode agents are orchestration wrappers. They intentionally do **not** translate, copy, or summarize Matt Pocock's skill instructions.

Install the original upstream skills in the target repository:

```bash
npx skills@latest add mattpocock/skills
```

Select at least these skills:

```text
setup-matt-pocock-skills
grill-with-docs
grilling
domain-modeling
handoff
prototype
to-spec
to-tickets
implement
tdd
code-review
diagnosing-bugs
triage
wayfinder
improve-codebase-architecture
codebase-design
research
resolving-merge-conflicts
```

OpenCode discovers upstream `SKILL.md` files from any of these project-local locations:

```text
.opencode/skills/<name>/SKILL.md
.claude/skills/<name>/SKILL.md
.agents/skills/<name>/SKILL.md
```

The wrapper agents load those original files on demand through OpenCode's native `skill` tool. They stop rather than use a local approximation when an expected skill is missing.

The wrappers were checked against upstream commit:

```text
e9fcdf95b402d360f90f1db8d776d5dd450f9234
```

Using `@latest` intentionally installs the current upstream version rather than freezing a copied snapshot. Review upstream changes when behavior changes.
