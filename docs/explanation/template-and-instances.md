# Template and instances

*Diátaxis quadrant: **understanding-oriented**. Hand-authored (constitution plane). Records the
narrative behind [ADR-0002](../adr/0002-general-template-de-specialization.md).*

## Why this repo is a template, not a product

This repo began as a *log-parser-specific* harness. It is now a **reusable, contract-first polyglot
agent-harness template**: the machinery that makes a polyglot pipeline safe — contract-first schemas,
the §4.3–4.6 normalization boundary, golden equivalence, drift and commit gates, the two-plane memory
— is **domain-neutral** and reusable, while the semiconductor equipment-log domain that seeded it is
just **one instance** of that machinery.

Keeping the two separate is what makes the repo cloneable as a starting point for a *different*
domain without dragging semiconductor specifics along. The split is enforced, not merely documented
(see *The one-directional invariant* below).

## The two halves

| Half | Where | Contents | On clone |
|------|-------|----------|----------|
| **Harness core** (domain-neutral) | repo root | `contracts/` (generic default), `libs/python` §4.3–4.6 normalize core + `libs/normalize-{spec.md,fixtures}`, `tools/`, `harness/`, `docs/`, the gates | **stays** |
| **Instance** (domain seed) | `examples/<name>/` | its own `contracts/`, `golden/`, `components/`, language-side normalize twin, `tests/`, manifest | **swap/remove** |

The **reference instance** is [`examples/log-parser/`](../../examples/log-parser/README.md) — the
semiconductor equipment-log domain. It depends on the core; the core never depends on it.

## The normalize split (the subtle part)

Normalization spans the language boundary, so ADR-0002 splits it deliberately:

- **Stays in core:** `libs/python/normalize` + `libs/normalize-spec.md` + `libs/normalize-fixtures`.
  The Python impl is the harness's own **language-neutral** §4.3–4.6 tooling — a uv workspace member
  imported by the core tool `polyglot_lint` and, in the other direction, by the *instance*-side
  golden runner that Phase 44 relocated into the overlay, and the shared `(raw, canonical)`
  fixture corpus cross-validates *any* language-side twin. "Core is language-neutral" keeps this in.
- **Moves to the instance:** `libs/dotnet/Normalize*`. It is the *example's* language-side
  implementation — no core Python tool imports it, and it is **not** a uv member. Because it is .NET
  (a specific language choice), it belongs to the instance that chose .NET, not to the neutral core.

> Note the reason for the .NET twin moving is **"core is language-neutral"**, *not* any uv/packaging
> reason — it is not a uv member precisely *because* it is instance-specific, which is a consequence,
> not the cause.

## The language/toolchain slot

The core hardcodes no language. The active instance declares its toolchains as **data** in
`harness/project.toml`:

```toml
[instance]
root = ""            # "" = the generic default; an instance sets e.g. root = "examples/log-parser"

[[languages]]
id = "dotnet"        # the example supplies .NET 10 (parser/converter) ...
[[languages]]
id = "python"        # ... and Python/uv (scheduler/collector)
```

A downstream template consumer swaps the instance and this slot; the permission matrix and personas
are checked against it by the GEN-03 consistency test.

## The one-directional invariant

The template only works if the core cannot reach into an instance. That is enforced by the GEN-04
guard `tools/harness_lint/tests/test_core_no_example_dep.py`, which scans every tracked file under
`tools/`, `harness/`, `libs/` and fails the suite on any `examples/` path reference, `import
examples`, or surviving `components/toy-converter` reference. A live negative-control proves the
scan cannot silently no-op.

There is **one** sanctioned exception, and it is a place rather than a line: the instance-config
slot in `harness/project.toml`, which by ADR-0002 (c) is `[instance]` plus `[[languages]]`. Three
pointer-key classes inside that slot are exempt, because each is a single line whose whole job is to
name the instance:

| Key | Example value | Why exempt |
|-----|---------------|------------|
| `root` | `examples/log-parser` | the instance-tree pointer itself |
| `persona` | `examples/log-parser/agents/dotnet-engineer.md` | points at the instance's language-side engineer |
| `test_paths` | the instance's CI test targets | the Phase-6 test-target data slot |

The guard spells this as `_INSTANCE_POINTER_LINE = re.compile(r"\s*(root|persona|test_paths)\s*=")`,
and each class carries its own positive test (`test_instance_root_pointer_is_exempt`,
`test_instance_pointer_persona_is_exempt`, `test_instance_pointer_test_paths_is_exempt`). Naming
only `root` here would describe a narrower contract than the one in force and imply the other two
were drift — they are not.

## How to add an instance

1. **Create the tree:** `examples/<name>/` with its own `contracts/` (JSON Schema + YAML specs),
   `golden/` baselines, any `components/` and language-side normalize twin, and `tests/`.
2. **Give it a contract manifest:** an `contracts/.hashes/manifest.json` for the instance so the
   drift gate can hash its schemas independently of the core default.
3. **Declare its languages:** set `[instance] root = "examples/<name>"` and the `[[languages]]`
   tables in `harness/project.toml`; keep the permission matrix + personas consistent (GEN-03 test).
4. **Reuse the core:** point the golden runner at the instance's converter and goldens; use the
   `libs/python/normalize` core + `libs/normalize-fixtures` corpus — never add a second normalizer.
5. **Stay one-directional:** the instance imports/uses the core; the core must not reference the
   instance (the GEN-04 guard will fail the suite if it does).
6. **Add nearest-wins rules:** an `examples/<name>/AGENTS.md` that restates the non-negotiables and
   any instance-local rules.

## See also

- [ADR-0002 — General Template De-specialization](../adr/0002-general-template-de-specialization.md)
- [ADR-0001 — Walking-Skeleton Golden Core Architecture](../adr/0001-walking-skeleton-golden-core.md) (complemented, not superseded)
- [`examples/log-parser/README.md`](../../examples/log-parser/README.md) · [`examples/log-parser/AGENTS.md`](../../examples/log-parser/AGENTS.md)
