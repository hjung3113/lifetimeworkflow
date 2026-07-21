# Phase 30: Deny-Domain Registry *(v2.4 A)* — Research

**Requirement:** SEAL-01 (`.planning/REQUIREMENTS.md:18-25`)
**Roadmap entry:** `.planning/ROADMAP.md:109-113`
**Ratified design:** `.planning/research/v2.4-scoping-FINAL.md:61-66` (Theme A) and `:38-41`
("the deny domains are deliberately separate and must stay separate")

**Confidence: HIGH on repo machinery.** Every file:line below was read from source in this session.
Nothing about the opencode *runtime* was executed — there is no opencode runtime in this container,
and the adapters are authored-only (`.opencode/plugin/ledger-guard.ts:4-8`).

---

## Summary

The harness has **three** path-deny enforcement domains, each with its own constant, its own owner
module, and its own bypass semantics. They are already disjoint and already documented as
deliberately disjoint. What does **not** exist is any single place where the three are *declared*,
and therefore no gate that fails when a hook's live constant drifts from what the harness claims
about it.

There is a fourth glob set spelled `SECRET_PATH_GLOBS` (`tools/adoption_scan/scan.py:54`) that is
**not** an enforcement domain and is deliberately wider than the hook's. An inventory that omits it
would be honest-but-incomplete; an inventory that lists it as a deny domain would be false. It must
appear as a declared **non-enforcing** glob set with a stated reason — that is the SEAL-01 shape
("the field that makes the gap visible as DATA").

---

## The three domains, exactly as they exist today

### Domain 1 — constitution

| Field | Live value | Citation |
|-------|-----------|----------|
| owner constant | `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**", "docs/glossary.md"]` | `tools/hooks/contract_guard.py:53` |
| declared by | ADR-0001 §Decision — the four members; a member may not be added or dropped without a superseding ADR | `tools/hooks/contract_guard.py:44-47`; `AGENTS.md:76-82` |
| bypass 1 | `GOLDEN_APPROVE_HUMAN`, non-empty/non-blank only | `contract_guard.py:57`, `:114` |
| bypass 2 | `HARNESS_DEV_BYPASS` via `dev_bypassed()`, emits a stderr dev-note and never claims human approval | `contract_guard.py:115`, `:119-128` |
| second deny axis | on-write byte hygiene via `lint_bytes` even when approved | `contract_guard.py:94-101` |
| Claude surface | `PreToolUse` matcher `Write|Edit` | `.claude/settings.json:121,125`; emitter source `tools/harness_emit/merge.py:126-133` |
| opencode surface | `tool.execute.before`, guard `input.tool !== "write" && input.tool !== "edit"` | `.opencode/plugin/contract-guard.ts:70` |
| second enforcement site | `apply.py` refuses a constitution destination in the adoption-apply write path | `tools/adoption_apply/apply.py:51`, `:112` |
| importers (never re-declared) | `tools/adoption_scan/destinations.py:87`, `tools/docs_guard/exclusions.py:46`, `tools/docs_guard/registry.py:46`, `tools/adoption_apply/apply.py:51` | — |
| existing pin test | `test_every_declared_plane_member_is_independently_enforced` — deletes each member in turn and asserts its own probe stops denying | `tools/hooks/tests/test_contract_guard.py:352-381` |

### Domain 2 — secret (path axis)

| Field | Live value | Citation |
|-------|-----------|----------|
| owner constant | `SECRET_PATH_GLOBS = ["*.env", "**/*.env"]` | `tools/hooks/secret_scan.py:37` |
| bypasses | **none** — `main()` never calls `dev_bypassed()` and reads no approval env | `secret_scan.py:81-91` |
| second deny axis | content patterns, **hardcoded** in the module | `secret_scan.py:44-48` |
| Claude surface | `PreToolUse` matcher `Read|Write|Edit` | `.claude/settings.json:131,135`; emitter `merge.py:135-143` |
| opencode surface | `input.tool !== "read" && !== "write" && !== "edit"` | `.opencode/plugin/secret-scan.ts:70` |
| disjointness rule | deliberately excludes the constitution plane so any-deny-wins cannot shadow `GOLDEN_APPROVE_HUMAN` | `secret_scan.py:15-20`; `contract_guard.py:16-20` |

