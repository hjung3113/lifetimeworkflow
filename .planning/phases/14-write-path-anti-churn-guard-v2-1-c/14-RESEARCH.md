# Phase 14: Write Path + Anti-Churn Guard (v2.1 C) - Research

**Researched:** 2026-07-16
**Domain:** Python tooling inside an existing uv workspace — a runnable frontmatter lint, a refusing
CLI writer, and a shared file-selection predicate. No new external dependencies.
**Confidence:** HIGH (every claim below is `[VERIFIED]` by reading the file or running the code in
this session; the two design recommendations are flagged as such)

> **Authoring note (meta, but load-bearing for this phase):** the first attempt to write this file
> was **denied by the repo's own `secret_scan` gate** (`tools/hooks/secret_scan.py:47`), because it
> quoted `approve.py:57` verbatim and that line has the shape `token` + `=` + 16-plus non-space
> characters. The gate was right on shape and wrong on intent — **exactly the D-03 trust model this
> phase is built on** (shape, not truth). The quote was reworded rather than bypassed. Plans should
> expect the same gate when quoting `approve.py` / `contract_guard.py` source into docs.

## Summary

This phase adds **no new technology**. Every shape it needs already exists in the repo and was read
line-by-line this session: the runnable-lint shape (`tools/polyglot_lint/lint.py`), the refusal shape
(`tools/golden_runner/approve.py`), the shared frontmatter parser (`tools/harness_lint/frontmatter.py`),
the fail-closed agreements predicate (`tools/memory_regen/inject.py:96-106`), and the confinement
idiom (`tools/docs_sync/generate.py:189-195`). The research question is therefore not "what library"
but "**what exactly can be extracted without breaking the four live Phase-13 invariants**" — and the
answer is: a clean extraction is available, in a direction the codebase **already imports**.

The single highest-value finding: **`inject.py:15` already contains `from tools.harness_lint import
parse_frontmatter`.** The `memory_regen → harness_lint` edge exists and is safe. So the shared
predicate (D-05) must live in **`tools/harness_lint/`**, consumed by `inject.py` — not the reverse.
The reverse direction (`harness_lint → memory_regen`) would both create an import cycle and drag
`tools.contract_drift.drift` (imported at `inject.py:14`) into a lint that has no business knowing
about drift gates. Zero new dependency edges are needed.

The second-highest: **the no-wall-clock gate is file-scoped and extraction can silently hollow it
out.** `test_inject_determinism.py:70-75` reads `tools/memory_regen/inject.py` **as text** and
asserts five tokens are absent. Move the predicate out and the gate stops covering it. The
extraction is only safe if the gate is widened to the new module in the same task.

**Primary recommendation:** Extract `tools/harness_lint/agreements.py` (file-selection only, no
`datetime` token), have `inject.py::_agreements_block` consume it, widen the no-wall-clock gate to
cover it, ship the lint as `tools/harness_lint/provenance.py` cloning `polyglot_lint`'s shape, and
put `/agree`'s writer in a new zero-dep virtual member `tools/agree/`. Source-only; do not emit.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Agreement file **selection** (glob/`_`/README/symlink/confine) | `tools/harness_lint/agreements.py` (new) | — | Shared by both consumers; harness_lint is the direction `inject.py:15` already imports. |
| Agreement **status** filtering (`active`) | `tools/memory_regen/inject.py` | — | Injector-only concern; the lint must NOT inherit it (see Open Question 1). |
| Agreement **rendering + cap** (N=6/M=700) | `tools/memory_regen/inject.py` | — | Injection-surface concern; stays put. Tests call `inject._agreements_block` directly. |
| Provenance **shape validation** | `tools/harness_lint/provenance.py` (new) | — | D-04. First runnable module in harness_lint. |
| Provenance **fast local signal** | `harness/commands/lint.md` | — | D-04 "both, not either". |
| Provenance **merge gate** | `tools/harness_lint/tests/` → CI `core-suite` | — | D-04. Non-bypassable. |
| `/agree` **write/retire** | `tools/agree/` (new member) | `tools/harness_lint/agree.py` (fallback) | See Q5 — `memory_regen` is **forbidden** by the tier's own README. |
| `/agree` **command surface** | `harness/commands/agree.md` | — | Source-only (D-10). Auto-covered by the glob lint. |
| ADR-0006 **errata** | `docs/adr/` (constitution plane) | — | Via `HARNESS_DEV_BYPASS` (D-12) or raw shell. |

## Standard Stack

### Core

**No new packages.** Every capability is stdlib + already-resolved workspace deps.

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `ruamel.yaml` | resolved (transitive via `check-jsonschema==0.37.4`) | Frontmatter YAML parse | Already the repo's only YAML parser. Accessed **only** through `tools.harness_lint.parse_frontmatter` — never directly. `[VERIFIED: tools/harness_lint/frontmatter.py:8-9, 21]` |
| `pytest` | `>=8.4,<9` (8.4.2 resolved) | The merge gate | `pyproject.toml:17`. `[VERIFIED: pyproject.toml]` |
| `argparse`, `re`, `dataclasses`, `pathlib` | stdlib | Lint + CLI | The exact stdlib set `polyglot_lint`/`approve.py` use. `[VERIFIED]` |

**DO NOT add `pyyaml`.** `tools/harness_lint/pyproject.toml:8` is explicit: *"DO NOT add pyyaml — it
is absent from the lock; parse frontmatter with the already-resolved ruamel.yaml."* `[VERIFIED]`

**Installation:** none. `uv sync` must not resolve a single new external package.

## Package Legitimacy Audit

**Not applicable — this phase installs zero external packages.** No slopcheck run is required; there
is nothing to check. If a plan proposes adding any package, that is a scope violation: both
`tools/harness_lint/pyproject.toml:6-8` and `tools/polyglot_lint/pyproject.toml:6-7` carry an
explicit "this member must never mutate uv.lock" constraint for external deps. `[VERIFIED]`

---

## Q1 — The Shared Predicate (D-05) — ANSWERED WITH file:line

### Where it lives, exactly

`tools/memory_regen/inject.py`, function `_agreements_block` (lines **90-115**). The predicate is
**not** a named function today — it is an inline loop body. Verbatim, lines 96-106:

```python
 96    entries: list[str] = []
 97    for path in sorted(base.glob("*.md")):
 98        if path.name.startswith("_") or path.name == "README.md" or path.is_symlink():
 99            continue
100        try:
101            path.resolve().relative_to(resolved_base)
102            frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
103        except (OSError, ValueError):
104            continue
105        if str(frontmatter.get("status", "")).strip() != "active":
106            continue
```

Plus lines **91-95** (the `resolved_base` setup that line 101 depends on):

```python
 91    base = Path(agreements_dir)
 92    try:
 93        resolved_base = base.resolve()
 94    except OSError:
 95        return ""
```

### Its exact current shape — five distinct layers, not three

CONTEXT D-05 calls this a "3-layer fail-closed exclusion". Reading the code, it is **five**:

| # | Layer | Line | Kind |
|---|-------|------|------|
| L1 | non-recursive sorted `glob("*.md")` | 97 | file selection |
| L2 | `_`-prefix + `README.md` + `is_symlink()` exclusion | 98 | file selection |
| L3 | confinement: `path.resolve().relative_to(resolved_base)` | 101 (+93) | file selection |
| L4 | parse, `except (OSError, ValueError): continue` | 102-104 | file selection (fail-closed) |
| **L5** | **`status != "active"` → skip** | **105** | **status filter — NOT file selection** |

**L1-L4 are "what is an agreement file". L5 is "which agreements does the injector render".** This
distinction is load-bearing and is the subject of Open Question 1 — the lint needs L1-L4 but almost
certainly must **not** inherit L5.

### Can it be extracted without breaking the four invariants?

**Yes. Verified against each one individually.**

**(a) Byte-identity determinism test** — `tools/memory_regen/tests/test_inject_determinism.py:29-54`.
Two tests: `test_assemble_is_byte_identical` and `test_assemble_delete_regenerate_is_byte_identical`,
both SHA-256 comparisons over `inject.assemble(...)`. A pure refactor that preserves output is
invisible to them. **The one thing that must survive verbatim is `sorted()` on line 97** — the
Phase-13 anti-pattern ("unsorted `glob()` returns filesystem order"). `conftest.py:82-88` deliberately
creates the fixture files in non-alphabetical order and `test_tmp_agreements_tree_fixture_shape`
(`test_inject_determinism.py:105`) asserts `_AGREEMENTS_CREATION_ORDER != tuple(sorted(...))` so the
ordering test cannot silently no-op. `test_agreements_order_is_sorted_not_filesystem`
(`test_inject_assembler.py:45-47`) is the live guard. **Verdict: SAFE, sorted() is non-negotiable.**

