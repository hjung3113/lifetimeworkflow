# Phase 13: Injector Reframe + Channel Wiring (v2.1 B) — Research

**Researched:** 2026-07-15
**Domain:** Deterministic payload assembly (Python) — `tools/memory_regen/inject.py`; two-plane memory wiring
**Confidence:** HIGH (all claims are `file:line`-cited against the working tree; budget arithmetic is *measured*, not estimated)

## Summary

Phase 13 is a **single-file refactor with a large blast radius of prose**. The real work lives in
`tools/memory_regen/inject.py` (148 lines) — a new priority-0 working-agreements directive composed
from `.memory/agreements/*`, a reworded data-scoped banner, and a reworded progress-log pointer that
surfaces a verbatim `updated:` stamp. Everything else (checkpoint write path, state-file shape, tests,
`/orient` prose) is satellite work.

Three findings dominate planning:

1. **The determinism safety net does not exist.** `inject.py:20-22` *claims* "delete+regen identical",
   but there is **no byte-identity test for `assemble()`** anywhere in the repo. `test_inject_assembler.py`
   tests budget/priority/pointer-only — never determinism. SC2 cannot be "preserved"; it must be **built
   first** (Wave 0), modelled on `tools/docs_sync/tests/test_docs_sync_determinism.py:43`.
2. **`.memory/agreements/` currently contains zero active agreements** — only `_TEMPLATE.md` (which
   carries `status: active` at `_TEMPLATE.md:2` — a live trap: naive globbing injects the template as a
   real directive) and `README.md`. Composition needs an explicit exclusion rule + `sorted()` iteration.
3. **The emit snapshot gate is ALREADY RED** — inherited from Phase 12, not caused by Phase 13. Do not
   "fix" it (Phase 15 owns it). See §Scope Fence.

**Primary recommendation:** Sequence as Wave 1 = {state-stamp/checkpoint write path ‖ determinism-test
backfill}, Wave 2 = the single-file `inject.py` reframe. Cap the agreements block at **N=6 entries /
M=700 chars** (measured headroom is 784) with whole-block overflow-to-pointer.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Agreements composition + cap | `tools/memory_regen/inject.py` (assembler) | — | `assemble()` is the single injection contract (D-01); both runtimes consume it |
| `updated:` stamp **write** | `/checkpoint` (`harness/commands/checkpoint.md`) | `.memory/state/*.md` | Write path is a command; state plane is committed |
| `updated:` stamp **read/surface** | `inject.py::_active_context_pointer` | — | Must be verbatim — read-only, no wall-clock |
| Freshness **judgement** | Agent (session context) | — | Q6: agent-side, no fixed threshold, no hook wall-clock |
| Runtime envelope | `.claude/hooks/memory-inject.sh` / `harness/plugins/session-inject.ts` | — | Envelope only — **no logic** (D-01) |
| Emit round-trip of changed prose | `tools/harness_emit` | — | **Phase 15**, NOT Phase 13 |

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MEM2-02 | Two distinct blocks: full-body capped agreements directive at priority-0 + data-scoped provenance banner; activeContext pointer reworded; determinism + 4000-char budget preserved | §1 Priority Renumbering, §2 Cap, §4 Composition, §6 Rewording |
| MEM2-05 | `updated: <ISO-date>` stamp written by `/checkpoint`, surfaced verbatim by `assemble()`; no wall-clock in `assemble()` or hook wrapper; progress tight by design (§7a) | §5 Stamp Round-Trip, §3 Determinism |

---

## Locked Decisions (from §7 + REQUIREMENTS.md:6 — do NOT re-litigate)

`.planning/REQUIREMENTS.md:6` records the kickoff decisions verbatim:

> **Kickoff decisions (2026-07-14):** Q1=committed-but-writable · Q2=dedicated `/agree` · Q3=per-guideline files · Q4=capped full-body · Q5=retire via per-file status · Q6=agent-side freshness (no fixed threshold).

| Decision | Status | Consequence for Phase 13 |
|---|---|---|
| Per-guideline files `.memory/agreements/<slug>.md` (§7b) | **LOCKED** | Composer reads a *directory*, not one file |
| Retire = flip `status` to retired, never delete (§7b, Q5) | **LOCKED** | Active-set filter is `status == active` |
| Progress tight: in-flight + remaining + short last-N-done (§7a) | **LOCKED** | No done-log accumulation |
| Full completed history lives in git (§7a) | **LOCKED** | Pointer prose should say so |
| Agreements link to ADRs, never restate (§7c) | **LOCKED** | Not enforced here (Phase 14 lint) |
| Q4 = capped full-body | **LOCKED (values open)** | N/M values → §2, NEEDS OPERATOR RATIFICATION |
| Q6 = agent-side freshness, no threshold | **LOCKED** | No wall-clock in `assemble()` **or** hook wrapper |

---

## §1. Priority Renumbering — every site that must change

### Current order (`inject.py:13-17`, docstring)

```
    (0) provisional banner   — NEVER dropped (D-02)
    (1) live drift summary   — NEVER dropped (reuses tools.contract_drift.run_gate)
    (2) contracts-index summary   (head of .memory/derived/contracts-index.md if present)
    (3) repo-map top-N            (head of .memory/derived/repo-map.md if present, else omitted)
    (4) activeContext POINTER     (path + one-line note — never the file body, P13)
```

Encoded in code at `inject.py:118-124` (the `sections` list) and the never-drop guard at
`inject.py:131`: `if name not in ("banner", "drift") and used + addition > budget_chars:`.

### Recommended resulting order

| New prio | Section | Never dropped? | Change |
|---|---|---|---|
| **0** | **Working-agreements directive** (`agreements`) | **YES** | **NEW** (capped; whole-block → pointer on overflow) |
| 1 | Data-provenance banner (`banner`) | YES | Reworded text (§6) |
| 2 | Live drift summary (`drift`) | YES | unchanged |
| 3 | Contracts-index summary | no | unchanged |
| 4 | Repo-map top-N | no | unchanged |
| 5 | **Progress-log pointer** (`active`) | no | Reworded + verbatim `updated:` stamp (§5) |

Never-drop guard becomes `if name not in ("agreements", "banner", "drift")`. The agreements block is
never-dropped **because it is already self-capped** — the cap is what makes never-dropping safe.

**Emission-order note.** SC1 says agreements is "a NEW priority-0". In the current design, list order ==
priority == emission order (`inject.py:118-135`), so the directive is emitted **first** and the banner
second. This **intentionally retires the "banner-first" D-02 phrasing** in favour of *directive-first,
banner-second*. When there are **zero active agreements the block is omitted entirely** (recommended —
no `"none recorded yet"` filler), so the banner is the first line again. That is the state **today**
(the dir holds only `_TEMPLATE.md` + `README.md`, both excluded), which keeps the blast radius small.

### Every site hardcoding the current order — exhaustive

| # | Site | What breaks |
|---|---|---|
| 1 | `inject.py:13-17` | Docstring priority list |
| 2 | `inject.py:41-44` | `BANNER` constant text |
| 3 | `inject.py:48` | `ACTIVE_HEADER = "## Active context (pointer)"` |
| 4 | `inject.py:94-99` | `_active_context_pointer` (+ its `noqa: ARG001` — `state_dir` becomes *used*) |
| 5 | `inject.py:110-116` | `assemble()` docstring ("Banner (0) and drift (1) are always present") |
| 6 | `inject.py:118-124` | `sections` list |
| 7 | `inject.py:131` | never-drop tuple `("banner", "drift")` |
| 8 | `tests/test_inject_assembler.py:19-24` | `test_first_line_is_provisional_banner` — asserts `first == inject.BANNER` **and** `"provisional" in first.lower()` → **RED** |
| 9 | `tests/test_inject_assembler.py:27-34` | `test_banner_asserts_adr_contract_override` — asserts `"provisional" in banner` → **RED** |
| 10 | `tests/test_inject_assembler.py:71` | `mandatory = len(BANNER) + len(_drift_summary()) + 1` — mandatory set grows |
| 11 | `tests/test_inject_assembler.py:116-122` | `test_main_prints_banner_first` → **RED** |
| 12 | `tests/test_inject_assembler.py:94-103` | `test_active_context_is_pointer_not_body` — still valid, but its `"## In flight"` marker guard must survive the §7a state rewrite |
| 13 | `harness/commands/orient.md:25-27` | "provisional banner → live contract-drift → …" prose |
| 14 | `harness/commands/orient.md:45` | "Provisional-banner-first: `.memory/` is a hint, not truth" |
| 15 | `harness/commands/orient.md:37` | "provisional; contracts/ADR override it" |
| 16 | `harness/plugins/session-inject.ts:13` | "same provisional banner" comment |
| 17 | `.claude/commands/orient.md:21` (generated) | **Phase 15** — do not hand-edit |
| 18 | `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr:1480,1525` | Embeds orient.md text — see §Scope Fence |