**The SEAL-04 debt is visible here and belongs in the registry as data.** The content patterns at
`secret_scan.py:44-48` are a *fork* of `contracts/harness/task-control/gate-registry.json:10-19`,
which is already the single source for `tools/adoption_scan/scan.py:48` and
`tools/evidence/capture.py:24`. The two lists genuinely differ today — the hook has 3 patterns, the
contract has 8.

### Domain 3 — review ledger

| Field | Live value | Citation |
|-------|-----------|----------|
| owner constant | `REVIEW_LEDGER_GLOBS = ["docs/.docs-review-ledger.toml"]` | `tools/hooks/ledger_guard.py:48` |
| bypasses | **none, by design** — honours neither `GOLDEN_APPROVE_HUMAN` nor `HARNESS_DEV_BYPASS` | `ledger_guard.py:26-30`; ADR-0010 `docs/adr/0010-human-docs-review-obligation-model.md:163-166` |
| declared by | ADR-0010 clause 3b, three-layer table | `docs/adr/0010-...md:141-152` |
| layer 1 | this hook, `PreToolUse` matcher `Write|Edit` | `.claude/settings.json:161,165`; emitter `merge.py:144-158` |
| layer 2 | `refuse_unsafe_destination` → `ReviewLedgerRefusal` (not a `ConstitutionRefusal` subclass) | `tools/adoption_apply/apply.py:65`, `:227` |
| layer 3 | `first_seen-unratified` — greenness only, not a write gate | `tools/docs_guard/ledger.py` (reason string listed in `tools/docs_guard/cli.py:72-107`) |
| opencode surface | `input.tool !== "write" && input.tool !== "edit"` | `.opencode/plugin/ledger-guard.ts:70` |
| existing disjointness test | asserts the ledger is denied by `REVIEW_LEDGER_GLOBS` and by *neither* of the other two, and that the ledger globs are a subset of the matrix `path_deny_globs` | `tools/adoption_apply/tests/test_constitution_refusal.py:528-531,576` |

---

## What is NOT a deny domain (and must be declared as such)

| Glob set | Where | Why it is not a domain |
|----------|-------|------------------------|
| `SECRET_PATH_GLOBS = ["*.env","**/*.env","*.pem","*.key","id_rsa*",".npmrc",".netrc"]` | `tools/adoption_scan/scan.py:54` | Deliberately module-own and wider; drives brownfield **classification**, not a write deny. The module states this at `:14-15,53`. Same identifier, different set — the single most likely place for a reader to conclude `*.pem` is denied on write. It is not. |
| `DERIVED_GLOBS` | `tools/docs_guard/exclusions.py` | Exclusion/classification set for the docs guard's uncovered ratchet. No enforcement. |
| `commit_gate` | `tools/hooks/commit_gate.py:1-24` | **Enumerates no paths at all.** It composes contract-drift + polyglot §4.3-4.6 over staged `*.tsv` + golden parity. Modelling it as a path-deny site would be a fabricated row. |
| `harness/permission-matrix.json:27-35` `path_deny_globs` | matrix | **Data, not a layer.** `tools.harness_emit.permissions` strips the key from the emitted `opencode.json` as resolver-only. ADR-0010 `:154-160` records this explicitly: "a layer that is only a data row is a claimed control that does not exist." |

The matrix union at `harness/permission-matrix.json:27-35` is exactly the concatenation of the three
live constants (7 entries: 4 + 2 + 1) — verified by reading both. **That equality is currently
unasserted anywhere.** A drift test that checks it in both directions is the cheapest control that
catches the ADR-0010 failure shape recurring.

---

## Where the registry should live

`contracts/harness/task-control/gate-registry.json` is the precedent the requirement names, and it
is a **data contract with no sibling schema**, registered explicitly in
`tools/contract_hash/hash.py:29-32` `DATA_CONTRACT_PATHS` so the RFC 8785 drift gate covers it.

Two facts that decide the shape:

1. **`contract-check` (CI) validates `<name>.schema.json` against a sibling `<name>.{yaml,yml,json}`**
   (`.github/workflows/ci.yml:108-127`). There are **zero** such pairs in the repo today — every
   schema is convention-only, so that job currently prints its VISIBLE SKIP line (`ci.yml:121-123`).
   Authoring `deny-domains.schema.json` + `deny-domains.json` as siblings makes that job
   non-vacuous for the first time.
