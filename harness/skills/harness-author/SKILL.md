---
name: harness-author
description: >-
  Use when about to author a new skill, command, or agent under harness/ — guides a grounded Q&A
  with defaults cited as path:line from this checkout, FIRST forcing the anti-sprawl question "why
  can't this live in an existing one?" for whichever kind you're adding, before any new file is
  created. Widens the prior skills-only meta-authoring scope to all three emitter-projected kinds.
---

# harness-author

The meta-skill for authoring a harness artifact — a skill, a command, or an agent. Its first job
is to stop sprawl in whichever kind you're adding; its second is to make the new artifact
well-formed and, where the shape allows, machine-checked.

## Step 0 (mandatory): why not an existing one?

Before creating anything, answer out loud: **"Why can't this live in one of the existing skills,
commands, or agents?"** Each kind's enumerated set is small and deliberately disjoint — a new file
is justified only when its routing trigger/purpose does not overlap any existing sibling of the
same kind. If the knowledge fits an existing skill's domain, extend that skill's body or
`references/` instead of adding a directory; if a command's job is already covered, extend that
command's action rather than adding a new one.

The current sets are enumerated at their single source of truth, not restated here (a restated
list is a second copy that silently goes stale):

- Skills: `tools/harness_lint/caps.py:144-155` (`EXPECTED_SKILLS`).
- Commands: `tools/harness_lint/tests/test_commands.py:52-74` (`EXPECTED_COMMAND_NAMES`).
- Agents: `tools/harness_lint/caps.py:57-59` (`EXPECTED_PERSONAS`) — enforced by
  `tools/harness_lint/tests/test_agents.py::test_expected_personas_present_no_sprawl`; adding an
  un-enumerated persona fails this guard, so update the set here in the same commit.

## Step 1: choose the kind and its shape

### Skill

Create `harness/skills/<name>/SKILL.md` where the directory name equals the frontmatter `name`.

- **name:** length capped by `tools/harness_lint/caps.py:_NAME_MAX`, matches the regex
  `^[a-z0-9]+(-[a-z0-9]+)*$` (`tools/harness_lint/caps.py:_NAME_RE`), equals the parent directory,
  no reserved vendor word, no angle-bracket tag.
- **description:** non-empty, capped by `tools/harness_lint/caps.py:_DESC_MAX`, verb-first "Use
  when… + does…" with a concrete routing trigger, disjoint from every other skill.
- **body:** progressive disclosure — concise, warned above `tools/harness_lint/caps.py:_BODY_WARN_LINES`
  lines (`tools/harness_lint/caps.py:_BODY_WARN_LINES` — a warn, not a hard fail), pointing to
  `references/` for depth rather than inlining everything.

The SAME caps apply to both the `opencode` and `Claude` runtimes — there is no per-runtime size
divergence to author around.

### Command

Create `harness/commands/<name>.md` with `description`, `agent`, and optional `subtask`
frontmatter. See `harness/commands/component.md:1-9` for a real example of the shape (a routing
`description`, an `agent:` slug, `subtask: true`). The `agent:` value must be a well-formed slug
(`tools/harness_lint/tests/test_commands.py:_AGENT_SLUG`) that resolves to a real persona file
under `harness/agents/` — checked at the phase level by
`tools/harness_lint/tests/test_agent_referential_integrity.py`.

### Agent

Create `harness/agents/<persona>.md` with least-privilege frontmatter (`mode`, `permission`,
`tools`). See `harness/agents/curator.md:1-17` for a real example of the shape — a `permission`
block least-privileged to the persona's job, and a `tools` allowlist that must agree with it. The
persona set, the valid permission keys, and the valid modes live at
`tools/harness_lint/caps.py:22-59`; the read-only-persona invariant is enforced by
`tools/harness_lint/caps.py:91-103` (`is_read_only`).

## Step 2: author the source

Write ONLY under `harness/` — `harness/skills/`, `harness/commands/`, or `harness/agents/`. Never
hand-edit the emitted `.opencode/` or `.claude/` trees; they are machine-generated projections.
Reference shapes to copy from:

- Command: `harness/commands/component.md:1-9`.
- Agent: `harness/agents/curator.md:1-17`.
- Skill (concise, `references/`-free body): `harness/skills/context-budget/SKILL.md:1-16`.

## Step 3: verify

Run the structural gate for the kind you authored:

- Skill: run `uv run pytest` on `tools/harness_lint/tests/test_skills.py` with `-x -q` — enforces
  the caps, the regex, the dir-name match, the routing-trigger token, the reserved-word/tag bans,
  and the pinned set of skill names (so adding an un-enumerated skill fails loudly).
- Command: run `uv run pytest` on `tools/harness_lint/tests/test_commands.py` with `-x -q` —
  enforces the caps and the pinned `EXPECTED_COMMAND_NAMES` set (so adding an un-enumerated command
  fails loudly), plus `tools/harness_lint/tests/test_agent_referential_integrity.py` for the
  cross-file `agent:` resolution.
- Agent: run `uv run pytest` on `tools/harness_lint/tests/test_agents.py` with `-x -q` — enforces
  the frontmatter shape, the read-only-persona invariant, and the pinned `EXPECTED_PERSONAS` set
  (so adding an un-enumerated persona fails loudly).

Then run the emit round-trip so both runtime trees stay in lockstep with `harness/`:

```
python -m tools.harness_emit && git diff --exit-code -- .opencode .claude opencode.json AGENTS.md CLAUDE.md tools/harness_emit/emit-manifest.json
```

A non-empty diff after that command means the source and the emitted trees have drifted — fix the
source, never the emitted copy.

## Out of scope

Plugins and hooks are not covered here — they have no analogous single-file source shape today.

## Related

- `harness/skills/brownfield-adoption/SKILL.md` — a sibling example of the Step-0 anti-sprawl
  question answered explicitly for a new skill.
- `tools/harness_lint/caps.py` — the single source of truth for every cap and enumerated set cited
  above.