`grep -rln "BANNER\|ACTIVE_HEADER\|inject.assemble"` confirms only `inject.py` +
`test_inject_assembler.py` reference the constants programmatically — sites 13–18 are prose/snapshot.

---

## §2. The Cap (Q4 values) — measured arithmetic

`Q4=capped full-body` is **locked**; the N/M values are not. This is a **RECOMMENDATION —
NEEDS OPERATOR RATIFICATION**.

### Measured section sizes (real, this working tree, 2026-07-15)

Measured via `uv run python -c "from tools.memory_regen import inject; ..."`:

| Section | Chars (today) | Notes |
|---|---|---|
| `BANNER` (current) | **133** | `inject.py:41-44` |
| `_drift_summary()` | **79** | clean path; DRIFT path grows ~1 line/schema (`inject.py:62`) |
| `_contracts_summary()` | **501** | 2 contracts; head-capped at `_HEAD_LINES = 20` (`inject.py:38`) |
| `_repo_map_topN()` | **2116** | 21 lines; **0 when absent** (gitignored — `.gitignore:23`) |
| `_active_context_pointer()` | **117** | `inject.py:96-99` |
| **`assemble()` total, repo-map present** | **2950** | headroom to 4000 = **1050** |
| `assemble()` total, repo-map absent | 833 | the common cold-container path |

> Caveat: repo-map is gitignored, so a fresh checkout measures 833 until
> `python -m tools.memory_regen.repo_map` runs. Plan against the **2950** (repo-map present) case —
> the SessionStart hook regenerates it first (`memory-inject.sh:36`).

### Headroom after the §6 rewording (measured)

The reworded texts are **longer** than what they replace — this eats headroom before any agreement:

| | Chars |
|---|---|
| Proposed `BANNER` (§6) | **316** (was 133, **+183**) |
| Proposed pointer + stamp (§6) | **200** (was 117, **+83**) |
| Base (drift + contracts + repo-map) | 2700 |
| **Payload after reword, zero agreements** | **3216** |
| **Headroom for the agreements block** | **784** |

### Recommendation: **N = 6 entries, M = 700 chars** (block total, header included)

Rationale — a realistic entry renders at ~96 chars:

```
- **Proceed when grounded** — act on grounded work; do not self-cancel or re-verify reflexively.
```

Header `## Working agreements (authoritative — honor these working-style directives)` = 76 chars.
So 6 entries + header = `76 + 6×97` = **658 ≤ 700**. ✓

| M | Payload total | Outcome |
|---|---|---|
| 600 | 3817 | OK — repo-map kept |
| **700 (rec.)** | **3917** | **OK — repo-map kept; 83 chars slack** |
| 800 | 4017 | OVER → repo-map (prio 4) priority-truncated → 1901 |
| 1200 | 4417 | OVER → repo-map dropped → 2301 |

**Why 700 is the defensible knee:** it is the largest round cap that still lets the full payload
(banner + drift + contracts-index + **repo-map** + pointer) coexist under 4000. At M≥800 the repo-map is
silently dropped **every session** — a real capability regression traded for agreement space. M is the
binding guard; N=6 is a *curation/readability* guard (a verbose entry trips M before N — correct).

**Self-healing property:** if `contracts/` grows and the contracts-index head approaches its 20-line
ceiling (~2200 chars), the payload exceeds 4000 and repo-map drops **gracefully** via the existing
priority-truncate (`inject.py:131`). The design degrades correctly without a cap change.

### Overflow degradation rule (precise)

```
active = [a for a in agreements if a.status == "active"]         # sorted by filename
block  = HEADER + "\n" + "\n".join(render(a) for a in active)
if len(active) == 0:            -> emit nothing (section omitted entirely)
elif len(active) > N            -> POINTER
elif len(block)  > M            -> POINTER
else                            -> block
```

Where `POINTER` is a fixed, deterministic, *countless* string. **Do not interpolate the count** —
`f"{len(active)} active agreements"` makes the payload churn on every add/retire and needlessly
couples the injected bytes to the directory size:

```
## Working agreements (authoritative — honor these working-style directives)
.memory/agreements/ — active agreements exceed the inject cap; read them before acting.
```

Degradation is **whole-block, all-or-nothing** — never a partial entry list, never a mid-line cut.
This preserves the D-07 "priority-truncate, never mid-line" invariant (`inject.py:19-21`) and keeps
the block a single deterministic function of the active set.

**If the operator disagrees with N/M:** the values must be module-level named constants
(`_AGREEMENTS_MAX_ENTRIES = 6`, `_AGREEMENTS_MAX_CHARS = 700`) and `assemble()` must accept an
`agreements_dir` parameter, so re-ratification is a one-line constant edit + a test-fixture change,
not a refactor. Plan for the constants regardless of the ratified values.

---

## §3. Determinism — the hazards and the exact defenses

### How byte-identity is tested today: **IT IS NOT**

`inject.py:20-22` asserts the contract:

> ```
> pointers only — never a full contract schema body (T-02-06). No timestamps, no secrets, so the
> output is deterministic (delete+regen identical).
> ```

But `grep -rn "determinis\|byte-identical\|identical" tools/ --include="*.py"` returns **zero hits in
`tools/memory_regen/tests/`** for the assembler. `test_inject_assembler.py` (123 lines) covers banner,
budget, priority-truncate, pointer-only, CLI — **no determinism assertion**. The only nearby determinism
tests are `test_repo_map_determinism.py` (a *different* module) and the canonical model,
`tools/docs_sync/tests/test_docs_sync_determinism.py:43`:

```python
def test_generate_delete_regenerate_is_byte_identical(tmp_path: Path) -> None:
    """generate → sha256 → delete → regenerate → identical hashes.
    (NOT git diff), against tmp_path."""
    out = tmp_path / "reference"
    first = docs_sync.write(out=out)
    digest_1 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in first}
    for p in first:
        p.unlink()
        assert not p.exists()
    second = docs_sync.write(out=out)
    digest_2 = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in second}
    assert digest_1 == digest_2
```

**Implication for the planner:** SC2 says determinism is "preserved". It cannot be preserved — it is
**unproven today**. The determinism test is a **Wave 0 gap** and must land *before* the reframe, so it
is a genuine regression net rather than a post-hoc rubber stamp. (I verified `assemble()` *is* in fact
deterministic today — two calls hash identically to `ffe87a9dd00864ae` — so the test will land green.)

### Hazard (a): directory iteration order — **the big one**

`Path.glob()` / `iterdir()` yield **filesystem order** (`readdir` order), which is *not* sorted and
varies across filesystems (APFS vs ext4), across containers, and after file rename/recreate. Composing
`.memory/agreements/*.md` with a bare `glob()` produces a payload whose section order is **environment-
dependent** — delete+regen on a different machine yields different bytes. This is the single most likely
way Phase 13 silently breaks the determinism contract.

**Defense:** `sorted(Path(agreements_dir).glob("*.md"))` — an established repo-wide precedent:
- `tools/harness_emit/generate.py:151` — `for path in sorted(root.glob("*.md")):`
- `tools/harness_emit/generate.py:191` — `for skill_md in sorted(root.glob("*/SKILL.md")):`
- `tools/memory_regen/repo_map.py:61` — `for p in sorted(root.rglob("*")):`
- `tools/memory_regen/contracts_index.py:75` — `for rel in sorted(manifest):`