2. **`tools.docs_sync` generates one `docs/reference/<stem>.md` per `*.schema.json`**
   (`tools/docs_sync/generate.py:30-40`). A schema therefore also costs a derived page, a
   contracts-index row, and two syrupy snapshots — the exact five-artifact atomic commit shape of
   `28-01-PLAN.md`.

**Verified non-breakage:** `tools/contract_hash/tests/test_hash.py:93-101` asserts the
`DATA_CONTRACT_PATHS` set against a *tmp* contracts tree and only counts files that exist there
(`hash.py:57` — `if (root / rel).is_file()`). Adding a third entry pointing at
`harness/security/deny-domains.json` therefore does **not** break that test.

---

## The drift test — what it can actually falsify

`tools/harness_lint/` is a virtual uv member with **no external deps**
(`tools/harness_lint/pyproject.toml`), imported by module path with the repo root pushed onto
`sys.path` by `tools/harness_lint/tests/conftest.py:19-22`. House style is a structural scan over
the real config, asserting agreement and failing loud
(`tools/harness_lint/tests/test_contract_graph_config.py:1-13`).

Seven checks are available, each falsifiable by a mutation:

| # | Check | Mutation that must make it RED |
|---|-------|-------------------------------|
| 1 | declared `globs` == the live constant, element-wise and ordered | delete `"golden/**"` from `contract_guard.CONSTITUTION_GLOBS` |
| 2 | `owner_module` + `owner_constant` resolve via `importlib` | rename the constant |
| 3 | domains pairwise disjoint over each domain's own probe corpus | add `docs/.docs-review-ledger.toml` to `CONSTITUTION_GLOBS` |
| 4 | matrix `path_deny_globs` == the union of the declared domains, **both directions** | add an unowned glob to the matrix (the ADR-0010 inert-data shape) |
| 5 | declared `bypasses` match live behaviour, driven through `decide()`/`main()` with env set — never a static read | make `ledger_guard.main()` honour `HARNESS_DEV_BYPASS` |
| 6 | declared Claude surfaces == the matcher on that hook's group in `merge.HARNESS_HOOK_GROUPS` | change `secret_scan`'s matcher from `Read|Write|Edit` to `Write|Edit` |
| 7 | declared opencode surfaces == the tool names in the adapter's `input.tool !== "…"` chain | delete `"edit"` from `.opencode/plugin/ledger-guard.ts:70` |

Check 5 is the one that matters most and the one most likely to be written wrong. A static read of
the module source ("does the file contain the string `dev_bypassed`?") is the failure mode named at
28-RESEARCH P4 — it goes green on an unused import. The check must set the env var and call the
hook's `decide()`/`main()` path.

Check 6 must read `tools.harness_emit.merge.HARNESS_HOOK_GROUPS`, **not** `.claude/settings.json`.
The emitter is the source; the settings file is its projection, and `emit-drift`
(`.github/workflows/ci.yml:218`) already gates the projection.

---

## Common pitfalls for this phase

**P1 — the registry becomes a fourth copy of the globs.** Three modules already import
`CONSTITUTION_GLOBS` rather than re-typing it (`destinations.py:87`, `exclusions.py:46`,
`apply.py:51`). The registry is a *declaration to compare against*, so it necessarily restates the
values — that is what makes drift detectable. The hooks must keep importing nothing from it, or the
comparison becomes a tautology (`x == x`). **The hooks stay the SSOT; the registry is the claim.**

**P2 — a test that only re-reads the JSON.** ADR-0010 `:158-160` names this exactly: "a test that
only re-reads the matrix proves the file's content, not the enforcement." Every declared *behaviour*
field (bypasses, surfaces) needs a live drive, not a file read.

**P3 — the constitution commit that half-lands.** Schema + instance + hash rebaseline + docs_sync
page + contracts-index + snapshots must land together or `drift` (`ci.yml:133`) or `stale-derived`
(`ci.yml:227`) reds. This is 28-RESEARCH P1, unchanged.

