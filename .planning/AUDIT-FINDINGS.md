# Full-Harness Audit — Findings Report

**Date:** 2026-07-14
**Scope IN:** `tools/**`, `harness/**`, `libs/**`, `contracts/**`, `.github/workflows/ci.yml`
**Scope OUT:** `examples/**` (reference instance); generated `.opencode/**`·`.claude/**` (byte-verified by emit-drift gate — reviewed `harness/` source)
**Method:** `/gsd:map-codebase` (7 docs) → concerns mapper leads → 3 read-only verification agents + direct verification. Every finding below was confirmed against source; the map's false positives are listed at the end.
**Baseline:** 568 pytest green; contract-drift clean; emit-drift clean.

---

## Meta-finding (the spine)

The two HIGH findings share one root: **the harness's central promises — contract-first runtime enforcement and polyglot golden-equivalence — have wiring gaps that the unit tests do not catch, because the tests exercise the pure functions with idealized inputs (repo-relative paths; pre-canonicalized cells) while the real call paths feed different inputs (absolute paths; raw TSV).** The functions are correct in isolation and green in CI; the integration seam is where they don't fire. This is the highest-leverage thing to fix and to add regression coverage for.

---

## HIGH

### H1 — `contract_guard` constitution-plane deny is a no-op in real Claude sessions
- **Where:** `tools/harness_perms/resolver.py:47-49` (`resolve_path`), `tools/hooks/contract_guard.py:42,60`, wired live at `.claude/settings.json:125`.
- **Defect:** `CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]` are prefix-anchored globs. `resolve_path` matches them with `fnmatchcase(path, glob)`, which requires the whole string to start with `contracts/`. Claude Code's Write/Edit `tool_input.file_path` is **absolute** (`/home/user/lifetimeworkflow/contracts/x.schema.json`), which never matches → `on_plane == False` → the write is **allowed**. The advertised "machines gate" PreToolUse deny silently never fires.
- **Evidence (empirical):** `fnmatchcase('/home/user/lifetimeworkflow/contracts/x.schema.json', 'contracts/**') == False`; the relative form used by every test (`tools/harness_perms/tests/test_resolver.py:60-72`) matches → false green.
- **Blast radius (narrowed):** `secret_scan`'s `*.env` path-deny is **safe** — it also lists `**/*.env`, and fnmatch `*` crosses `/`, so `/home/app/prod.env` → DENY. Only `contract_guard` is affected. CODEOWNERS + the CI drift gate remain as backstops, so the constitution plane is not unguarded end-to-end — but the runtime first line is dead.
- **Severity:** HIGH · **Fix touches constitution:** no (code fix in resolver/hook). The fix pattern already exists in-repo (`secret_scan`'s dual-glob) — either normalize `file_path` to repo-relative before matching, or add `**/`-prefixed globs. Prefer path-normalization so it's robust for both absolute and `./`-relative.
- **Regression test:** feed an absolute `file_path` through `contract_guard.decide` and assert deny.

### H2 — Golden comparator does not apply the cell-level canonicalization the spec/contract mandate
- **Where:** `libs/python/normalize/core.py:78-88` (`normalize_tsv`), `tools/golden_runner/runner.py:135-140` (compare path).
- **Defect:** `normalize_tsv` does only R1 (BOM strip), R2 (LF), R8 (`sorted(lines)`). It never splits cells or calls `normalize_cell`/`_norm_decimal`/`_norm_datetime`. The comparator calls **only** `normalize_tsv` on both sides, then compares with `==`. So the §4.3-4.6 decimal-locale and timezone canonicalizations the spec says "must be neutralized before diff" (`libs/normalize-spec.md:19-22`) are never applied on the compare path. `1,5` vs `1.5`, or `+09:00` vs the UTC form, yields a **false RED** — or masks a real value regression that differs only in representation. `normalize_cell` + R3/R5 helpers are exercised only by corpus-parity tests, dead relative to compare.
- **Severity:** HIGH (it's the project's stated Core Value) — **latent** on the current toy corpus if both producers happen to emit identical representation, but the comparator does not deliver its contract.
- **Fix touches constitution:** **YES, effectively.** Wiring cell canonicalization into the compare path changes what compares equal → can shift golden baselines → the human-gated `/golden-approve` path. **Requires operator sign-off + likely paired golden re-approval + ADR.** Do not self-apply.

---

## MEDIUM

### M1 — declared `tolerance` float compare is wired to nothing
- **Where:** contract `contracts/normalization/format-conventions.schema.json:44-52` declares `float_compare.mode="tolerance"`, `tolerance=1e-9`; `libs/normalize-spec.md:51-54` says it "applies at compare time in the golden runner." `tools/golden_runner/runner.py:140` compares with pure string `==`. No numeric/tolerance compare exists anywhere in `tools/**` / `libs/**`.
- **Severity:** MEDIUM — contract-vs-code drift (contract-first rule: the code is the wrong one). Same compare path as H2. **Fix touches constitution:** no (contract already declares the knob; fix is runner code) — but it, too, changes compare semantics and can shift goldens → bundle with H2 under operator sign-off.

### M2 — `normalize_cell` crashes uncaught on an empty decimal/datetime cell
- **Where:** `libs/python/normalize/core.py:33,45,56-63`.
- **Defect:** `"" != "\N"` so an empty cell skips the null guard; `kind=="decimal"` → `Decimal("")` raises `InvalidOperation`; `kind=="datetime"` → `datetime.fromisoformat("")` raises `ValueError`. Neither caught. The line-62 "empty-string stays empty" comment covers only `string`.
- **Severity:** MEDIUM (latent — not on the compare path today per H2, and fixtures likely type empties as `string`). **Fix touches constitution:** no for the guard; the *semantics* of empty typed cells may warrant a spec note (`normalize-spec.md` R6, human-gated).

### M3 — `contract_drift.classify()` mislabels an added-and-required property as non-breaking
- **Where:** `tools/contract_drift/drift.py:69-70,84-110`.
- **Defect:** `classify` iterates only `old_idx`. For `required` it checks `val - nval` (removals) but never `nval - val` (additions). A newly-added property lives only in `new_idx`, so adding it to `required` only grows the required set (`val - nval == ∅`) → returns `non-breaking`. But existing instances lacking that field now fail validation — a producer-breaking change. No test for this case in `tools/contract_drift/tests/test_classify.py`.
- **Severity:** MEDIUM — the drift gate still **trips** (any hash change = drift → human must rebaseline + pair golden/ADR), so this only *mislabels* severity in the report, potentially inviting a lighter review of a genuinely breaking edit. **Fix touches constitution:** no (fix is `drift.py` + test).

### M4 — constitution-plane hook is fail-open on malformed stdin
- **Where:** `tools/hooks/_stdin.py:50-78` (safe-sentinel `Event()`), `tools/hooks/contract_guard.py:60` (empty `file_path` → no deny → allow).
- **Defect:** intentional and documented (`_stdin.py:19-23`), but a defense-in-depth gap: a malformed or field-omitted payload never reaches the deny branch. Compounds H1 — the constitution-plane guard being fail-open is the higher-risk of the two postures.
- **Severity:** MEDIUM. **Fix:** best resolved by an **ADR-recorded decision** on the fail-open posture (human-gated `docs/adr/`) rather than a silent code flip — the constitution guard may warrant fail-*closed* once H1 is fixed.

---

## LOW / informational

- **L1 — R3/R5 decimal/datetime lint rules never invoked with real `kinds`.** `tools/polyglot_lint/lint.py:44,92-102` gate R3/R5 behind non-empty `kinds`; all three production call sites (`contract_guard.py:71`, `commit_gate.py:181`, `harness/commands/lint.md:37`) pass none → non-canonical decimal/datetime cells pass the commit gate silently. Same root as H2. By-design/latent. LOW.
- **L2 — `_norm_datetime` drops sub-second precision** (`core.py:48`, no `%f`). Contract-conformant (R5 pins second precision); latent masking risk. LOW; widening would be a constitution change.
- **L3 — `tools/contract_hash` has no dedicated test dir.** Load-bearing (RFC 8785 hasher under the whole drift gate) but delegates to `rfc8785.dumps` + `hashlib`; the untested logic is the `.parent`-relative keying + symlink-escape guard (`hash.py:50-59`). LOW-MED — add a direct test.
- **L4 — CI matrix indexes `lang["id"]/["test"]` without `.get()`** (`.github/workflows/ci.yml:53-56`; `loader.py:42-50` is raw passthrough). Malformed `[[languages]]` → KeyError crashes the `setup` job **loud** (fan-in fails), not a silent bypass. LOW — cheap `.get()` + clear error.
- **L5 (informational) — broad `except Exception` in `tools/memory_regen/inject.py:56-59`.** REFUTED as a risk: it degrades only the session-start advisory banner (`# pragma: no cover - degrade gracefully`); the enforcing drift gate runs independently in CI (`ci.yml:132-135`) and cannot be masked by it.

---

## Refuted map leads (false positives — map was appropriately over-inclusive)

- `baseline_path` alias `tools/golden_runner/runner.py:70` — **used** by `examples/log-parser/tests/test_value_regression.py:14,37`.
- "Two argv-ignoring `main()` CLIs" — the derived-plane regenerators (`memory_regen/*`, `harness_emit/generate.py:463`, `docs_sync/generate.py:261`) ignore argv **intentionally** (`# noqa: F841 reserved for future flags`); they take no args. `contract_hash`/`polyglot_lint` DO consume argv via argparse.
- `memory_regen/inject.py` broad except — advisory only (see L5).

---

## Proposed fix batches

**Batch A — pure code + tests, no gate — ✅ DONE (591 pytest green, ruff clean, emit clean):**
- H1 — ✅ `repo_relative()` at the hook-stdin seam normalizes absolute paths before `resolve_path` in both gates + absolute-path regression tests. (`7d71c7e`)
- M3 — ✅ `classify` flags required-set additions (new or promoted-optional) as breaking + 3 tests. (`6b83a72`)
- M2 — ✅ empty decimal/datetime cell short-circuits to `""` (R6) instead of raising + edge-case tests. (`716c24a`)
- L4 — ✅ CI matrix `sys.exit` with a clear message on a missing `id`/`test` + `id` consistency gate. (`0d83745`)
- L3 — ✅ dedicated `tools/contract_hash/tests/` (canonicalization, keying, symlink-escape, write). (`987325c`)

**Batch B — operator-delegated dispositions (2026-07-14):**

- **H2 + M1 → queued as a future PHASE (not a patch).** Investigation refined the finding: the core
  comparator (`normalize_tsv`) is *intentionally* column-agnostic — it cannot canonicalize decimal/
  datetime cells because **per-column kinds live in the instance overlay**
  (`examples/log-parser/contracts/log-specs/standard-log.spec.yaml`), never in the domain-neutral
  core (GEN-04 keeps domain names out of `tools/`·`harness/`·`libs/`). `run_identity_converter`'s
  own docstring says domain canonicalization is "the domain converter's job." So H2 is not a plain
  bug — it is an **architecture decision**: should the golden runner become column-schema-aware
  (consume a per-case column-kind spec so `compare()` applies `normalize_cell` + tolerance), or is
  cell canonicalization definitively the producer's job with the core only neutralizing R1/R2/R8?
  M1 (tolerance) is the one clear *core-contract* promise gap (`format-conventions.schema.json`
  declares `mode="tolerance"`; the spec says "applies at compare time in the golden runner") but it
  rides the same column-kind plumbing. **Recommendation: `/gsd:plan-phase`** — decide core-vs-
  instance ownership, add the column-kind source if chosen, then re-baseline goldens under
  `/golden-approve`. Not prototyped, to avoid front-running the design + golden churn.
- **M4 → decided: KEEP fail-open, recorded as ADR-0004 (draft staged).** Rationale: flipping the
  constitution guard to fail-closed is not *selective* (a malformed payload has no `file_path`), so
  it would deny **every** `Write|Edit` on any malformed stdin — wedging legitimate editing to guard
  a plane that CODEOWNERS + the CI drift gate already ratify authoritatively. H1 already closes the
  realistic exposure (well-formed absolute-path writes). **Promoted (human-authorized) →
  `docs/adr/0004-constitution-hook-fail-open-posture.md`** + README index row. (The contract-guard
  PreToolUse hook correctly *denied* the agent Write to `docs/adr/` — a live validation of H1; the
  promotion was performed as file ops under explicit human authorization, with CODEOWNERS as the
  authoritative ratification at merge.)
- **L2 (sub-second datetime precision) → leave as-is.** Contract-conformant (`normalize-spec.md` R5
  pins second precision); a spec change only if ever revisited. No action.