Ordering rule: **sort by filename (slug), ascending, byte-wise** — stable, human-predictable, and
independent of frontmatter. Do **not** sort by `added:` date (ties are ambiguous → nondeterministic) and
do **not** sort by mtime (not committed, container-ephemeral).

### Hazard (b): the `updated:` stamp

`datetime.now()` / `date.today()` anywhere in `assemble()` destroys determinism **and** violates Q6.
The stamp must be **read verbatim** from the state file's frontmatter and interpolated as an opaque
string. `assemble()` must never parse it into a date, compare it, or format it.

**Defense:** a static test asserting the module's source contains no wall-clock symbols (§Validation
Architecture). Repo precedent for exactly this discipline: `tools/harness_emit/merge.py:16` — "no
`datetime.now()`/floats — so re-emit is byte-identical".

### Hazard (c): `_TEMPLATE.md` injected as a real agreement — **live trap**

`.memory/agreements/_TEMPLATE.md:2` reads `status: active # active | retired`. A naive
`glob("*.md")` + `status == active` filter **injects the template as a live directive**, rendering the
literal text `<One-line working-style or methodology rule.>` into a priority-0 block the agent is told
to honor. It also silently consumes 1 of N entries.

**Defense (three layers):**
1. Skip files whose name starts with `_` (template convention).
2. Skip `README.md` explicitly (it has *no* frontmatter → `parse_frontmatter` returns `({}, text)`, so
   `status` is absent → layer 3 also catches it).
3. Treat **missing/unparseable `status` as NOT active** (fail-closed). Only the exact string `active`
   admits an entry.

`tools/harness_emit/generate.py:147` sets the precedent: "are excluded. Frontmatter is read via the
shared `parse_frontmatter` — never re-slice fences."

### Hazard (d): CRLF / encoding

A hand-edited agreement saved CRLF would shift bytes. `parse_frontmatter` already normalizes:
`tools/harness_lint/frontmatter.py:40` — `text = md_text.replace("\r\n", "\n").replace("\r", "\n")`
("Normalize line endings so the fence scan is CRLF-safe (boundary invariant §4.3)"). **Reuse it; do not
re-slice fences.** Also read with explicit `encoding="utf-8"` (repo-wide convention, `inject.py:72`).

### Hazard (e): non-hermetic tests

`assemble()` defaults read the **real** `.memory/` (`inject.py:34-35`). A test that asserts on the live
agreements dir goes red the moment someone adds an agreement. `assemble()` already parameterizes
`derived_dir` / `state_dir` (`inject.py:105-109`) — **add `agreements_dir` as a peer parameter** and
point cap/overflow/ordering tests at `tmp_path`.

---

## §4. Agreements Composition — the Phase 12 shape

### Entry format (`.memory/agreements/_TEMPLATE.md`, verbatim)

```markdown
---
status: active # active | retired
added: YYYY-MM-DD
provenance: "added because <verbatim user feedback>"
---

# <Title — the working-agreement in a few words>

<One-line working-style or methodology rule.>

Related: [ADR-xxxx](../../docs/adr/0000-example.md) · [.planning/PROJECT.md § Key Decisions](../../.planning/PROJECT.md#key-decisions) <!-- LINK, never restate a project decision (§7c) -->
```

Contract restated at `.memory/agreements/README.md:8-12`:

> Its YAML frontmatter must contain `status:` (`active` or `retired`), `added:` (an ISO date), and
> `provenance:` (`"added because <verbatim user feedback>"`). Its body contains a title, one-line
> working-style or methodology rule, and a `Related:` link. Retire an agreement with
> `status: retired`; never delete it.

### Plane placement (be precise)

`.memory/agreements/` is the **PROCESS plane** — the *4th* plane. Per `.memory/README.md:16`:
committed ✅, regenerated ❌, "Human-authored via feedback (curated)". Per
`harness/skills/two-plane-memory/SKILL.md:48-53` it is "Plane 3 — PROCESS agreements", "a peer of the
committed-state tier… **not regenerated** and is not derived." Per `README.md:5-6` it is "not
constitution, so it is not path-denied. This is the D-Q1 committed-but-writable posture."

**It is hand-editable. It is NOT derived. `tools/memory_regen` must READ it and never WRITE it** —
`.memory/agreements/README.md:4-5`: "is never regenerated, is never written by `tools/memory_regen`".
Phase 13 adds a *reader* in `tools/memory_regen`; that is consistent (the module is the assembler, not
just a generator), but the plan must not let the composer create/normalize/rewrite agreement files.

### Active-set selection

- **Active** = frontmatter `status` is exactly `"active"`.
- **Not active** = `"retired"`, absent, malformed, unparseable, or a non-agreement file (`_*`, `README.md`).
- Fail-closed: never guess. Mirrors `frontmatter.py:54-55` ("treat as no frontmatter (fail safe, don't guess)").

**Today the active set is EMPTY** — `find .memory -type f` yields only `_TEMPLATE.md` + `README.md` under
`agreements/`. So the block is omitted and the payload is unchanged in shape. Every cap/ordering test
therefore **must** use synthetic `tmp_path` fixtures (§3e).

### Full-body rendering

"Full-body" (§2 property 4: "Directives must be *present*, not *pointed at*") means the **title + the
one-line rule** — the directive content. It does **not** mean the raw file bytes.

**Exclude from the payload:** `provenance:`, `added:`, `status:`, and the `Related:` line. Rationale:
(a) they are curation metadata, not directives; (b) `provenance` embeds *verbatim user feedback* of
unbounded length — including it makes M unpredictable and widens the injection surface (§9); (c) the
`Related:` links are lazy-load pointers, and preloading them fights P13.

Recommended per-entry render — one line, deterministic, budget-predictable:

```
- **{title}** — {rule}
```

Where `title` = the `# ` H1 text and `rule` = the first non-empty, non-`Related:` body line. If either
is missing → **skip the entry** (fail-closed) rather than emit a half-directive.

**Reuse `parse_frontmatter`:** `from tools.harness_lint import parse_frontmatter`
(`tools/harness_emit/generate.py:35` sets this precedent). Signature —
`tools/harness_lint/frontmatter.py:26`: `def parse_frontmatter(md_text: str) -> tuple[dict, str]`.
There is **no PyYAML dependency** in `pyproject.toml`; `frontmatter.py` ships its own `_load_yaml`.
**Do not `uv add pyyaml`** for this.

---

## §5. The `updated:` Stamp Round-Trip

### Where `/checkpoint` writes today

`harness/commands/checkpoint.md:17-19` — a prose-instructed command (no runnable script):

> 1. Update the committed state files with the current focus and progress:
>    - `.memory/state/activeContext.md` — what is in flight right now (current task, next step).
>    - `.memory/state/progress.md` — what is done / what remains.

It stages exactly two files (`checkpoint.md:27-29`). **There is no runnable `/checkpoint` binary** — it
is a Markdown command executed by the `orchestrator` agent (`checkpoint.md:6`). So "`/checkpoint` writes
the stamp" is an **instruction edit**, not a code change. This materially shrinks that task — and means
its verification is **structural** (the command text mandates the stamp; the state files carry one), not
a unit test of a writer function.

### Current state-file shape — **no frontmatter at all**

`.memory/state/activeContext.md:1-6` begins with an H1 + blockquote; `progress.md:1-5` likewise. Neither
has a `---` fence. So `parse_frontmatter` returns `({}, text)` for both **today** — the absent-stamp path
is the **current** path and must degrade gracefully on day one.

### Recommended stamp format

Add a YAML frontmatter block — consistent with `.memory/agreements/*` (which Phase 12 chose frontmatter
for) and parseable by the same shared `parse_frontmatter`:

```markdown
---
updated: 2026-07-15
---

# activeContext — session progress log (COMMITTED)
...
```