**P4 — proposing a docs binding reds the branch until a human acts.** A new `[[binding]]` row in
`docs/doc-dependencies.toml` with no ledger row classifies `first_seen-unratified`
(`tools/docs_guard/cli.py:72-107`), and the ledger is agent-deny with no token
(`ledger_guard.py:26-30`). That is correct behaviour, not a bug — but it must be planned as a
blocking-human task, not discovered at CI.

**P5 — editing a hook to add a "see the registry" comment fires a review obligation.**
`docs/doc-dependencies.toml` binds `tools/hooks/contract_guard.py` → `.memory/README.md` at
`severity = "required"`. Verified: no binding names `secret_scan.py` or `ledger_guard.py`, and none
names `tools/harness_lint/**` or `tools/contract_hash/**`. Phase 30 as planned touches **none** of
the bound sources, so **no existing review obligation fires**.

---

## Environment availability

- `uv` present; `uv run pytest` is the suite entry (`AGENTS.md:53`).
- No .NET SDK assumed; nothing in this phase needs it.
- No opencode runtime — adapters are source-authored only, so check 7 is a **source parse**, never
  an execution (`.opencode/plugin/ledger-guard.ts:4-8`).
- Zero new external packages. `importlib`, `json`, `re`, `pathlib` are stdlib. Package Legitimacy
  Gate: **not applicable**.

---

## Disagreements between the ratified design and the live code

Reported, not smoothed.

1. **SEAL-03's cited line numbers are stale.** `.planning/REQUIREMENTS.md:36-38` cites
   `.claude/settings.json:121,160`. Live: `:121` is the `contract_guard` group's matcher (correct)
   but the ledger group's matcher is `:161` and its command `:165`. `.opencode/plugin/ledger-guard.ts:65,70`
   is cited; `:65` is a comment line and `:70` is the tool guard. Cosmetic, but the phase-32 plan
   should re-derive rather than copy.
2. **The scoping doc says "three path-deny domains"; the live code has three *enforcing* domains and
   a fourth identically-named non-enforcing glob set** (`adoption_scan/scan.py:54`). SEAL-01 as
   written would produce a registry that is silent about it. Recommended resolution: declare it in a
   `non_enforcing_glob_sets` section. Recorded as decision D-06.
3. **`secret_scan` has a second deny axis the requirement's field list does not model.**
   SEAL-01 enumerates path-deny domains; `secret_scan.py:44-48` also denies on *content*. A registry
   that lists only `SECRET_PATH_GLOBS` under-describes its own owner module. Recommended resolution:
   a `content_axis` field recording that the patterns are hardcoded and that SEAL-04 (phase 33)
   moves them to `gate-registry.json`. This makes the carried debt visible as data — the same
   argument SEAL-01 makes for the bash gap.
4. **`apply.py:227` lowercases the path before matching the ledger globs**
   (`resolve_path(REVIEW_LEDGER_GLOBS, relative.lower())`); `ledger_guard.py:70` does not. The two
   layers therefore disagree on a mixed-case spelling of the ledger path. Not in SEAL-01's scope to
   fix — recorded here so phase 31's threat model inherits it rather than rediscovering it.

---

## Sources

All HIGH — read from source in this session:
`tools/hooks/contract_guard.py`, `tools/hooks/secret_scan.py`, `tools/hooks/ledger_guard.py`,
`tools/hooks/commit_gate.py:1-45`, `tools/harness_perms/resolver.py`,
`harness/permission-matrix.json`, `tools/harness_emit/merge.py:80-175`,
`.opencode/plugin/{contract-guard,secret-scan,ledger-guard}.ts`, `.claude/settings.json` (hook
groups), `tools/contract_hash/hash.py:1-60`, `tools/contract_hash/tests/test_hash.py:88-101`,
`contracts/harness/task-control/gate-registry.json`, `docs/doc-dependencies.toml`,
`docs/adr/0010-human-docs-review-obligation-model.md:120-175`, `.github/workflows/ci.yml:95-135,218-310`,
`tools/harness_lint/{pyproject.toml,tests/conftest.py,tests/test_contract_graph_config.py}`,
`tools/adoption_scan/scan.py:48-54`, `tools/adoption_apply/apply.py:51-65,112,227`,
`tools/adoption_apply/tests/test_constitution_refusal.py:528-576`, `pyproject.toml:29-35`,
`uv.lock` (workspace member list).
