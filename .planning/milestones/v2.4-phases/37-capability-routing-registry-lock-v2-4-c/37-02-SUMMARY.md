# Summary 37-02 — LANE-04: Skill `registry.lock` + Adapter CI

**Status:** Complete

## What the plan said, and what happened

The goal was goal-backward: *editing a skill's description, adding a `references/` file, or emitting
a skill to only one runtime must FAIL a gate.* Before this plan all three passed `emit-drift` green.
All three now fail, each with its own mutation proof.

## The demonstration — verbatim

**A drifted skill surface is CAUGHT:**

```sh
$ uv run python -m tools.skill_registry --check
skill-registry: OK — 18 skill(s) match the committed lock.
$ echo $?
0

# now change a skill's routing trigger — the one thing that decides which requests reach it
$ sed -i '' 's/Use when a write is blocked or you need to reason/Use when a write is blocked or you want to reason/' harness/skills/gate-model/SKILL.md
$ uv run python -m tools.skill_registry --check

FAIL: the skill surface has DRIFTED from its declaration in harness/skills/registry.lock.
  gate-model: description changed (it is the skill's routing trigger)
  gate-model: source file changed: SKILL.md

If the change is intended, re-declare it so the move is deliberate and reviewable:

    uv run python -m tools.skill_registry --write

then commit the regenerated lock.
$ echo $?
1
```

The same comparison also runs inside the suite (`tools/harness_lint/tests/test_skill_registry_lock.py`)
and as the `registry-lock` CI job, so it is caught locally *and* at the fan-in.

Each of the three escapes has a dedicated mutation proof on a **copied** tree:

```sh
uv run pytest tools/skill_registry -q -k "description_rewrite or new_reference_file or half_emitted"
```

## Why this is not a duplicate of `emit-drift`

`emit-drift` re-runs the emitter and diffs. It asks *"is the emitted tree a faithful projection of
the current source?"* — and it is blind **by construction** to a change in what that source
*declares*, because it re-derives its expectation from the same source it is checking. `registry.lock`
asks the other question: *"does the skill surface still match its declaration?"* Three concrete
escapes:

1. **A description rewrite.** The description is the routing trigger — it decides which requests
   reach the skill at all. Editing it re-emits cleanly to both trees; `emit-drift` stays green.
2. **A new `references/` file.** The emitter discovers that subtree by glob, so a file added to it is
   emitted and manifested with no declaration moving.
3. **A half-emitted surface.** A skill present in one runtime lane and absent from the other is still
   a self-consistent re-emit; only declaring the expected **pair** catches it.

`caps.EXPECTED_SKILLS` already catches an added or removed skill *name*, and nothing else.

## Reused vs built

| Reused | Built |
|---|---|
| `tools.harness_emit.manifest.load_manifest` over the committed `emit-manifest.json` — the emitted-path column is **read**, never recomputed, so there is no second copy of the emit layout | `tools/skill_registry/` — `build_registry`, `dumps`, `load_lock`, `diff_lock`, `write_lock`, CLI |
| the `manifest.prune_then_write` determinism contract (`sort_keys=True, indent=2`, trailing LF) | `harness/skills/registry.lock` (226 lines, 18 skills) |
| `tools.harness_lint.parse_frontmatter` — no second YAML reader | the `registry-lock` CI job + fan-in `needs` entry |
| the `emit-drift` / `drift` / `stale-derived` job shape and message discipline | `test_skill_registry_lock.py` in-suite gate |
| `project_skill.iter_reference_files`' symlink/escape traversal defence | |

Deliberately **not** reused: `tools/contract_hash`'s RFC 8785 canonicalization. Skill sources are
Markdown, not JSON documents; raw-byte SHA-256 is the correct digest and `contract_hash` stays the
sole owner of JSON canonicalization.

## What the lock records, per skill

`description_sha256` · `sources` (path → SHA-256 of raw bytes, whole skill directory) · `emitted`
(both runtime lanes) · `disciplines` (which lane disciplines name this skill — landing phase 36's
second deferred item, so a lane requirement cannot be silently repointed at a different procedure).

`diff_lock` names the skill **and the facet** that moved. A bare "the files differ" would be a gate
nobody acts on.

## Verification

`uv run pytest tools/skill_registry` **alone** → 20 passed (isolatability confirmed, not assumed).
`--write` on an unchanged tree is a byte-identical no-op — the determinism proof, asserted as a test
rather than intended. The lock lives at `harness/skills/registry.lock`, beside the skill tree rather
than inside any skill directory, so it never hashes itself; re-running the emitter after adding it
left `git status --porcelain` empty, confirming the emitter does not sweep it up.

## Deviations

None.