**Recommended over the alternatives:** an inline `> updated: …` blockquote line or a trailing footer
would need a bespoke regex (a second parser = a second determinism hazard), and would collide with the
existing blockquote banner at `activeContext.md:3-6`. Frontmatter reuses a tested parser and matches the
tier next door. ISO `YYYY-MM-DD` (date, not datetime) matches `_TEMPLATE.md:3` (`added: YYYY-MM-DD`).

> ⚠️ `parse_frontmatter` returns a parsed mapping; a bare `2026-07-15` may load as a **`datetime.date`**
> object, not a string. Rendering `str(date)` happens to give `2026-07-15`, but relying on that is
> fragile. **Recommendation:** quote it (`updated: "2026-07-15"`) so it round-trips as a string, and/or
> `str()`-coerce at the render site. The plan should verify `_load_yaml`'s actual scalar handling
> (`tools/harness_lint/frontmatter.py`) before pinning this — flagged as a **task-level verify step**.

### Surfacing verbatim, without wall-clock

`_active_context_pointer(state_dir)` currently **ignores** its parameter — `inject.py:94`:

```python
def _active_context_pointer(state_dir: Path = STATE_DIR) -> str:  # noqa: ARG001 (path is fixed)
```

The reframe **uses** `state_dir` (read `activeContext.md`, `parse_frontmatter`, pull `updated`) and the
`noqa: ARG001` comes off. The stamp is interpolated as an opaque string:

```python
stamp = fm.get("updated")
suffix = f" [updated: {stamp}]" if stamp else " [updated: unknown — run /checkpoint]"
```

No `datetime`, no comparison, no formatting. Q6 (`REQUIREMENTS.md:26`) is explicit:

> freshness is judged **agent-side** against the session date (no fixed threshold, no hook-wrapper
> wall-clock code, per Q6).

The agent already has today's date in session context, so surfacing the raw stamp is sufficient.

### Absent-stamp degradation (the day-one path)