**(b) No-wall-clock static gate — ⚠ THIS IS THE TRAP.**
`test_inject_determinism.py:70-75`:

```python
def test_inject_module_has_no_wallclock(repo_root: Path) -> None:
    text = (repo_root / "tools/memory_regen/inject.py").read_text(encoding="utf-8")
    for token in ("datetime", "date.today", ".now()", "time.time", "time.monotonic"):
        assert token not in text
```

It reads **one hardcoded file path as text**. Two consequences:

1. The import line `from tools.harness_lint.agreements import iter_agreement_files` contains none of
   the five tokens → the extraction itself does **not** trip the gate. `[VERIFIED: token scan]`
2. **But the extracted module is then not covered by any wall-clock gate.** Extraction moves code out
   from under a live guard. This is the exact Phase-13 anti-pattern ("claimed-but-untested
   invariant") reproduced in reverse. **The plan MUST widen this gate to the new module in the same
   task as the extraction.**

**⚠ Second-order trap:** if the gate is widened to a module, that module can never contain the
literal substring `datetime`. The provenance lint's D-02 check is naturally spelled
`isinstance(value, str)` — which needs **no `datetime` import at all** (a `datetime.date` simply
fails `isinstance(..., str)`). So keep `agreements.py` (gated) and `provenance.py` (not gated,
lint-only) as **separate modules** and the conflict never arises. Do not merge them.

**(c) ~4000-char budget** — `inject.py:135-163`; `test_inject_assembler.py:32-33, 152-158, 160-164`.
The cap logic (`_AGREEMENTS_MAX_ENTRIES=6` / `_AGREEMENTS_MAX_CHARS=700`, lines 113-115) and the
budget loop (155-160) live **outside** the extractable region. Untouched. **Verdict: SAFE.**

**(d) The `agreements_dir` parameter** — `assemble(..., agreements_dir: Path = AGREEMENTS_DIR)` at
`inject.py:139`, threaded to `_agreements_block(agreements_dir)` at line 146. The extracted helper
takes the dir as its argument, so the parameter is preserved verbatim. **Verdict: SAFE.**

### ⚠ A fifth constraint CONTEXT did not name

**`inject._agreements_block` must keep its name and signature.** Seven live tests call it directly as
a private: `test_inject_assembler.py:38, 46, 55, 59, 64, 76, 156`. Extract the *body*, not the
function. `[VERIFIED]`

### Recommended extraction (extraction is preferred per D-05, and it is clean)

New file `tools/harness_lint/agreements.py` — file-selection layers L1-L4 only:

```python
def iter_agreement_files(agreements_dir: Path) -> list[Path]:
    """Sorted, non-recursive, symlink-free, confined *.md agreement files (L1-L3)."""

def load_agreement(path: Path) -> tuple[dict, str] | None:
    """Parse one confined agreement -> (frontmatter, body), or None on OSError/ValueError (L4)."""
```

`inject.py::_agreements_block` becomes a consumer that adds L5 (`status == "active"`) + render + cap.
`provenance.py` consumes the same helper and applies its own checks to **every** agreement file.

**Fallback (only if extraction proves invasive — it does not appear to):** a parity test asserting
`set(iter_agreement_files(d)) == {paths the injector selected}` over the shared `tmp_agreements_tree`
corpus. Even if extraction lands, **ship this parity test anyway** — it costs ~10 lines and is the
regression net that makes D-05's "they must never disagree" an *asserted* invariant rather than a
prose claim (the exact Phase-13 lesson).

## Q2 — Cross-Member Import Safety — ANSWERED

**The safe direction is `tools/memory_regen` → `tools/harness_lint`. It already exists.**

`tools/memory_regen/inject.py:15`: `from tools.harness_lint import parse_frontmatter` `[VERIFIED]`

| Check | Finding |
|-------|---------|
| **uv workspace membership** | `pyproject.toml:34` — `members = ["libs/python", "tools/*"]`. Both are members. `uv.lock:14,17` lists `logparser-harness-lint` + `logparser-memory-regen`. Cross-member import by module path is the established idiom (`tools` is a namespace package with no `tools/__init__.py`). `[VERIFIED]` |
| **Cycle risk (proposed direction)** | **None.** `harness_lint` imports nothing from `memory_regen`. |
| **Cycle risk (reverse direction)** | **Real.** `harness_lint.provenance → memory_regen.inject → harness_lint` is a cycle. It would *technically* resolve (see PEP-562 below) but would also drag `tools.contract_drift.drift` (`inject.py:14`) and, transitively, tree-sitter/networkx-adjacent machinery into a pure lint. **Reject.** |
| **PEP-562 lazy re-export** | `tools/harness_lint/__init__.py:19-24` is a lazy `__getattr__`. Its docstring (lines 7-11) names the precedent: *"an eager top-level import here would run during pytest's conftest-collection bootstrap before the repo root is on `sys.path`, breaking collection (mirrors tools/harness_perms)."* **`[VERIFIED]`** |
| **Recommended import form** | **Import the submodule directly** — `from tools.harness_lint.agreements import iter_agreement_files` — and do **not** touch `__init__.py`'s `__all__`. This sidesteps the collection hazard entirely with zero new lazy-export plumbing. If a plan *does* add to `__all__`, it must extend the `__getattr__` branch, not add a top-level import. |
| **GEN-04** | **No violation.** `test_core_no_example_dep.py` scans for `examples/` references; `test_core_no_workspace_member_dep.py:37,61-68` scans core files for **`workspace.toml` `[[members]].root` path markers** (e.g. `tests/fixtures/workspace/member-a`) — a different concept from uv members. A `tools/`→`tools/` Python import is not scanned by either. `[VERIFIED: read both guards]` |

## Q3 — Runnable-Lint Shape (`tools/polyglot_lint/lint.py`) — ANSWERED

**The exact shape to clone:**

| Element | Line | Shape |
|---------|------|-------|
| Violation | 47-53 | `@dataclass(frozen=True)` with exactly two `str` fields: `rule` (stable code) + `detail` (human-readable) |
| Pure checkers | 55, 65 | `lint_bytes(raw) -> list[Violation]`, `lint_tsv(text, kinds) -> list[Violation]`. Clean input → `[]`, never `None`, never raise. |
| File entry | 106-115 | `lint_file(path: str \| Path, ...) -> list[Violation]` — composes the pure checkers |
| CLI | 118-142 | `def main(argv: list[str] \| None = None) -> int` with `import argparse` **inside the function** (lines 124-126) |
| Exit codes | 138, 142 | **0** clean / **1** any violation |
| Output split | 138, 141 | OK → `print(...)` **stdout**: `f"polyglot-lint: OK — {path}"`. FAIL → `print(..., file=sys.stderr)`: `f"polyglot-lint: FAIL [{v.rule}] {v.detail}"`, one line per violation (**all** violations printed, not just the first) |
| Module guard | 145-146 | `if __name__ == "__main__": raise SystemExit(main())` |

**How `/lint` invokes it** — `harness/commands/lint.md:37`, a `!`-prefixed bash macro. Verbatim
structure, worth cloning:

```
!`fail=0; files=$(git ls-files '*.tsv'); if [ -z "$files" ]; then echo "SKIP: ..."; else
  for f in $files; do uv run python -m tools.polyglot_lint.lint "$f" || fail=1; done;
  if [ "$fail" -ne 0 ]; then echo "FAIL: ..."; exit 1; fi; echo "OK: ..."; fi`
```

Three properties the provenance step must copy `[VERIFIED: lint.md:29-37]`:
1. **Presence-safe** — zero matching files → announced SKIP, exit 0, never a false failure. **This
   matters enormously here: the active agreement set is legitimately EMPTY.** A provenance step that
   fails on an empty dir would break `/lint` on day one.
2. **Accumulate-then-fail** — `|| fail=1` per file, single exit at the end, so all violations surface
   in one run.
3. **`uv run python -m tools.<member>.<module>`** — module path, never a file path.

`lint.md` also states the design law this phase inherits: *"Thin macro over the canonical linters.
Wraps the existing tools; adds no new rules"* (line 14) and *"one engine, three sites"* (line 32).

## Q4 — Refusal Shape (`tools/golden_runner/approve.py`) — ANSWERED

| Element | Line | Shape |
|---------|------|-------|
| Exception | 29-30 | `class GoldenApprovalRefused(Exception)` — one dedicated class, one-line docstring |
| Pure fn | 33-71 | `promote(case, *, approve=False, adr=None, human_token=None) -> Path` — **keyword-only** signals after `*`. Raises; does not return an error code. |
| Guard order | 47, 52, 59, 66 | Cheapest/most-explicit signal first, expensive existence check last |
| Message style | 47-50 | `"REFUSED: <what is required> (<why, with the citation>)."` — always the `REFUSED: ` prefix, always names the missing signal **and** the path to supply it |
| CLI | 74-98 | argparse; `try: promote(...) except GoldenApprovalRefused as exc: print(str(exc)); return 3` |
| Exit codes | 96, 98 | **3** refused / **0** success |
| Success line | 97 | `f"PROMOTED: {verified} (ADR: {args.adr})."` — affirmative, names the artifact + the cited authority |

**The blank/whitespace-is-not-a-signal rule** — two co-existing spellings, both verified:

- `approve.py:57-58` — the expected value is read from the env via `os.environ.get(HUMAN_TOKEN_ENV)`,
  then the guard is `if not <expected> or <supplied> != <expected>:` — a falsy `""` refuses.
  *(Quoted descriptively rather than verbatim: the literal line trips the repo's own `secret_scan`
  shape rule, `secret_scan.py:47`.)*
- `_stdin.py:42-44` — `bool((os.environ.get(DEV_BYPASS_ENV) or "").strip())` — **the stricter one;
  catches `"   "`**
- `contract_guard.py:103` — `bool((os.environ.get(APPROVAL_ENV) or "").strip())`

**For `/agree --because`, use the `.strip()` form:** `if not (because or "").strip(): raise
AgreementRefused(...)`. `--because "   "` must refuse. `approve.py`'s bare-falsy check is the older,
weaker spelling; `_stdin.py`/`contract_guard.py` are the current convention. ADR-0007:52 states the
rule normatively: *"unset / empty / whitespace-only ⇒ no bypass."* `[VERIFIED]`

**⚠ One deliberate divergence to decide:** `approve.py:94` prints the refusal to **stdout**;
`lint.py:141` prints failures to **stderr**. `/agree` should follow `approve.py` (stdout) since it is
the refusal precedent D-07 names verbatim; the provenance lint should follow `lint.py` (stderr).
Note it in the plan so it reads as a choice, not an inconsistency.

**Command-authoring precedent** — `harness/commands/golden-approve.md`:
- Frontmatter: `description: >-` folded block **starting with "Use when…"** (line 3), `agent:` slug
- Body: *"Thin macro over the **already-coded** refusal gate. Do NOT re-implement approval logic"* (11-12)
- `!`python -m tools.golden_runner.approve $ARGUMENTS`` — **positional `$ARGUMENTS` pass-through, no
  shell-string construction from arguments** (16-19). Injection-safe; clone verbatim.
- A "The human gate (refusal is the default)" section enumerating each required signal + a worked
  example.

## Q5 — Where `/agree`'s Write Logic Lives — ANSWERED

### What a new uv member costs — measured, not assumed

| Question | Answer |
|----------|--------|
| Root `pyproject.toml` edit? | **No.** `members = ["libs/python", "tools/*"]` is a **glob** (`pyproject.toml:34`). Any new `tools/<name>/pyproject.toml` is auto-enrolled. `[VERIFIED]` |
| `package = false` needed? | **Yes** — `[tool.uv] package = false`. Every existing tools member sets it (harness_lint:11-14, memory_regen:19-23, polyglot_lint:10-13). Without it uv tries to build a wheel and `uv sync` fails. `[VERIFIED]` |
| `uv.lock` churn? | **Minimal + deterministic.** One name in the sorted top list (`uv.lock:7-21`) + a 4-line block:<br>`[[package]]` / `name = "logparser-agree"` / `version = "0.0.0"` / `source = { virtual = "tools/agree" }`. That is the **entire** diff for a zero-dep member — verified against the real `logparser-harness-lint` (274-277) and `logparser-harness-perms` (279-282) entries. |
| Is any test guarding `uv.lock`? | **No.** Grepped `tools/` + `.github/` for `uv.lock`: every hit is a *comment* in a pyproject or a docstring/snapshot string. **Zero assertions over lock content.** `[VERIFIED]` |
| Does Phase 2's D-01 warning bite? | **No.** That warning is about **external dependency resolution** contention (`memory_regen/pyproject.toml:8-10`: *"Declared here so uv.lock resolves ONCE in Wave 1; Wave-2 plans never contend on the lock"*). A zero-dep virtual member triggers no resolution. Keep `dependencies = []` and the warning is inapplicable. `[VERIFIED]` |

### The homes, ranked

| Option | Verdict |
|--------|---------|
| **`tools/memory_regen/agree.py`** | **FORBIDDEN.** `.memory/agreements/README.md:4-5` states the tier *"is never regenerated, is **never written by `tools/memory_regen`**, and does not collide with `.memory/derived/`."* Putting the writer there contradicts the tier's own committed contract. **Do not propose this.** `[VERIFIED]` |
| **`tools/agree/` (new member)** — **RECOMMENDED** | Honest home; the writer is neither a validator nor about `harness/`. Cost: 4 lines of lock + one sorted-list entry, no resolution, no guard test. Needs `tools/agree/tests/conftest.py` with the sys.path shim (clone `tools/memory_regen/tests/conftest.py:26-33` verbatim — `parents[3]` → repo root + `libs/python`). |
| **`tools/harness_lint/agree.py`** (fallback) | Zero lock churn. But harness_lint's `pyproject.toml:4` description reads *"structural validators for the harness/ single source"* — a writer to `.memory/` fits neither half. If chosen, **the description must be amended in the same commit**, or the member's stated contract becomes false (the very defect D-12 is cleaning up in ADR-0006). |

**Recommendation: `tools/agree/`.** The measured lock cost is 4 deterministic lines with no guard test
and no resolver involvement; the conceptual cost of misfiling the writer is higher and permanent.
`[ASSUMED — a judgement call, not a verified fact; D-13's "Claude's Discretion" covers module naming]`

## Q6 — The `added:` Quoting Defect (D-02) — ANSWERED, EMPIRICALLY

### What `parse_frontmatter` actually does — run live this session

```
$ uv run python -c "from tools.harness_lint import parse_frontmatter; ..."
'YYYY-MM-DD'                str      # added: YYYY-MM-DD    (the literal placeholder)
datetime.date(2026, 7, 16)  date     # added: 2026-07-16    (a real date, unquoted)  ← the defect
'2026-07-16'                str      # added: "2026-07-16"  (quoted)                 ← the fix
```

### ⚠ The defect is subtler than CONTEXT D-02 states — and this makes the fix MORE important

D-02 says `_TEMPLATE.md:3` *"currently ships `added: YYYY-MM-DD` unquoted, which YAML parses into a
`datetime.date` object."* **That is not what happens.** `YYYY-MM-DD` is not a valid YAML timestamp,
so ruamel falls back to `str` — the template's placeholder parses as `str` **today**.

The defect is a **latent teaching defect**, not a live parse defect: the template teaches the
*unquoted shape*, and the instant `/agree` substitutes a real ISO date into it, the value becomes
`datetime.date`. The lint would then reject every file `/agree` itself wrote. **D-02's fix
(`added: "YYYY-MM-DD"`) is correct and necessary — the reasoning in D-02 is what needs the
correction, not the decision.** Do not re-litigate the decision; do record the corrected mechanism.

### Phase 13's binding precedent

| Evidence | Finding |
|----------|---------|
| `tools/memory_regen/tests/conftest.py:99, 110, 131` | Every synthetic agreement writes `added: "2026-01-02"` — **quoted** `[VERIFIED]` |
| `tools/memory_regen/tests/test_inject_assembler.py:19` | The `updated:` stamp fixture writes `updated: "2026-01-02"` — **quoted** `[VERIFIED]` |
| `tools/memory_regen/inject.py:124` | `stamp = str(frontmatter.get("updated", "")).strip()` — the **injector defensively coerces** |
| `tools/memory_regen/inject.py:105` | `str(frontmatter.get("status", "")).strip() != "active"` — same coercion |

**The critical asymmetry:** the injector **coerces with `str()`** (it must degrade gracefully — see
`test_absent_stamp_degrades_gracefully`, `test_inject_assembler.py:109-117`). **The lint must NOT
coerce** (D-02: *"a bare date object must FAIL, not be silently coerced"*). This is not a
contradiction — the injector's job is to never crash a session; the lint's job is to fail loud. Both
share the *file-selection* predicate (L1-L4); neither shares the other's *value handling*. Another
reason L5 must not be bundled into the shared helper.

### The exact assertion shape

```python
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PROVENANCE = re.compile(r"^added because \S")          # D-01: prefix + non-empty tail
_STATUS = frozenset({"active", "retired"})              # D-01

added = frontmatter.get("added")
if not isinstance(added, str):
    # An unquoted YAML scalar parses to a date object; quote it so it round-trips as str (D-02).
    violations.append(Violation("PROV-added-type", f"'added' must be a QUOTED string; got "
                                f"{type(added).__name__} — write added: \"YYYY-MM-DD\"."))
elif not _ISO_DATE.match(added):
    violations.append(Violation("PROV-added-format", f"'added' must be ISO YYYY-MM-DD; got {added!r}."))
```

**Order is load-bearing:** the `isinstance` check must come **first**. Applying `_ISO_DATE.match()` to
a `date` object raises `TypeError`, which would crash the lint instead of failing it. Ship a test that
proves the date-object path produces a **Violation, not an exception**.

**No `import datetime` is required anywhere** — `isinstance(x, str)` is `False` for a date object
without naming the type. This keeps the door open to widening the wall-clock gate over
`agreements.py` without a token collision (Q1(b)).

## Architecture Patterns

### System Architecture Diagram

```
  user types feedback mid-work
            │
            ▼
   /agree  (harness/commands/agree.md)          ── source-only, NOT emitted (D-10)
            │  !`uv run python -m tools.agree $ARGUMENTS`   ← positional, no shell construction
            ▼
   tools/agree/write.py
     ├── --because missing/blank/ws? ──► AgreementRefused ──► stdout "REFUSED: …" ──► exit 3
     ├── --retire <slug> ─► flip status: active → retired IN PLACE (never delete, D-09)
     └── add ─► fill _TEMPLATE.md shape ─► .memory/agreements/<slug>.md
                   status: active | added: "<ISO>" | provenance: "added because <--because>"
            │
            │                    ┌─────────────────────────────────────────┐
            ▼                    │   tools/harness_lint/agreements.py      │  ← NEW, SHARED (D-05)
   .memory/agreements/*.md ─────►│   iter_agreement_files()  L1-L4 only:   │
   (committed, writable,         │   sorted glob("*.md") · no `_`/README   │
    NOT constitution)            │   · no symlink · confined · fail-closed │
                                 └───────┬─────────────────────┬───────────┘
                                         │                     │
                    ┌────────────────────┘                     └──────────────────┐
                    ▼                                                             ▼
      tools/harness_lint/provenance.py                        tools/memory_regen/inject.py
        checks ALL agreement files:                             _agreements_block() adds:
          status ∈ {active, retired}                              L5  status == "active"
          added   isinstance str + ISO                            render title + rule only
          provenance ^added because \S                            cap N=6 / M=700 → pointer
        list[Violation] · main() exit 0/1                       assemble() → priority-0 directive
                    │                                                   │
        ┌───────────┴────────────┐                                      ▼
        ▼                        ▼                              SessionStart payload
  /lint (fast, local)   tools/harness_lint/tests/               (≤4000 chars, byte-identical)
  presence-safe skip     → CI core-suite = MERGE GATE
```

### Recommended Structure

```
tools/agree/                       # NEW zero-dep virtual member
├── pyproject.toml                 # dependencies = [] ; [tool.uv] package = false
├── __init__.py
├── write.py                       # AgreementRefused + add/retire + main() exit 0/3
└── tests/
    ├── __init__.py
    ├── conftest.py                # sys.path shim — clone memory_regen/tests/conftest.py:26-33
    └── test_agree_refusal.py

tools/harness_lint/
├── agreements.py                  # NEW — shared L1-L4 predicate (no `datetime` token, ever)
├── provenance.py                  # NEW — D-04 lint, clones polyglot_lint/lint.py shape
└── tests/
    ├── test_provenance.py         # NEW
    └── test_agreements_predicate.py  # NEW — includes the injector-parity test

tools/memory_regen/inject.py       # EDIT — _agreements_block consumes iter_agreement_files
tools/memory_regen/tests/test_inject_determinism.py  # EDIT — widen the wall-clock gate (Q1b)
harness/commands/agree.md          # NEW source-only — auto-covered by the glob lint
harness/commands/lint.md           # EDIT — add the presence-safe provenance step
.memory/agreements/_TEMPLATE.md    # EDIT — added: "YYYY-MM-DD"  (D-02)
docs/adr/0006-*.md                 # APPEND ## Errata (D-12) — constitution plane
```

### Pattern: Split the predicate by *concern*, not by *caller*

**What:** `agreements.py` answers "is this a valid agreement file?" (L1-L4). `inject.py` answers
"should I render it?" (L5). `provenance.py` answers "is its stamp well-formed?".
**When:** whenever two consumers need overlapping-but-not-identical filtering — the exact D-05 case.
**Why:** the naive read of D-05 ("share the 3-layer filter") would give the lint L5, silently
exempting every retired file from provenance checking forever (D-09 keeps them forever). See Open
Question 1.

### Anti-Patterns to Avoid

- **Two hand-kept copies of the predicate.** D-05's whole point. Even if extraction lands, ship the
  parity test — the copy risk returns the moment someone "optimizes" one side.
- **Merging `agreements.py` and `provenance.py`.** The wall-clock gate widening (Q1b) makes
  `agreements.py` a token-restricted module; the lint should be free of that constraint.
- **Renaming or inlining `inject._agreements_block`.** Seven tests call it directly.
- **A provenance lint step that fails on an empty dir.** The active set is legitimately empty
  (D-13). Presence-safe skip, per `lint.md:34-37`.
- **A PreToolUse hook to "enforce" provenance.** Explicitly **rejected** by D-03, not deferred. It
  cannot enforce truth (see Security Domain).
- **Writing to the real `.memory/agreements/` to exercise anything.** `tmp_path` + `agreements_dir=`
  only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Frontmatter parse | `---` fence slicing | `tools.harness_lint.parse_frontmatter` | CRLF-safe (`frontmatter.py:40`), fail-safe on unclosed fences (55), safe loader (61). `test_commands.py:17` states the convention. |
| YAML load | `import yaml` | `ruamel.yaml` via the parser above | pyyaml is **absent from the lock** (`harness_lint/pyproject.toml:8`). |
| Path confinement | `str(p).startswith(base)` | `path.resolve().relative_to(base)` + `is_symlink()` | `inject.py:98,101`; `docs_sync/generate.py:189-195`; `golden_runner/runner.py:88-102`. D-06. |
| Agreement file selection | a second glob+filter | `iter_agreement_files()` | D-05 — the entire point of this phase's refactor. |
| Refusal semantics | `return False` / print+continue | `AgreementRefused` → exit 3 | `approve.py:29-30, 91-96`. D-07. |
| Violation reporting | tuples / dicts / strings | `@dataclass(frozen=True) Violation(rule, detail)` | `lint.py:47-53`. D-04. |
| Blank-signal detection | `if not x` | `bool((x or "").strip())` | `_stdin.py:44`; ADR-0007:52. |
| Command→module invocation | shell string built from args | `!`… $ARGUMENTS`` positional | `golden-approve.md:16-19`. Injection-safe. |
| A command-name list | a new `EXPECTED_COMMANDS` frozenset | the existing glob | **D-11.** `test_commands.py:47, 63, 70, 85, 103` is glob-driven — `agree.md` is auto-covered with **zero test edits**. |

**Key insight:** every shape this phase needs is already ratified in-repo. The phase's real work is
**one careful extraction** plus **authoring**, not construction. A plan that introduces a new
`Violation`-like type, a new refusal idiom, or a new frontmatter reader has failed.

## Common Pitfalls

### Pitfall 1: Extraction silently hollows out the no-wall-clock gate — ⚠ HIGHEST RISK
**What goes wrong:** `agreements.py` is extracted; `test_inject_module_has_no_wallclock` still passes
(it reads only `inject.py`) — but nothing now guards the extracted code. A later edit adds
`date.today()` there and the suite stays green.
**Why:** the gate hardcodes one file path (`test_inject_determinism.py:72`).
**Avoid:** widen it to the new module **in the same task as the extraction**. Prove it with a
negative control (a synthetic clock token must be flagged) — `test_core_no_workspace_member_dep.py:141-147`
is the in-repo pattern for "prove the scan is live and cannot silently no-op".
**Warning sign:** the extraction task and the gate-widening task land in different waves.

### Pitfall 2: The lint inherits the `active` filter and never checks a retired file
**What goes wrong:** D-05's "3-layer" phrasing includes status. Bundle L5 into the shared helper and
`provenance.py` skips every `status: retired` file — which, per D-09, is where every retired
agreement lives **forever**.
**Avoid:** share L1-L4 only. See Open Question 1.
**Warning sign:** `iter_agreement_files` has a `status` parameter.

### Pitfall 3: Regex-matching a date object raises instead of failing
**What goes wrong:** the ISO regex is applied before the type check → `TypeError` crashes the lint. A
crashed gate lets the guarded thing through.
**Avoid:** `isinstance` first, always. Test that the date-object path yields a `Violation`.
**Warning sign:** no test feeds an unquoted real date.

### Pitfall 4: The `/lint` provenance step fails on the empty active set
**What goes wrong:** `/lint` goes red on every developer machine on day one, because there are zero
agreements and the step treats "no files" as failure.
**Avoid:** presence-safe skip, cloning `lint.md:37`'s `if [ -z "$files" ]; then echo "SKIP: …"` branch.
**Warning sign:** the step is not exercised against an empty dir.

### Pitfall 5: Emitting, or "fixing" the red `harness_emit` snapshot
**What goes wrong:** `harness/commands/agree.md` gets emitted → `test_coexist.py:53-54`'s hard
**19** breaks. Or someone runs `--snapshot-update` and **steals Phase 15's gate**.
**Avoid:** D-10 — source-only. **Verified live this session:** `harness/commands/*.md` = exactly
**19** files, and `uv run pytest tools/harness_emit tools/memory_regen tools/harness_lint -q` →
**1 failed, 359 passed**, the single failure being `test_projected_tree_matches_committed_snapshot`.
**That is the correct baseline.**
**Warning sign:** any diff under `.opencode/` or `.claude/`, or under
`tools/harness_emit/tests/__snapshots__/`.

### Pitfall 6: Substring-matching a gate (Phase-13 lesson, inherited)
**What goes wrong:** a naive token scan false-passes. `test_inject_determinism.py:82-83` documents
the real case: a bare `date` scan matched "up**date**" in `gsd-check-update.js`, so the gate asserts
`re.search(r"^\s*date\b", ..., flags=re.MULTILINE)` **and** `assert "gsd-check-update" in shell`
*to prove the gate avoids the false positive*.
**Avoid:** command-shaped tokens + a positive control proving the near-miss is tolerated.

### Pitfall 7: Verifying a claimed invariant by reading prose (Phase-13 lesson)
`inject.py:20-22`'s docstring asserted delete+regen byte-identity while **no test asserted it**.
Phase 13 found three false stated guarantees; this session found a fourth (ADR-0006's phantom seed)
and a fifth (D-02's stated parse mechanism — see Q6). **Grep for the test before trusting any
"is preserved" claim.**

## Code Examples

### The predicate, extracted (Source: derived from `tools/memory_regen/inject.py:90-106`)

```python
# tools/harness_lint/agreements.py
"""The single .memory/agreements/ file-selection predicate (D-05).

Shared by tools/memory_regen/inject.py (which adds the status filter + render + cap) and
tools/harness_lint/provenance.py (which checks every agreement file's stamp). Two copies of
this predicate would drift, and a drift means the lint and the injector disagree about what an
agreement IS.

Selection is fail-closed and confined (D-06, mirroring tools/docs_sync._confine): non-recursive
sorted glob, never rglob, no symlink follow, never outside agreements_dir. `sorted` is
load-bearing — bare glob() returns filesystem order and would break byte-identity determinism.

Deliberately EXCLUDES the `status: active` filter: that is the INJECTOR's render policy, not the
definition of an agreement file. The lint must check retired entries too (they live forever, D-09).

This module is covered by the no-wall-clock static gate — it must never contain a clock token.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_lint.frontmatter import parse_frontmatter


def iter_agreement_files(agreements_dir: Path) -> list[Path]:
    """Sorted, non-recursive, symlink-free, confined ``*.md`` agreement files (L1-L3)."""
    base = Path(agreements_dir)
    try:
        resolved_base = base.resolve()
    except OSError:
        return []
    selected: list[Path] = []
    for path in sorted(base.glob("*.md")):  # sorted: determinism, never filesystem order
        if path.name.startswith("_") or path.name == "README.md" or path.is_symlink():
            continue
        try:
            path.resolve().relative_to(resolved_base)
        except (OSError, ValueError):
            continue
        selected.append(path)
    return selected


def load_agreement(path: Path) -> tuple[dict, str] | None:
    """Parse one agreement into ``(frontmatter, body)``; ``None`` on unreadable/malformed (L4)."""
    try:
        return parse_frontmatter(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
```

### `inject._agreements_block` as a consumer (name + signature preserved — 7 tests depend on them)

```python
# tools/memory_regen/inject.py — replaces lines 90-115
from tools.harness_lint.agreements import iter_agreement_files, load_agreement

def _agreements_block(agreements_dir: Path = AGREEMENTS_DIR) -> str:
    entries: list[str] = []
    for path in iter_agreement_files(agreements_dir):
        loaded = load_agreement(path)
        if loaded is None:
            continue
        frontmatter, body = loaded
        if str(frontmatter.get("status", "")).strip() != "active":  # L5: injector render policy
            continue
        rendered = _render_agreement(body)
        if rendered:
            entries.append(rendered)
    if not entries:
        return ""
    block = AGREEMENTS_HEADER + "\n" + "\n".join(entries)
    if len(entries) > _AGREEMENTS_MAX_ENTRIES or len(block) > _AGREEMENTS_MAX_CHARS:
        return AGREEMENTS_POINTER
    return block
```

### The parity test (D-05's fallback — ship it regardless)

```python
# tools/harness_lint/tests/test_agreements_predicate.py
def test_lint_and_injector_select_the_same_files(tmp_agreements_tree: Path) -> None:
    """The shared predicate and the injector never disagree about what an agreement IS (D-05)."""
    from tools.harness_lint.agreements import iter_agreement_files, load_agreement
    from tools.memory_regen import inject

    selected = iter_agreement_files(tmp_agreements_tree)
    assert {p.name for p in selected} == {"alpha-ground.md", "middle-retired.md", "zeta-proceed.md"}

    block = inject._agreements_block(tmp_agreements_tree)
    active = [p for p in selected if (load_agreement(p) or ({}, ""))[0].get("status") == "active"]
    assert {p.name for p in active} == {"alpha-ground.md", "zeta-proceed.md"}
    for path in active:
        title = next(ln[2:].strip() for ln in path.read_text().splitlines() if ln.startswith("# "))
        assert title in block
    assert "Retired rule" not in block  # retired: selected by the predicate, not rendered
```

### `/agree` refusal (Source: mirrors `tools/golden_runner/approve.py:29-30, 47-50, 91-96`)

```python
class AgreementRefused(Exception):
    """Agreement write refused (no verbatim user feedback to stamp as provenance)."""


def add(slug: str, title: str, rule: str, *, because: str | None = None,
        added: str | None = None, agreements_dir: Path = AGREEMENTS_DIR) -> Path:
    if not (because or "").strip():
        raise AgreementRefused(
            "REFUSED: an agreement is written ONLY in response to explicit user feedback. "
            'Supply the verbatim feedback with --because "<what the user said>"; it becomes the '
            "provenance stamp. An agent must not invent one (MEM2-04, §2 property 2)."
        )
    ...

def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(
        description="Add or retire a .memory/agreements/ working-agreement (user-feedback-gated)."
    )
    parser.add_argument("slug", help="agreement slug (file stem under .memory/agreements/)")
    parser.add_argument("--because", default=None,
                        help="VERBATIM user feedback; becomes the provenance stamp (required to add)")
    parser.add_argument("--retire", action="store_true",
                        help="flip status: active -> retired in place (never deletes, D-09)")
    args = parser.parse_args(argv)
    try:
        path = retire(args.slug) if args.retire else add(args.slug, ..., because=args.because)
    except AgreementRefused as exc:
        print(str(exc))
        return 3
    print(f"AGREED: {path}.")
    return 0
```

### The `/lint` step (Source: mirrors `harness/commands/lint.md:37`, presence-safe)

```
!`files=$(git ls-files '.memory/agreements/*.md' | grep -v -e '/_' -e '/README.md$' || true); if [ -z "$files" ]; then echo "SKIP: no agreement entries — provenance check is a no-op (exit 0)."; else fail=0; for f in $files; do uv run python -m tools.harness_lint.provenance "$f" || fail=1; done; if [ "$fail" -ne 0 ]; then echo "FAIL: provenance violation(s) above — every agreement needs a well-formed origin stamp (MEM2-04)."; exit 1; fi; echo "OK: all agreement entries carry a well-formed provenance stamp."; fi`
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `.memory/agreements/` inert committed data | priority-0 executable directive channel | Phase 13 | Why this phase is a security control (D-03), not formatting |
| Interim defenses: title+rule render, N=6/M=700, scope header (D-15..D-19) | durable provenance lint | **This phase** | T-13-01's mitigation |
| Agreements had no write path (hand-authored) | `/agree` is the sanctioned + only path | **This phase** | ADR-0006:92-93's "no write tooling until Phase 14" is now satisfied |
| Predicate inline in `inject.py` | shared `agreements.py` | **This phase** | D-05 |

**Deprecated/outdated in the upstream wording — three SC/requirement defects to plan around:**

1. **`EXPECTED_COMMANDS` (ROADMAP SC3 + MEM2-04:24) does not exist.** Grepped: no such symbol.
   **D-11 already resolves this** — the glob (`test_commands.py:47`) auto-covers `agree.md`.
   `[VERIFIED]`
2. **"agents cannot auto-invent entries" (SC2 / MEM2-04) overclaims.** **D-03 already resolves this** —
   the lint enforces shape, not truth.
3. **⚠ NEW — SC2's "follows the existing `stale-derived` gate pattern (regenerate → verify)" is a
   category error CONTEXT does not cover.** `test_ci_stale_derived.py:1-18` is a **regenerate→diff**
   gate for **DERIVED** artifacts (`git add -A` + `git diff --cached --exit-code`). But
   `.memory/agreements/README.md:3-5` states the tier *"is not derived: it is never regenerated."*
   **A human-authored tier cannot be regenerate→verified.** The correct pattern is the one D-04
   already names — `polyglot_lint`'s **validate-in-place** shape. D-04 and SC2 conflict; **D-04 is
   correct and D-04 wins** (CONTEXT decisions are locked and were written after the ROADMAP). The
   plan should state this explicitly so a verifier does not fail the phase against SC2's literal
   wording. `[VERIFIED: read both files]`

## Runtime State Inventory

**Omitted — not a rename/refactor/migration phase.** The `_agreements_block` change is an in-repo
code extraction with no stored data, no live service config, no OS-registered state, no secrets, and
no build artifacts carrying a changed name. `.memory/agreements/` holds exactly two committed files
(`git ls-files` → `README.md`, `_TEMPLATE.md`) and gains none in this phase.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `uv` | every test/lint invocation | ✓ | workspace resolved; `uv run pytest` ran clean this session | — |
| `pytest` | the merge gate | ✓ | 8.4.2 (`>=8.4,<9`) | — |
| `ruamel.yaml` | `parse_frontmatter` | ✓ | transitive via `check-jsonschema==0.37.4` | — |
| `git` | `/lint` file discovery, guard scans | ✓ | `git ls-files` verified | — |
| `.NET SDK` | — | ✗ | — | **Not needed.** Phase 14 is Python-only. |
| `.claude/settings.local.json` | `HARNESS_DEV_BYPASS` (D-12 only) | ✗ **ABSENT** | — | `export HARNESS_DEV_BYPASS=1` in the shell, or raw-shell append (see Security Domain) |

**Missing with no fallback:** none.
**Missing with fallback:** `.claude/settings.local.json` — gitignored (`.gitignore:26-27`) and absent
in this checkout. Only blocks D-12's errata write, and two fallbacks exist.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (`>=8.4,<9`, `pyproject.toml:17`) + syrupy 5.2.0 for snapshots |
| Config file | `pyproject.toml:37-41` — `testpaths = ["libs/python", "tools"]`, `addopts = "-ra"` |
| Quick run | `uv run pytest tools/harness_lint tools/memory_regen -q` (~0.5s; **must be 0 failed**) |
| Full suite | `uv run pytest -q` — **expect exactly 1 failed** (`test_projected_tree_matches_committed_snapshot`) |

**Baseline verified live this session:** `uv run pytest tools/harness_emit tools/memory_regen
tools/harness_lint -q` → **1 failed, 359 passed in 1.07s**. The one failure is Phase 15's debt.

### Phase Requirements → Test Map

| Req | Behavior | Type | Automated Command | File |
|-----|----------|------|-------------------|------|
| MEM2-04 | Well-formed stamp passes | unit | `uv run pytest tools/harness_lint/tests/test_provenance.py -x` | ❌ Wave 1 |
| MEM2-04 | **NEG:** `provenance:` absent → Violation | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **NEG:** `provenance: "because x"` (no `added ` prefix) → Violation | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **NEG:** `provenance: "added because"` (empty tail) → Violation | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **NEG:** `provenance: "added because   "` (ws tail) → Violation | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **NEG:** `added: 2026-07-16` unquoted → date object → **Violation, NOT TypeError** | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **NEG:** `added: "16-07-2026"` → Violation | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **NEG:** `status: pending` (∉ {active,retired}) → Violation | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **NEG:** `status: retired` entry **IS linted** (not skipped) | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **EXCL:** `_TEMPLATE.md` + `README.md` **excluded, not flagged** | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | **EXCL:** symlinked `escape.md` not read (mirror `test_inject_assembler.py:72-76`) | unit | `test_agreements_predicate.py` | ❌ Wave 1 |
| MEM2-04 | Empty dir → `[]`, exit 0 (**presence-safe**) | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | `main()` exit 0 clean / 1 dirty; FAIL→stderr, OK→stdout | unit | `test_provenance.py` (capsys) | ❌ Wave 1 |
| MEM2-04 | Predicate is **sorted**, not filesystem order | unit | `test_agreements_predicate.py` | ❌ Wave 1 |
| MEM2-04 | **D-05 parity:** lint & injector select the same files | integration | ↑ | ❌ Wave 1 |
| MEM2-04 | `/agree --because ""` / `"   "` / omitted → **exit 3** | unit | `tools/agree/tests/test_agree_refusal.py` | ❌ Wave 1 |
| MEM2-04 | `/agree --because "<x>"` → file whose stamp **passes provenance** (round-trip) | integration | ↑ | ❌ Wave 1 |
| MEM2-04 | `--retire <slug>` flips status in place; **file still exists**; diff limited to the status line | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | `--retire` of an unknown slug → refuse, no file created | unit | ↑ | ❌ Wave 1 |
| MEM2-04 | `agree.md` passes the glob command lint (**D-11**, zero edits) | unit | `uv run pytest tools/harness_lint/tests/test_commands.py -q` | ✅ **exists** |
| MEM2-04 | `agree.md` description carries a `_ROUTING_TRIGGERS` token | unit | ↑ | ✅ **exists** |
| **REGRESSION** | byte-identity determinism survives extraction | unit | `uv run pytest tools/memory_regen/tests/test_inject_determinism.py -q` | ✅ **exists** |
| **REGRESSION** | wall-clock gate **widened to `agreements.py`** + negative control | unit | ↑ (EDIT) | ⚠ **EDIT — Q1(b)** |
| **REGRESSION** | ~4000-char budget holds | unit | `test_inject_assembler.py:32, 152-158` | ✅ **exists** |
| **REGRESSION** | `harness_emit` no worse than **1 failed / 46 passed** | smoke | `uv run pytest tools/harness_emit -q` | ✅ **exists** |
| **REGRESSION** | `.opencode/` + `.claude/` untouched (**D-10**) | smoke | `git status --porcelain .opencode .claude` → empty | manual |

### Sampling Rate

- **Per task commit:** `uv run pytest tools/harness_lint tools/memory_regen -q` — **0 failed**
- **Per wave merge:** `uv run pytest -q` — **exactly 1 failed** (the `harness_emit` snapshot), plus
  `git status --porcelain .opencode .claude tools/harness_emit/tests/__snapshots__` → **empty**
- **Phase gate:** full suite at the 1-failed baseline; `ruff check . && ruff format --check .`;
  `/lint` green on an empty agreements dir

### Wave 0 Gaps

**None.** pytest 8.4.2 is installed, `tools/harness_lint/tests/conftest.py` and
`tools/memory_regen/tests/conftest.py` exist, and `tmp_agreements_tree`
(`memory_regen/tests/conftest.py:91-145`) is a ready-made 5-file corpus (active ×2, retired ×1,
`_TEMPLATE.md`, `README.md`, created in non-alphabetical order).

**Wave-1 infra note (not a gap):** if `tools/agree/` is a new member, it needs
`tools/agree/tests/conftest.py` with the sys.path shim — clone `memory_regen/tests/conftest.py:26-33`
verbatim.

**⚠ Fixture-reuse note:** `tmp_agreements_tree` is defined in `tools/memory_regen/tests/conftest.py`
and is **not visible** to `tools/harness_lint/tests/` (pytest conftest scope is directory-based, and
these are sibling trees). The harness_lint tests must define their own — either a local copy in
`tools/harness_lint/tests/conftest.py` or, better, **promote the corpus builder into
`tools/harness_lint/agreements.py`'s test support and have `memory_regen`'s conftest call it**, so
the D-05 parity test compares both consumers against **one** corpus rather than two that can drift.
The second option is more work but is the same "single rule, reused" principle D-05 is enforcing.

## Security Domain

`security_enforcement` is not disabled — section included.

### Applicable ASVS Categories

| Category | Applies | Standard Control |
|----------|---------|-----------------|
| V2 Authentication | no | No auth surface (local CLI) |
| V3 Session Management | no | — |
| V4 Access Control | **partial** | `contract_guard` gates `docs/adr/` for D-12's errata (ADR-0007). `/agree` deliberately has **no** token gate (D-08). |
| **V5 Input Validation** | **yes** | `parse_frontmatter` safe loader (`frontmatter.py:9, 60-61` — no arbitrary object construction). `--because` is **data**, written into a quoted YAML scalar — never `eval`'d, never shell-interpolated. `$ARGUMENTS` passed **positionally** (`golden-approve.md:16-19`). |
| V6 Cryptography | no | **D-01: no crypto, no signatures, no attestation** — theater against this threat model. |
| **V12 File & Resources** | **yes** | D-06 confinement: sorted non-recursive glob, `is_symlink()` skip, `resolve().relative_to(base)`. `/agree`'s **write** path needs the same confinement — a slug of `../../../contracts/x` must be refused. |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Agent self-invents an agreement → priority-0 self-instruction (**T-13-01**) | Elevation of Privilege | **Partial by design (D-03).** `--because` makes omission impossible; forging requires deliberately fabricating a user quote — visible in the git diff. **Shape, not truth.** |
| Malformed/absent stamp slips in silently | Repudiation | The lint fails loud; CI `core-suite` is non-bypassable |
| Path traversal via `--because` or `<slug>` | Tampering | Confine the **write** path (D-06); reject slugs containing `/`, `..`, or a leading `_` |
| YAML injection via `--because` (a `"` or newline closing the scalar) | Tampering | **⚠ Not covered by any decision.** A `--because` containing a double-quote or newline could break out of the quoted scalar and forge sibling frontmatter keys. **The writer must emit YAML via a serializer or escape the value — never f-string it into the template.** Then assert round-trip: a `--because` with `"` and `\n` must parse back to the exact input string. **Add this test.** |
| Credentials pasted into `--because` → committed + injected every session | Information Disclosure | `.memory/agreements/README.md:13` states the no-secrets rule. **Out of scope for D-01's regex** — the `/agree` command doc should restate the warning; the lint does not scan for credential shapes. (Note: `secret_scan` PreToolUse would catch a shape-matching value on the Write path — see the authoring note at the top of this file.) |
| Retired entry never re-linted | Repudiation | **Open Question 1** — do not bundle L5 into the shared predicate |
| Agent self-enables `HARNESS_DEV_BYPASS` | Elevation of Privilege | **Accepted** — ADR-0007:82 names it explicitly; CODEOWNERS at merge is the real gate |

### Q8 — ADR-0006 Errata Mechanics (D-12) — ANSWERED

**The false claim, verbatim** — `docs/adr/0006-*.md:92-93`, inside `### Consequences`:

```
- **Neutral / accepted:** the tier ships as a **scaffold** — `_TEMPLATE.md` + README + one committed
  seed — with no write tooling until Phase 14; humans add agreements by hand in the interim.
```

*(Note: it does not grep as `"committed seed"` — the phrase wraps across lines 92→93.)*
`git ls-files .memory/agreements/` → `README.md`, `_TEMPLATE.md`. **No seed. Confirmed.** `[VERIFIED]`

**Why an errata is append-only-legal:** the claim sits in `### Consequences`, **not** in
`## Decision Outcome`. `docs/adr/README.md:14` forbids editing *decision content*;
`docs/adr/README.md:13` explicitly permits *"Fixing typos/links"*. An appended, dated `## Errata`
section after `## Links` (the file is 110 lines) touches **zero decision words**. `[VERIFIED]`

**How `HARNESS_DEV_BYPASS` is set and honored:**

| Step | Fact |
|------|------|
| Storage | `.claude/settings.local.json` — gitignored (`.gitignore:26-27`: *"Local-only settings (never commit — may hold GOLDEN_APPROVE_HUMAN ratification token)"*). **ABSENT in this checkout — confirmed by `ls`.** |
| Mechanism | Plain **env var**. `_stdin.py:39` `DEV_BYPASS_ENV = "HARNESS_DEV_BYPASS"`; `_stdin.py:42-44` `dev_bypassed()` → `bool((os.environ.get(...) or "").strip())`. It reaches the hook via the settings file's `env` block **or any exported shell var** — nothing requires the JSON file. |
| Consumer | `contract_guard.py:104` — `approved = token_present or dev_bypassed()` |
| Registration | `.claude/settings.json:125` — `"command": "uv run python -m tools.hooks.contract_guard"` under `PreToolUse` `[VERIFIED]` |
| Deny path | `contract_guard.py:73-81` — `docs/adr/**` ∈ `CONSTITUTION_GLOBS` (line 43) → `resolve_path(...) == "deny"` → deny naming `/golden-approve` + CODEOWNERS |
| Bypass path | `contract_guard.py:108-117` — allowed, **plus a stderr note that never claims human approval**: *"allowed via HARNESS_DEV_BYPASS (dev-only) — CODEOWNERS still gates merge"* |

**Does byte-hygiene still apply on the bypass path? — YES. Verified by reading `decide()`.**

`contract_guard.py:60-92` runs the checks in this order: (1) off-plane → `None` (line 73-74);
(2) on-plane + not approved → deny (76-81); (3) **on-plane + approved → `lint_bytes(content.encode("utf-8"))`
→ deny on any violation (83-90)**; (4) clean → `None`. Since `approved` is
`token_present or dev_bypassed()` (104), **step 3 runs identically on the dev-bypass path.** The
docstring is explicit (11-14): *"even an APPROVED constitution write is DENIED if its payload bytes
fail the reused POLY-01 `lint_bytes` (§4.3-4.6: BOM / CRLF)."* ADR-0007's design spec agrees:
byte-hygiene **never** waived. `[VERIFIED — read the code, not the prose]`

**⇒ The errata text must be LF-only with no BOM.** A CRLF paste is denied even with the bypass set.

**Two viable landing paths:**

1. **Dev-bypass (sanctioned):** set `HARNESS_DEV_BYPASS=1` (export, or an `env` block in
   `.claude/settings.local.json` — the file must be **created**; it is absent), then Write/Edit
   normally. Produces the audit stderr note. **Preferred.**
2. **Raw shell (honest caveat):** the hook matcher is `Write|Edit` — a Bash `cat >>` **never reaches
   `contract_guard` at all**, so it also skips the byte-hygiene check. If used, run
   `uv run python -m tools.polyglot_lint.lint` on the file manually, or just be certain the append is
   LF-only. **Path 1 is preferred precisely because it keeps the byte check.**

**Never forge `GOLDEN_APPROVE_HUMAN`** (`approve.py:9`, `contract_guard.py:7`, ADR-0007:55). The
whole point of `HARNESS_DEV_BYPASS` being a *distinct* variable is that a dev-bypassed write is never
mislabeled human-ratified.

**CODEOWNERS is unaffected:** `/docs/adr/ @hjung3113` (CODEOWNERS) still gates merge. The file's own
header notes CODEOWNERS is advisory unless branch protection is enabled — a pre-existing,
out-of-scope repo setting, not this phase's problem.

**D-13 — the errata must say the empty set is CORRECT.** Suggested content (LF-only):

```markdown
## Errata

**2026-07-16** — The "Neutral / accepted" bullet under *Consequences* states the tier ships with
"`_TEMPLATE.md` + README + one committed seed". **There is no seed and there never was**:
`git ls-files .memory/agreements/` returns exactly `README.md` and `_TEMPLATE.md`, and the only
add-commit for the directory (`96b8db2`) added exactly those two files.

**The empty active agreement set is CORRECT, not a defect to repair.** An agreement is written only
in response to explicit user feedback (MEM2-04, proposal §2 property 2); no such feedback has been
recorded, so there is nothing to record. **An agent that "fixes" this by authoring an agreement would
self-invent user feedback — the exact T-13-01 threat this ADR's channel and the Phase-14 provenance
guard exist to prevent.** Do not seed this directory.

No decision recorded in this ADR is changed by this note; it corrects a factual claim about what
shipped (append-only, `docs/adr/README.md`).
```

## Project Constraints (from CLAUDE.md / AGENTS.md)

| Directive | Bearing on Phase 14 |
|-----------|---------------------|
| **Contract-first** — contracts/ is the single source; code that differs is wrong | `.memory/agreements/README.md` + `_TEMPLATE.md` are the tier's contract. D-01's regex mirrors `_TEMPLATE.md` **exactly and nothing more**. |
| **Derived plane is never hand-edited; decisions are append-only ADRs** | Agreements are **NOT derived** (README:3-5) — this kills both the `memory_regen` home (Q5) and SC2's regenerate→verify pattern. D-12's errata is the append-only-compliant instrument. |
| **No model identifier in repo artifacts** | No model id in commits, PR bodies, code comments, `agree.md`, or the errata. |
| **Template ≠ instance; core depends on NO instance (GEN-04)** | `tools/` + `harness/` are core. Nothing this phase adds may reference `examples/`. `test_core_no_example_dep.py` is the live guard. |
| **`uv` only** — never pip/poetry/pyenv | `uv run pytest`, `uv run python -m …`. |
| **ruff, line-length 100, target py311, `select = ["E","F","I","UP","B"]`** | `pyproject.toml:43-49`. `from __future__ import annotations` at the top of every new module (every existing tools module does). |
| **`/lint` is a thin macro; adds no new rules** | `lint.md:14`. The provenance step calls the module; the rules live in `provenance.py`. |
| **GSD workflow enforcement** | Phase 14 work runs through `/gsd:execute-phase`, not ad-hoc edits. |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `tools/agree/` (new zero-dep member) is a better home than `tools/harness_lint/agree.py` | Q5 | Low — a judgement call inside D-13's "Claude's Discretion". Lock cost measured; both work. |
| A2 | The lint should check **retired** entries too (L5 excluded from the shared helper) | Q1/OQ-1 | **Medium — the one open decision.** Wrong ⇒ either retired entries are permanently unlinted, or pre-`/agree` hand-authored entries must be retro-stamped. Both defensible; see OQ-1. |
| A3 | `--because` needs YAML-escaping (quotes/newlines) | Security | Low if handled, **Medium if skipped** — an unescaped `"` forges sibling frontmatter keys. Cheap to test; just do it. |
| A4 | Promoting the fixture corpus to a shared builder beats duplicating it per conftest | Validation | Low — a duplicated fixture works; it just reintroduces the drift D-05 is eliminating. |

## Open Questions

1. **Does the provenance lint check `status: retired` entries?** ⚠ **The one design decision the
   planner must make.**
   - **What we know:** D-05 says share the "3-layer fail-closed exclusion … of non-`active` status",
     which reads as *the lint inherits L5*. D-09 says retired entries live **forever** as the audit
     trail. The code (`inject.py:105`) genuinely bundles status into the same loop.
   - **What's unclear:** if the lint inherits L5, **every retired entry is permanently unlinted** —
     an agent could retire an entry and its forged stamp becomes unauditable, and D-01's
     `status ∈ {active, retired}` check could never fire on a `status: pending` typo (a non-active
     status is skipped before it can be flagged). That last point is self-defeating: **D-01's own
     status rule is unenforceable if the lint inherits D-05's status filter.**
   - **Recommendation:** **share L1-L4 only; the lint checks every agreement file.** This satisfies
     D-05's actual intent ("the lint and the injector must not disagree about what an agreement
     *is*" — a *file-selection* concern) while making D-01's status rule enforceable. Cost: any
     hand-authored entry ever added without a stamp fails the lint — **currently zero such files
     exist** (`git ls-files` → README + `_TEMPLATE` only), so the cost is exactly zero today.
   - **Ship the parity test either way** — it turns the D-05 invariant into an assertion.

2. **Does `/agree` write the `added:` date itself?**
   - **What we know:** `_TEMPLATE.md:3` has `added:`; D-01 requires ISO `YYYY-MM-DD`. The
     no-wall-clock rule (Q6/MEM2-05) is scoped to **`assemble()` and the hook wrappers**
     (`test_inject_determinism.py:70-87` reads only `inject.py`, `memory-inject.sh`,
     `session-inject.ts`) — **not** to `tools/agree/`.
   - **What's unclear:** a `date.today()` in the writer is *not* forbidden by any live gate, but it
     would make `/agree`'s output non-reproducible in tests.
   - **Recommendation:** `--added` **optional**, defaulting to today's ISO date in `main()` **only**
     — never inside the pure `add()` function, which takes `added: str`. This mirrors `assemble()`'s
     discipline (clock at the edge, never in the pure core) and makes `add()` deterministically
     testable. **Do not** widen the wall-clock gate over `tools/agree/`.

3. **How is SC2's "follows the `stale-derived` gate pattern" satisfied?**
   - **What we know:** it is a category error (see *State of the Art* #3) — a human-authored tier
     cannot be regenerate→verified. D-04 mandates the correct pattern.
   - **Recommendation:** the plan should state explicitly that **D-04 supersedes SC2's pattern
     clause** (CONTEXT decisions are locked and post-date the ROADMAP), and that SC2's *substance*
     ("fails when an agreement file lacks a well-formed provenance/origin stamp") is fully satisfied.
     Flag it for `/gsd:verify-work` so the phase is not failed against a mis-worded criterion.

## Sources

### Primary (HIGH confidence — read in full or executed this session)
- `tools/memory_regen/inject.py` (173 lines, in full) — the predicate at 90-115; the
  `harness_lint` import at :15; the `contract_drift` import at :14
- `tools/memory_regen/tests/test_inject_determinism.py`, `test_inject_assembler.py`,
  `conftest.py` — the four invariants + the `tmp_agreements_tree` corpus
- `tools/polyglot_lint/lint.py` (147 lines, in full) — the D-04 shape
- `tools/golden_runner/approve.py` (103 lines, in full) — the D-07 shape
- `tools/harness_lint/{__init__.py, frontmatter.py, pyproject.toml}` — PEP-562 lazy re-export; the
  parser; the no-pyyaml/no-lock-mutation constraints
- `tools/harness_lint/tests/{test_commands.py, test_core_no_workspace_member_dep.py,
  test_ci_stale_derived.py}` — the glob-driven command lint (D-11); the GEN-04 twin; the
  stale-derived pattern
- `tools/hooks/{contract_guard.py, _stdin.py, secret_scan.py}` — `dev_bypassed()`; the
  byte-hygiene-still-applies finding; the shape-anchored content patterns
- `pyproject.toml`, `uv.lock`, `CODEOWNERS`, `.gitignore` — workspace glob, member entries, gates
- `docs/adr/{0006-*.md:92-93, 0007-*.md, README.md:10-25}` — the phantom seed; the bypass; append-only
- `.memory/agreements/{README.md, _TEMPLATE.md}` — the tier contract; the D-02 shape
- `harness/commands/{lint.md, golden-approve.md}` — the two authoring precedents
- **Executed:** `uv run python -c "…parse_frontmatter…"` → the three-way quoting result (Q6)
- **Executed:** `uv run pytest tools/harness_emit tools/memory_regen tools/harness_lint -q` →
  **1 failed / 359 passed** (baseline confirmed)
- **Executed:** `git ls-files .memory/agreements/` → 2 files (the D-12 seed falsification)
- **Executed:** `ls harness/commands/*.md | wc -l` → **19** (the D-10 count)
- **Executed:** `grep -rn "uv.lock" tools/ .github/` → zero assertions (Q5's lock-guard finding)

### Secondary (MEDIUM)
- `.planning/phases/14-.../14-CONTEXT.md` D-01..D-13 — locked upstream input
- `.planning/{REQUIREMENTS.md:24, ROADMAP.md § Phase 14, STATE.md:200}` — the requirement, the SCs,
  the carry-forward
- `docs/superpowers/specs/2026-07-14-contract-guard-dev-bypass-design.md` — the bypass design

### Tertiary (LOW)
- None. **Zero WebSearch was performed — this phase adds no external technology.** Every claim above
  is grounded in a file in this repo or a command run in this session.

## Metadata

**Confidence breakdown:**
- **Standard stack:** HIGH — no new packages; every version read from `pyproject.toml`/`uv.lock`
- **Q1 (shared predicate):** HIGH — file:line for the predicate and each of the four invariants;
  the wall-clock trap verified by reading the gate's source
- **Q2 (import direction):** HIGH — the safe edge already exists at `inject.py:15`; both GEN-04
  guards read in full
- **Q3/Q4 (shapes):** HIGH — both modules read in full
- **Q5 (member cost):** HIGH on the measurements (glob membership, 4-line lock diff, zero guard
  tests); the recommendation itself is `[ASSUMED]` (A1)
- **Q6 (quoting):** HIGH — verified by executing the parser; **CONTEXT's stated mechanism corrected**
- **Q7 (validation):** HIGH on infrastructure and baseline; the retired-entry scope is OQ-1
- **Q8 (errata):** HIGH — `decide()`'s control flow read line-by-line; `settings.local.json`
  absence confirmed by `ls`
- **Pitfalls:** HIGH — each traced to a live test or a Phase-13 post-mortem finding

**Research date:** 2026-07-16
**Valid until:** ~2026-08-15 (30 days — findings are repo-internal and stable; only a Phase-15
re-emit or an `inject.py` edit would invalidate them)