| Condition | Behavior |
|---|---|
| Stamp present | `… [updated: 2026-07-15]` |
| Frontmatter absent (**today's files**) | `… [updated: unknown — run /checkpoint]` |
| `updated` key missing / empty | same as above |
| File missing / unreadable (`OSError`) | same as above — **never raise** |

The pointer must **never** throw: it is on the SessionStart path, and `memory-inject.sh:40` swallows a
non-zero exit into an empty payload (`|| echo ''`) — a crash silently blanks the *entire* injection.
Mirror the existing tolerant idiom at `inject.py:69-74` (`_read_head` catches `OSError` → `""`).

### §7a tight-progress shape

`progress.md:7-10` is already terse (4 bullets). `activeContext.md:8-22` already has `## In flight` +
`## Next`. §7a wants **in-flight + remaining + short last-N-done**, no growing done-log. The gap is
mostly **prose in `checkpoint.md`** mandating the shape (and forbidding accumulation), plus a
`## Recently done (last N)` heading. Note `test_inject_assembler.py:100` pins the literal marker
`"## In flight"` as a fixture guard — **do not rename that heading**, or update the test in lockstep.

---

## §6. Rewording — current text and proposed replacements

### The banner

**CURRENT** (`inject.py:41-44`, verbatim):

```python
BANNER = (
    "PROVISIONAL — volatile session state below is a hint, not truth. "
    "contracts/ and docs/adr/ (ADR) ALWAYS override .memory/ on conflict."
)
```

**Why it reads as "distrust your own work"** — three independent defects:

1. **`PROVISIONAL` is a bare, unscoped lead word.** It is the *first token of the session*, with no
   noun attached. It qualifies the reader's whole situation, not a file class.
2. **"a hint, not truth"** is an *epistemic* claim, not an authority claim. "Truth" is unqualified —
   the sentence never says *truth about what*. The correct claim is narrow ("`contracts/` is the
   authority **on data shape**"); the wording generalizes it to all knowledge.
3. **The scope clause arrives too late and too weakly.** "on conflict" is the final two words of the
   second sentence; by then "hint, not truth" has already landed. The genuinely scoped clause is
   *behind* the unscoped one.

Net: the only correctly-scoped words ("override … on conflict") are subordinate to two unscoped
epistemic assertions. An agent generalizes to "my working context is unreliable" → hedges, re-verifies,
self-cancels (§1c). Compounded because `.claude/hooks/memory-inject.sh:24-25` calls this out as *the*
reason injection is currently disabled:

> the "provisional / confirm-before-trusting" framing that MEM2 will reframe

**PROPOSED** (316 chars — measured; from §3 of the proposal, lightly tightened):

```python
BANNER = (
    "DATA PROVENANCE — the derived/state summaries below are auto-generated context, not the "
    "source of truth. On a DATA conflict, contracts/ and docs/adr/ (ADR) always win over "
    ".memory/. This is about which artifact wins a contradiction — NOT a reason to distrust, "
    "retract, or re-verify your own grounded working context."
)
```

Why it is strictly data-scoped: the lead is a **noun phrase naming the domain** ("DATA PROVENANCE");
the subject is *the summaries*, not the reader; "DATA conflict" scopes before the authority claim
lands; and the final clause forecloses the over-generalization explicitly.

### The pointer

**CURRENT** (`inject.py:48` + `:96-99`, verbatim):

```python
ACTIVE_HEADER = "## Active context (pointer)"
...
    return (
        f"{ACTIVE_HEADER}\n"
        ".memory/state/activeContext.md — volatile; confirm against contracts/ADR before trusting."
    )
```

`"confirm against contracts/ADR before trusting"` is a **direct behavioral imperative** — worse than the
banner. It is an instruction ("confirm"), addressed to the agent, with a precondition on *trusting*.
"volatile" adds an unscoped reliability slur. Nothing in it is data-scoped.

**PROPOSED** (200 chars incl. stamp — measured):

```python
ACTIVE_HEADER = "## Progress log (pointer)"
...
".memory/state/activeContext.md — session progress log (what was in flight; git holds the "
"full completed history). On a data conflict, contracts/ADR win. [updated: 2026-07-15]"
```

Changes: `Active context` → `Progress log` (SC1's "reworded to a progress-log pointer"); the imperative
is deleted; authority is restated data-scoped; "git holds the full completed history" encodes §7a; the
verbatim stamp lands (§5).

### Already done by Phase 12 — do NOT redo

Per `12-02-SUMMARY.md`, the state banners in `activeContext.md:3-6` / `progress.md:3-4`, `AGENTS.md`,
`.memory/README.md:51-55`, and `two-plane-memory/SKILL.md:30-33` **already carry** the reworded
"DATA AUTHORITY … not a reason to re-verify grounded work" text. That is MEM2-03 = **Phase 12, shipped**.
Phase 13 touches only `inject.py` + `orient.md` + `session-inject.ts:13`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---|---|---|---|
| YAML frontmatter parsing | A regex over `---` fences | `from tools.harness_lint import parse_frontmatter` (`frontmatter.py:26`) | CRLF-normalized (`:40`), fail-safe on unclosed fence (`:54`), already the emitter's parser (`generate.py:35`) |
| YAML scalar loading | `uv add pyyaml` | `frontmatter.py::_load_yaml` | No PyYAML dep exists; adding one for 3 keys is unjustified |
| Deterministic dir iteration | `os.listdir` + manual sort | `sorted(dir.glob("*.md"))` | 4 precedents (§3a) |
| Byte-identity proof | `git diff` | sha256 over `tmp_path` + syrupy | `docs_sync/tests/test_docs_sync_determinism.py:43`; derived paths are gitignored (`.gitignore:23`) so git diff proves nothing |
| Budget truncation | Mid-line slicing | Existing whole-section priority-truncate (`inject.py:127-134`) | D-07 invariant |
| Freshness comparison | `datetime.now()` in `assemble()` / a date-diff in `memory-inject.sh` | Surface the stamp; let the agent judge | Q6 **and** determinism (`inject.py:20-22`) |

**Key insight:** every mechanic Phase 13 needs already exists in this repo with a cited precedent. Net-new
code should be ~1 composer function + ~1 render function. Anything larger is a smell.

---

## Common Pitfalls

### Pitfall 1: Assuming the determinism test exists
**What goes wrong:** Planner writes "determinism test stays green" — but there is none, so the reframe
ships unprotected and a `glob()` ordering bug reaches main.
**How to avoid:** Wave 0 backfill (§3). **Warning sign:** no new file under `tools/memory_regen/tests/`.

### Pitfall 2: `_TEMPLATE.md` injected as a live directive
**What goes wrong:** `_TEMPLATE.md:2` is `status: active` → the template becomes a priority-0 directive
reading `<One-line working-style or methodology rule.>`.
**How to avoid:** three-layer exclusion (§3c). **Warning sign:** a test fixture that copies the real
agreements dir; a payload containing `<`.

### Pitfall 3: Testing the cap against the live (empty) agreements dir
**What goes wrong:** Active set is empty **today**, so a cap test against the real dir passes vacuously
and rots the day someone adds an agreement.
**How to avoid:** `agreements_dir` param + `tmp_path` fixtures (§3e).

### Pitfall 4: Reworded text silently blowing the budget
**What goes wrong:** New banner is +183 chars and the stamp +83 — headroom drops 1050 → 784 before any
agreement. A generous cap then evicts the repo-map every session, invisibly (it is *supposed* to drop —
no test fails).
**How to avoid:** the §2 arithmetic; a test asserting repo-map **survives** at a full-cap agreements block.

### Pitfall 5: "Fixing" the red emit snapshot
**What goes wrong:** Planner sees `test_projected_tree_matches_committed_snapshot` RED, assumes Phase 13
broke it, and re-emits — stealing Phase 15's scope and mixing generated-tree churn into a logic diff.
**How to avoid:** §Scope Fence — it is **already red on a clean tree**, from Phase 12.

### Pitfall 6: An exception in the pointer blanking the whole injection
**What goes wrong:** `memory-inject.sh:40` is `uv run … || echo ''` — any traceback ⇒ **empty payload**,
silently. A missing state file would delete the entire session's orientation.
**How to avoid:** catch `OSError` and degrade (§5); test the file-missing path.

### Pitfall 7: Leaving injection disabled
**What goes wrong:** `.memory/.inject-disabled` short-circuits the hook to an empty payload
(`memory-inject.sh:28-31`). Phase 13 ships a perfect reframe that never runs.
**How to avoid:** §Scope Fence — decide explicitly.

---

## Runtime State Inventory

Phase 13 changes injected-payload text and adds a state-file stamp — a refactor with runtime coupling.

| Category | Items Found | Action Required |
|---|---|---|
| Stored data | **`.memory/state/activeContext.md` + `progress.md`** — committed, no frontmatter today (`activeContext.md:1`, `progress.md:1`) → absent-stamp path is live. **`.memory/agreements/`** — only `_TEMPLATE.md` + `README.md`; **zero active agreements** | Add stamp to both files (data migration, hand-edit — committed human/agent tier, not derived); code edit in `assemble()` to read it |
| Live service config | **None** — verified: injection is consumed only by `.claude/hooks/memory-inject.sh` (wired as SessionStart group 4, `test_hook_wiring.py:34-40`) and the deferred `harness/plugins/session-inject.ts`. No external service holds this payload | none |
| OS-registered state | **None** — verified: `.claude/settings.json` SessionStart wiring is committed config; no scheduler/daemon registration | none |
| Secrets/env vars | **`GOLDEN_APPROVE_HUMAN`** (`gate-model/SKILL.md:44-51`) — unrelated to this phase (`.memory/agreements/` is **not** path-denied, Q1). **`CLAUDE_PROJECT_DIR`** (`memory-inject.sh:15`) — unchanged | none |
| Build artifacts | **`.memory/derived/repo-map.md`** — gitignored (`.gitignore:23`), regenerated (`memory-inject.sh:36`); **absent on a fresh checkout** (measured 0 chars → payload 833 vs 2950). **`.memory/derived/contracts-index.md`** — tracked (`.gitignore:24`) | Regenerate before measuring budget; do not commit repo-map |
| **Runtime feature flag** | **`.memory/.inject-disabled`** — present; short-circuits the hook to an empty payload (`memory-inject.sh:28-31`) | **Decision required** — see Scope Fence |

**The canonical question — after every file is updated, what still has the old string?** The generated
runtime trees (`.claude/commands/orient.md:21`, `.opencode/command/orient.md`) and the emit snapshot
(`.ambr:1480,1525`) still carry "provisional banner" prose. **Phase 15 owns re-emitting them.**

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|---|---|---|---|---|
| uv | all commands | ✓ | (workspace configured) | — |
| pytest | all tests | ✓ | 8.4.x pinned (`python-conventions/SKILL.md:29`) | — |
| syrupy | snapshot determinism | ✓ | 5.2.0 — used by `test_emit_determinism.ambr` | sha256-only test |
| `tools.harness_lint.parse_frontmatter` | frontmatter parsing | ✓ | in-repo (`frontmatter.py:26`) | — |
| `tools.contract_drift.run_gate` | drift section | ✓ | in-repo (`inject.py:30`) | already degrades (`inject.py:58`) |
| networkx / tree-sitter | repo-map regen | ✓ | repo-map generated OK during research | section omits if absent (`inject.py:91`) |
| PyYAML | — | ✗ | — | **not needed** — `frontmatter.py` ships `_load_yaml` |
| node | hook envelope | ✓ | `memory-inject.sh:18-20` | — |
| opencode runtime | `session-inject.ts` | ✗ | — | **Authored-only, execution deferred** (`session-inject.ts:4-8`) — do not attempt to run |

**Missing dependencies with no fallback:** none.

---

## Validation Architecture

### Test Framework

| Property | Value |
|---|---|
| Framework | pytest 8.4.x (uv workspace) + syrupy 5.2.0 |
| Config file | root `pyproject.toml` (uv workspace); `tools/memory_regen/tests/conftest.py` (sys.path wiring, `repo_root` fixture) |
| Quick run command | `uv run pytest tools/memory_regen -q` |
| Full suite command | `uv run pytest tools/memory_regen tools/harness_lint -q` |
| Estimated runtime | ~5s scoped / ~20s full |

> **Suite baseline:** `uv run pytest tools/harness_emit` is **1 failed, 46 passed** on a clean tree
> *before any Phase 13 work* (`test_projected_tree_matches_committed_snapshot`, Phase-12 inheritance).
> Phase 13's gate is `tools/memory_regen` + `tools/harness_lint` green, with harness_emit **no worse
> than 1 failed**.

### Phase Requirements → Test Map

| Req | SC | Behavior | Test Type | Automated Command | File Exists? |
|---|---|---|---|---|---|
| MEM2-02 | SC2 | **delete+regen byte-identical** — `assemble()` twice ⇒ identical sha256, incl. a populated agreements dir | unit | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py::test_assemble_is_byte_identical -x` | ❌ **Wave 0** |
| MEM2-02 | SC2 | **Committed syrupy snapshot** pins the payload over a fixed fixture tree | snapshot | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py::test_payload_matches_snapshot -x` | ❌ Wave 0 |
| MEM2-02 | SC2 | **Sorted iteration** — shuffled creation order ⇒ identical payload; entries appear slug-ascending | unit | `…::test_agreements_order_is_sorted_not_filesystem -x` | ❌ Wave 0 |
| MEM2-02 | SC2 | **Budget with agreements present** — full-cap block ⇒ `len(payload) <= 4000` | unit | `…::test_budget_holds_with_full_agreements_block -x` | ❌ Wave 0 |
| MEM2-02 | SC1/SC2 | **Repo-map survives** a full-cap (M=700) agreements block (the §2 knee) | unit | `…::test_repo_map_survives_full_cap_agreements -x` | ❌ Wave 0 |
| MEM2-02 | SC1 | **Overflow → pointer** — N+1 entries ⇒ pointer, no entry bodies; and >M chars ⇒ pointer | unit | `…::test_overflow_degrades_to_pointer -x` | ❌ Wave 0 |
| MEM2-02 | SC1 | **Never-dropped** — at `budget_chars=1`, agreements + banner + drift all present | unit | `…::test_agreements_banner_drift_never_dropped -x` | ❌ Wave 0 |
| MEM2-02 | SC1 | **Active-set filter** — `status: retired` excluded; `_TEMPLATE.md` + `README.md` excluded; missing status excluded | unit | `…::test_only_active_non_template_agreements_compose -x` | ❌ Wave 0 |
| MEM2-02 | SC1 | **Data-scoped banner** — `BANNER` has no `provisional`/`hint, not truth`/`confirm before trusting`; contains `DATA` + `contract` + `adr` | unit | `…::test_banner_is_data_scoped` (**rewrite** of `test_inject_assembler.py:19-34`) | ⚠️ **rewrite** |
| MEM2-02 | SC1 | **Two distinct blocks** — agreements header ≠ banner; both present when agreements exist | unit | `…::test_two_distinct_blocks_emitted -x` | ❌ Wave 0 |
| MEM2-02 | SC1 | **Pointer reworded** — payload has no `confirm against contracts/ADR before trusting`; `ACTIVE_HEADER` says progress log | unit | `…::test_pointer_is_progress_log_not_imperative -x` | ❌ Wave 0 |
| MEM2-05 | SC3 | **Verbatim stamp** — fixture state file `updated: 2026-01-02` ⇒ `[updated: 2026-01-02]` in payload | unit | `…::test_updated_stamp_surfaced_verbatim -x` | ❌ Wave 0 |
| MEM2-05 | SC3 | **Absent-stamp degradation** — no frontmatter / missing key / missing file ⇒ graceful text, **no raise** | unit | `…::test_absent_stamp_degrades_gracefully -x` | ❌ Wave 0 |
| MEM2-05 | SC3 | **No wall-clock (static)** — `inject.py` source has no `datetime`/`date.today`/`time.`/`now()` | static | `…::test_inject_module_has_no_wallclock -x` | ❌ Wave 0 |
| MEM2-05 | SC3 | **No hook wall-clock (static)** — `memory-inject.sh` has no `date`/`$(date)`; `session-inject.ts` no `Date.now`/`new Date` | static | `…::test_hook_wrappers_have_no_wallclock -x` | ❌ Wave 0 |
| MEM2-05 | SC3 | **`/checkpoint` mandates the stamp** | structural | `grep -q "updated:" harness/commands/checkpoint.md` | ⚠️ after edit |
| MEM2-05 | SC3 | **State files carry a stamp** | structural | `grep -q "^updated:" .memory/state/activeContext.md .memory/state/progress.md` | ⚠️ after edit |
| MEM2-05 | SC4 | **Tight progress** — `checkpoint.md` mandates in-flight + remaining + last-N-done and forbids accumulation | structural | `grep -qi "last .*done\|no.*done-log\|git holds" harness/commands/checkpoint.md` | ⚠️ after edit |
| MEM2-02 | SC1 | **Pointer-only preserved** — no `$schema`; activeContext body (`## In flight`) absent | unit | existing `test_inject_assembler.py:88-103` — must stay green | ✅ |

### Sampling Rate

- **Per task commit:** `uv run pytest tools/memory_regen -q` (~5s)
- **Per wave merge:** `uv run pytest tools/memory_regen tools/harness_lint -q` (~20s)
- **Phase gate:** both green + `harness_emit` no worse than its 1 inherited failure, before `/gsd:verify-work`

Max feedback latency: **< 20s**. No watch-mode flags.

### Wave 0 Gaps

- [ ] `tools/memory_regen/tests/test_inject_determinism.py` — **NEW**; the byte-identity + snapshot +
      no-wall-clock net. Covers SC2/SC3. **Must land before the reframe** — model:
      `tools/docs_sync/tests/test_docs_sync_determinism.py:43`.
- [ ] `tools/memory_regen/tests/conftest.py` — **NEW fixture** `tmp_agreements_tree` producing synthetic
      agreements (≥1 active, ≥1 retired, a `_TEMPLATE.md` decoy, a no-frontmatter file), created in
      **non-alphabetical** order so the sorted-iteration test is meaningful.
- [ ] `assemble(agreements_dir=…)` parameter — a **testability prerequisite** (peer of `derived_dir` /
      `state_dir`, `inject.py:105-109`); without it, cap/ordering/overflow tests cannot be hermetic.
- [ ] `tools/memory_regen/tests/__snapshots__/` — syrupy snapshot dir (does not exist for this package).
- [ ] Rewrite `test_inject_assembler.py:19-34,71,116-122` in lockstep with the reframe (**expected red**
      — a *planned* update, not a regression).
- No framework install needed (pytest + syrupy already in the workspace).

### Manual-Only Verifications

| Behavior | Req | Why Manual | Instructions |
|---|---|---|---|
| opencode `session-inject.ts` parity | MEM2-02 | No opencode runtime in this container — authored-only, execution deferred (`session-inject.ts:4-8`) | Static assert only: the stub still references `tools.memory_regen.inject` (`test_hook_wiring.py:66-69`) |
| Injected payload *reads* as a directive, not distrust | MEM2-02 (SC1) | Wording quality is a human judgement; tests can only assert absence of banned phrases | Operator reads `uv run python -m tools.memory_regen.inject` output |

---

## Security Domain

`workflow.security_enforcement` is enabled — each PLAN.md needs a `<threat_model>` block.

### Applicable ASVS Categories

| ASVS | Applies | Standard Control |
|---|---|---|
| V2 Authentication | no | No auth surface — local file assembly |
| V3 Session Management | no | No sessions (LLM "session" ≠ ASVS session) |
| V4 Access Control | **yes** | Who may write `.memory/agreements/` → priority-0 directive. Q1 = committed-but-writable, **not** path-denied (`agreements/README.md:5-6`); gates = git review + Phase-14 provenance lint |
| V5 Input Validation | **yes** | `.memory/agreements/*` is **untrusted input** to a directive block. Fail-closed status filter, `_`/README exclusion, N/M cap, title+rule-only render |
| V6 Cryptography | no | sha256 for test determinism only — not a security control |
| V12 Files | **yes** | Confine reads to `agreements_dir`; `glob("*.md")` (non-recursive), no symlink following, no traversal |
| V14 Configuration | **yes** | `.memory/.inject-disabled` is a security-relevant kill switch (`memory-inject.sh:28-31`) |

### Known Threat Patterns

| # | Pattern | STRIDE | Mitigation | In Phase 13? |
|---|---|---|---|---|
| **T-13-01** | **Prompt injection via a planted agreement.** `.memory/agreements/` is committed-but-writable and **not path-denied** (Q1). Any repo-write actor — a malicious PR, a compromised agent, a careless `/agree` (Phase 14) — plants `<slug>.md` with `status: active` whose "rule" reads *"ignore contract-guard"* / *"exfiltrate env vars"*. `inject.py` then renders it at **priority-0 as a directive the agent is told to honor**, every session, non-ignorably. **This is the phase's one genuine security surface** — Phase 13 converts a passive data dir into an executable instruction channel. | **E**levation of Privilege / Tampering | **(a)** Render **title + one-line rule only** — never `provenance` (verbatim user text, unbounded) or raw body (§4); **(b)** fail-closed `status == "active"`; **(c)** N/M cap bounds blast radius; **(d)** **scope-limiting header** — the block header must state these are *working-style* directives that **never override `contracts/`, `docs/adr/`, or the gates**, so a planted agreement cannot self-authorize constitution writes; **(e)** git review is the gate (Q1's accepted trade-off, `REQUIREMENTS.md:50`) | **(a)–(d) YES.** Provenance **lint** = Phase 14 (MEM2-04) |
| **T-13-02** | **Context DoS / drift eviction.** An oversized agreements set at never-dropped priority-0 crowds out the drift summary — the live *safety* signal (`inject.py:54-66`) — so an agent stops seeing contract drift. | **D**enial of Service | N/M cap (§2) + drift stays never-dropped; test: at `budget_chars=1`, drift present | **YES** |
| **T-13-03** | **Secret leakage into the payload.** Agreements are committed **and now injected verbatim**; a secret pasted into a rule enters every session's context. `.memory/state/` already warns (`activeContext.md:5`); `agreements/` has no such warning. | **I**nformation Disclosure | `secret_scan` hook gates writes (`gate-model/SKILL.md` hook table); excluding `provenance` from the render shrinks the surface. **Recommend:** add the no-secrets line to `agreements/README.md` | Partial — README line is a **cheap add** |
| **T-13-04** | **Path traversal / symlink escape.** A crafted slug or a symlink in `agreements/` reads outside the dir. | **I**nformation Disclosure | Non-recursive `glob("*.md")` (not `rglob`), confine to `agreements_dir`, no symlink follow. Precedent: `tools/docs_sync` `_confine` (`generate.py`), `golden_runner._confine` | **YES** |
| **T-13-05** | **Silent injection failure.** An unhandled exception ⇒ `memory-inject.sh:40` `|| echo ''` ⇒ empty payload; drift + agreements vanish **silently**. Availability of the safety signal. | **D**enial of Service | Every new read catches `OSError` and degrades (§5); test the missing-file path | **YES** |
| **T-13-06** | **Determinism break as a tamper channel.** Non-sorted iteration makes the payload environment-dependent — an attacker-influenced ordering could shift which entries land, and diffs become unreviewable. | **T**ampering | `sorted()` (§3a) + byte-identity test | **YES** |

**Not a threat (do not theatricalize):** sha256 in tests is a determinism check, not integrity; there is
no network, no untrusted deserialization (`_load_yaml` is in-repo, no `yaml.load`), no auth, no PII.

---

## Scope Fence — explicitly OUT of Phase 13

| Out of scope | Owner | Why a planner might wrongly pull it in |
|---|---|---|
| **`/agree` command** (append/retire agreements) | **Phase 14** (MEM2-04) | Phase 13 *reads* agreements — the write path is Phase 14. `agreements/README.md:18-19`: "The `/agree` write path and provenance lint arrive in Phase 14; they are intentionally out of scope for this scaffold." |
| **Provenance / anti-invent lint** in `tools/harness_lint` | **Phase 14** (MEM2-04) | T-13-01's *durable* mitigation is the lint. Tempting to add here — resist; Phase 13's mitigations are render-shape + cap + fail-closed filter |
| **Adding real agreement content** | Phase 14 / operator | The active set is empty today; agreements are **user-authored via feedback** (§2 property 2 — "An agent **must not invent** entries"). Phase 13 must **not** author agreements to "test" the block — use `tmp_path` fixtures |
| **Re-emitting `.opencode/` + `.claude/`** | **Phase 15** (MEM2-06) | Editing `harness/commands/orient.md` makes generated copies stale. Phase 12 set the precedent (`12-01-SUMMARY.md` "Deferred": re-emit "deferred to Phase 15; those generated copies were intentionally not edited here") |
| **Fixing the red emit snapshot** | **Phase 15** | ⚠️ `uv run pytest tools/harness_emit` is **already 1-failed on a clean tree** — `test_projected_tree_matches_committed_snapshot`, from Phase 12's `two-plane-memory/SKILL.md` edit (diff confirms `Plane 3 — PROCESS agreements` + data-authority text). **Not a Phase 13 regression. Do not regenerate the `.ambr`** — that would silently bless Phase 12's un-emitted tree and steal Phase 15's gate |
| **`EXPECTED_COMMANDS` count changes** | Phase 15 | No new command in Phase 13 — `/checkpoint` is *edited*, not added |
| **Local memory web UI / pointer index** | **Phase 16** (MEM2-07) | §7d's "pointers that reference memory files" is adjacent to the pointer reword — different phase |
| **MEM2-03 prose reword** (`.memory/README.md`, state banners, SKILL.md, `AGENTS.md`) | **Phase 12 — DONE** | `12-02-SUMMARY.md` confirms shipped. Re-doing it churns Phase 12's work |
| **ADR-0006 authoring** | **Phase 12 — DONE** | Landed at `docs/adr/0006-process-memory-channel-and-provenance-reframe.md`, commit `bea92ef` |
| **Per-instance agreement overlays** | **v2 (MEM2-F1)** | `REQUIREMENTS.md:42` — deferred |
| **Wall-clock staleness threshold** | **Never** (Q6) | `REQUIREMENTS.md:53` lists "Hook-wrapper / `assemble()` wall-clock staleness comparison" as **Out of Scope**. §3 of the proposal *suggested* the hook wrapper — **§7/Q6 overrides**: agent-side, no threshold, **no hook-wrapper wall-clock code** |
| **Promoting agreements to the constitution plane** | **Never** (Q1) | `REQUIREMENTS.md:50` — out of scope |

### ⚠️ Decision required: `.memory/.inject-disabled`

`.memory/.inject-disabled` is **present**, short-circuiting the hook to an empty payload
(`memory-inject.sh:28-31`). Both the flag file and `activeContext.md:12-13` name **Phase 13** as the
re-enable trigger:

> - SessionStart memory injection is temporarily **DISABLED** (`.memory/.inject-disabled`) — MEM2
>   Phase 13 reframes it; re-enable with `rm .memory/.inject-disabled`.

And `memory-inject.sh:22-27` gives the reason — the very framing SC1 fixes.

**No Success Criterion mentions re-enabling.** But the phase's whole value is unrealized while the flag
stands, and two committed surfaces promise Phase 13 does it.

**Recommendation — `NEEDS OPERATOR RATIFICATION`:** delete `.memory/.inject-disabled` in Phase 13's final
plan, **after** the reframe is green, and strip the now-obsolete `TEMPORARY DISABLE` block
(`memory-inject.sh:22-31`) + the `activeContext.md:12-13` note. **Counter-argument:** the payload's other
half (`/agree`, provenance lint) lands in Phase 14, so an operator may prefer to re-enable at Phase 15.
**If deferred, the plan must still update `activeContext.md:12-13`** so the state plane stops asserting
something false. Do **not** leave this implicit — surface it at planning.

---

## Suggested Plan Decomposition

`inject.py` is **one 148-line file** — plans that both edit it will conflict. Decompose by *file
ownership*, not by requirement.

### Wave 1 — parallel (disjoint file sets)

**Plan 13-01 — State stamp + tight progress + `/checkpoint` write path** *(MEM2-05, write half)*
- Files: `harness/commands/checkpoint.md`, `.memory/state/activeContext.md`, `.memory/state/progress.md`
- Add `updated:` frontmatter to both state files; mandate the stamp + §7a tight shape in `checkpoint.md`;
  forbid done-log accumulation ("git holds the full completed history").
- **Verify `_load_yaml` scalar handling first** (§5 caveat) — quoted vs bare date.
- Preserve the `## In flight` heading (`test_inject_assembler.py:100` pins it).
- Verify: structural greps. **No `inject.py` edit.**

**Plan 13-02 — Determinism safety net (Wave 0 backfill)** *(MEM2-02 SC2 prerequisite)*
- Files: `tools/memory_regen/tests/test_inject_determinism.py` (**new**), `conftest.py` (+fixture),
  `__snapshots__/` (new).
- Byte-identity + snapshot + no-wall-clock statics + `tmp_agreements_tree` fixture.
- Lands **green against today's `inject.py`** (verified: `assemble()` already hashes stably) — a true
  regression net, not a rubber stamp.
- **Must merge before 13-03.** **No `inject.py` edit** (except the `agreements_dir` param — see note).

> **Sequencing note:** the `agreements_dir` parameter is a testability prerequisite owned by **13-03**.
> Either (a) 13-02 lands determinism/no-wall-clock tests only, deferring agreements fixtures to 13-03's
> own wave, or (b) 13-03 opens with a trivial "add the param" task. **Recommend (a)** — it keeps Wave 1
> strictly `inject.py`-free and the wave boundary clean.

### Wave 2 — sequential (depends on 13-01 **and** 13-02)

**Plan 13-03 — Injector reframe** *(MEM2-02 + MEM2-05 read half)* — **single-file, must be one plan**
- Files: `tools/memory_regen/inject.py`, `tools/memory_regen/tests/test_inject_assembler.py`,
  `harness/commands/orient.md`, `harness/plugins/session-inject.ts` (comment only)
- Sub-waves:
  1. `agreements_dir` param + composer (`sorted` glob, exclusions, fail-closed status filter, render) +
     cap/overflow constants
  2. Priority renumber (§1 sites 1,5,6,7) + `BANNER` reword + `ACTIVE_HEADER`/pointer reword + verbatim
     stamp
  3. Rewrite `test_inject_assembler.py` (sites 8–12) + add cap/overflow/order/stamp tests + `orient.md`
     & `session-inject.ts:13` prose
- Depends on **13-01** (the stamp must exist to be read) and **13-02** (the net must exist to protect it).

**Plan 13-04 — Re-enable injection** *(scope-fence decision)* — **only if ratified**
- Files: delete `.memory/.inject-disabled`; strip `memory-inject.sh:22-31`; update `activeContext.md:12-13`
- Strictly after 13-03 green. Gate on operator ratification.

### Dependency graph

```
Wave 1:  [13-01 state stamp]  ‖  [13-02 determinism net]
                    \                /
Wave 2:              [13-03 injector reframe]
                              |
Wave 3:              [13-04 re-enable]  (conditional)
```

**Why the stamp-write must precede the stamp-surfacing:** 13-03's verbatim-stamp test needs a real
frontmatter shape to target. If 13-03 landed first, `_active_context_pointer` would read a key nothing
writes, and the only live path would be the absent-stamp fallback — SC3 unproven end-to-end.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|---|---|---|
| A1 | **N=6 / M=700** are the right cap values | §2 | Too small ⇒ overflow-to-pointer becomes the normal path (defeats "full-body"); too large ⇒ repo-map evicted every session. **Arithmetic is measured; the values are a judgement.** `NEEDS OPERATOR RATIFICATION` |
| A2 | Agreements emitted **first** (before the banner), retiring "banner-first" | §1 | If the operator wants the banner literally first, swap order — priority semantics unchanged. Low risk (block is omitted when the set is empty — the state today) |
| A3 | Zero active agreements ⇒ block **omitted** (no "none recorded yet" filler) | §1, §4 | §2 of the proposal suggested filler text. Low risk; omission is cleaner + keeps today's payload shape |
| A4 | Render = **title + rule only**; `provenance`/`Related:` excluded | §4 | If the operator wants provenance injected, M must grow substantially and T-13-01's surface widens. **Recommend excluding** |
| A5 | `updated:` goes in **YAML frontmatter** (quoted ISO date) | §5 | State files have no frontmatter today. If rejected, a bespoke parser is needed (extra determinism hazard) |
| A6 | `parse_frontmatter`'s `_load_yaml` returns a bare date as `datetime.date` | §5 | **Unverified** — did not read `_load_yaml`'s body. Quoting the value sidesteps it. **Task-level verify step in 13-01** |
| A7 | Phase 13 should delete `.memory/.inject-disabled` | Scope Fence | No SC mandates it; two committed surfaces promise it. `NEEDS OPERATOR RATIFICATION` |
| A8 | The red `harness_emit` snapshot is Phase 12's, not Phase 13's | Scope Fence | **Verified** — red on a clean tree; diff shows only Phase-12 `SKILL.md` text. Low risk |
| A9 | `/checkpoint` is prose-only (no runnable) | §5 | **Verified** — `checkpoint.md:6` `agent: orchestrator`; steps are prose + `!` shell lines. Makes the stamp-write an instruction edit |

## Open Questions

1. **Cap values (Q4 — locked as "capped", values open).**
   - Known: headroom after reword = **784 chars** (measured); a realistic entry ≈ 96 chars; M≥800 evicts the repo-map.
   - Unclear: how many agreements the operator expects to accumulate; whether repo-map eviction is acceptable.
   - Recommendation: **N=6 / M=700**; named module constants so re-ratification is a one-line edit.

2. **Re-enable injection in Phase 13?** (A7) — Recommendation: yes, as a final gated plan. If deferred, **still** correct `activeContext.md:12-13`.

3. **Emission order: agreements-first or banner-first?** (A2) — Recommendation: agreements-first per SC1's "priority-0"; note it retires the D-02 "banner-first" phrasing in `orient.md:45` + docstrings.

4. **Does the block header carry a scope limiter?** — Recommendation: **yes** (T-13-01(d)) — the header should state agreements never override `contracts/`/`docs/adr/`/the gates. Costs ~60 chars of M; buys a real mitigation against a planted directive claiming constitution authority.

## Sources

### Primary (HIGH — read this session, `file:line` cited)
- `tools/memory_regen/inject.py` (148 lines, full) — priority list, `BANNER`, `ACTIVE_HEADER`, `assemble()`, budget/truncate
- `tools/memory_regen/tests/test_inject_assembler.py` (123 lines, full) — **no determinism test**
- `tools/memory_regen/tests/conftest.py`, `test_hook_wiring.py` — fixtures, hook wiring
- `tools/docs_sync/tests/test_docs_sync_determinism.py:37-70` — the byte-identity model
- `tools/harness_lint/frontmatter.py:26-55` — `parse_frontmatter`; `tools/harness_emit/generate.py:35,144-152,191`
- `.memory/agreements/{_TEMPLATE.md,README.md}`, `.memory/state/{activeContext.md,progress.md}`, `.memory/README.md`, `.memory/.inject-disabled`
- `.claude/hooks/memory-inject.sh` (45 lines, full), `harness/plugins/session-inject.ts:1-60`, `harness/commands/{checkpoint.md,orient.md}`
- `harness/skills/{two-plane-memory,gate-model,python-conventions}/SKILL.md`
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §1–§7; `.planning/REQUIREMENTS.md`; `.planning/ROADMAP.md` (Phase 13); `.planning/phases/12-*/12-0{1,2,3}-SUMMARY.md`, `12-VALIDATION.md`
- **Measured live:** section sizes / payload totals / sha256 stability (`uv run python -c …`); `uv run pytest tools/harness_emit` = 1 failed / 46 passed (pre-existing); repo-map regen

### Secondary (MEDIUM)
- `tools/harness_emit/tests/__snapshots__/test_emit_determinism.ambr:1470-1535` — orient.md embedding (read in situ)
- `git log --oneline -1 -- tools/harness_emit/tests/__snapshots__/` → `07c91c8` (last snapshot update = Phase 11)

### Tertiary (LOW)
- None. No WebSearch used — this phase is entirely repo-internal. No external library research required
  (§Don't Hand-Roll: every mechanic has an in-repo precedent).

## Package Legitimacy Audit

**Not applicable — Phase 13 installs no external packages.** Every dependency is already in the uv
workspace (`pytest`, `syrupy`) or in-repo (`tools.harness_lint.parse_frontmatter`,
`tools.contract_drift.run_gate`). PyYAML is explicitly **not** to be added (§Don't Hand-Roll). If a plan
proposes `uv add`, that is a scope violation — flag it.

## Metadata

**Confidence breakdown:**
- Current behavior / `file:line` claims: **HIGH** — every claim read from the working tree this session
- Budget arithmetic: **HIGH** — measured via live execution, not estimated
- Cap values (N/M): **MEDIUM** — arithmetic is HIGH, the judgement needs ratification (A1)
- Determinism hazards: **HIGH** — glob-order + wall-clock are well-established; `_TEMPLATE.md` trap verified live
- Threat model: **MEDIUM-HIGH** — T-13-01 follows directly from Q1 + priority-0 directive semantics
- Frontmatter scalar handling: **LOW** (A6) — `_load_yaml` body not read; task-level verify required

**Research date:** 2026-07-15
**Valid until:** ~30 days (repo-internal, stable) — **but re-measure the budget arithmetic if
`contracts/` grows or `_HEAD_LINES` changes**, since the §2 knee depends on the contracts-index size.
