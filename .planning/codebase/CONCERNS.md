# Codebase Concerns

**Analysis Date:** 2026-07-14

**Scope:** `tools/**`, `harness/**`, `libs/**`, `contracts/**`, `.github/workflows/ci.yml`.
`examples/**` and generated `.opencode/**`/`.claude/**` are out of scope (reference instance /
byte-verified emit output — review `harness/**` source instead). `harness/plugins/*.ts` (TypeScript
opencode plugins: `secret-scan.ts`, `polyglot-lint.ts`, `format-on-write.ts`, `contract-guard.ts`,
`session-inject.ts`) are in-scope by path but this pass was Python-centric — they were located and
their role confirmed (they shell out to the same `tools.*` Python modules per their docstrings) but
not line-audited. Flag as a follow-up audit lane.

This document is a **leads list** for the planned full-harness audit — favor coverage over
certainty. Every finding is marked with a confidence/severity tag; items marked **VERIFY** need a
runtime probe (real Claude Code hook payload, live CI run, etc.) that a read-only pass cannot do.

**Known carried blockers (context, not new findings — do not re-open as new leads):**
- BOOT-01 — `.NET 10` SDK install is egress-denied in the dev sandbox (`tools/bootstrap/install.sh`
  fetches `https://dot.net/v1/dotnet-install.sh`); dotnet-gated code paths (golden-parity, `.cs`
  format-on-write) run SKIP-mode locally and only execute for real in CI (`golden` job installs the
  SDK via `actions/setup-dotnet`).
- Commit signing key is a 0-byte placeholder — commits show `Unverified`.
- DEF-05-02-1 — `tools/hooks/tests/test_commit_gate.py` drift-approval tests leak the
  `GOLDEN_APPROVE_HUMAN` token across tests (missing `monkeypatch.delenv`); a fixture at
  `tools/hooks/tests/test_commit_gate.py:36` already does this for SOME tests but not uniformly —
  worth a grep-for-missing-delenv sweep in the audit, not re-derivation here.

---

## Dead Code Candidates

### 1. R3-decimal / R5-datetime polyglot rules are implemented, unit-tested, and never wired live — HIGH confidence, HIGH severity

`tools/polyglot_lint/lint.py:44,92-102` (`lint_tsv(text, kinds=...)`) implements the §4.6/§4.4
per-cell canonicality checks, but **every production call site omits `kinds`**, so `rule = None` at
`lint.py:96` and the R3/R5 branch never fires outside unit tests:

- `tools/hooks/contract_guard.py:71` calls `lint_bytes(content...)` only (byte-level R1/R2) — never
  `lint_file`, so R3/R5 never apply to constitution-plane writes (by design, per docstring — not a
  bug on its own).
- `tools/hooks/commit_gate.py:181` — `for v in lint_file(path):` — no `kinds` argument. Only
  R1/R2/R6/R7 run at commit time.
- `harness/commands/lint.md:37` — the `/lint` macro's polyglot step invokes
  `python -m tools.polyglot_lint.lint "$f"` per tracked `*.tsv` with no `--kinds` flag.

Net effect: the harness ships a rule engine capable of catching non-canonical decimal locale
(`1,5` vs `1.5`) and non-UTC/non-ISO datetimes in wire TSVs, but **no shipped caller ever supplies
the per-column `kinds` needed to activate it** — R3/R5 are exercised only by
`tools/polyglot_lint/tests/test_lint.py:42-54`. There is no `contracts/`-derived source of
per-column kinds threaded into any of the three call sites. Verify: confirm no other in-repo or
`examples/log-parser` caller supplies `kinds` (out of scope for this pass, but the wiring gap is
real within `tools/`+`harness/`).

### 2. `golden_runner.baseline_path` alias is unreferenced — MEDIUM confidence, LOW severity

`tools/golden_runner/runner.py:70`: `baseline_path = verified_path` — a module-level alias with a
docstring justifying it ("the alias reads naturally in both contexts"). Grep across `tools/**` and
`harness/**` finds zero call sites besides its own definition — no test, no hook, no CLI imports
`golden_runner.baseline_path`. Candidate for removal or an explicit `__all__`/test proving intent.

### 3. `argv` parameters parsed but never consulted (reserved-for-future dead params) — HIGH confidence, LOW severity

- `tools/memory_regen/inject.py:140` — `main(argv)`: `argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)`. No flags are ever read; the CLI ignores all arguments.
- `tools/memory_regen/repo_map.py:204` — identical pattern, same `noqa` marker.

Both are self-documented as intentional placeholders, but they are effectively dead code paths
today (any argv passed is silently discarded) — worth confirming they're still on the roadmap or
removing the unused parameter.

### 4. `tools/contract_hash` has no dedicated test directory — coverage gap flagged separately below (see Hardening & Coverage Gaps #1), listed here too because `schema_hash`/`write_manifest`/`main --write` have no direct caller inside the test tree, only indirect exercise via `contract_drift`/`memory_regen` tests.

### 5. `harness/plugins/*.ts` — NOT dead, but unverified reachability — LOW confidence, VERIFY

`tools/harness_emit/generate.py:172` (`iter_plugins`) walks `harness/plugins/` and projects into
`.opencode/`; opencode is `harness_emit`'s primary target but the repo's *active* dev runtime is
Claude Code (per `CLAUDE.md`: "dev = Claude Code, deploy = opencode"). Whether the TS plugins are
ever actually loaded/executed by an opencode runtime in this repo's current lifecycle is unverified
from a static read — flag as a reachability check for the audit, not a dead-code claim.

---

## Correctness & Edge-Cases

### 1. Constitution/secret PreToolUse gates match against REPO-RELATIVE globs but Claude Code hook `file_path` may be ABSOLUTE — HIGH confidence, CRITICAL severity, **VERIFY at runtime**

`tools/harness_perms/resolver.py:47-49` (`resolve_path`) does a plain `fnmatchcase(path, glob)`
against globs like `"contracts/**"`, `"docs/adr/**"`, `"golden/**"`, `"*.env"`, `"**/*.env"`
(`harness/permission-matrix.json`, `tools/hooks/contract_guard.py:42`,
`tools/hooks/secret_scan.py:37`). These globs assume `path` is **repo-root-relative**.

Every consumer — `tools/hooks/contract_guard.py:decide()`, `tools/hooks/secret_scan.py:decide()` —
feeds `resolve_path` the raw `event.file_path` parsed straight from Claude's hook stdin
(`tools/hooks/_stdin.py:parse_event`, `tool_input.file_path`) with **no normalization step**. The
parsed `Event` dataclass carries a `cwd` field (`tools/hooks/_stdin.py:46`) that is **never read**
by either gate (`grep` across `tools/hooks/*.py` for `event.cwd`/`.cwd` finds only test-file
references, never production code) — there is no `os.path.relpath(file_path, cwd_or_repo_root)`
call anywhere in the gate decision path.

Claude Code's documented PreToolUse `tool_input.file_path` for Write/Edit is conventionally an
**absolute path**. If that holds here, `fnmatchcase("/home/.../contracts/x.schema.json",
"contracts/**")` never matches — `contract_guard` and `secret_scan` would **silently never deny a
real write**, because `on_plane` / the path-deny branch is always `False` for a real session, and
only the byte-hygiene branch (`lint_bytes` on approved constitution writes) or the content-pattern
branch (secret regex) would ever fire. This would mean the "CODEOWNERS-gated constitution plane"
and "*.env path deny" access-control halves of both gates are effectively **inert** in production,
despite 100% green unit tests.

Every existing test for these two gates (`tools/hooks/tests/test_contract_guard.py`,
`tools/hooks/tests/test_secret_scan.py`, `tools/harness_perms/tests/test_resolver.py`) constructs
`file_path` as a **fabricated relative string** (`"contracts/x.schema.json"`,
`"config/prod.env"`) — none exercises an absolute path, so the test suite cannot currently detect
this gap either way. **This is the single highest-value item for the audit to verify**: capture one
real Claude Code PreToolUse Write/Edit payload in this environment and inspect the literal
`tool_input.file_path` string.

### 2. `normalize_tsv` does NOT apply cell-level decimal/datetime canonicalization — MEDIUM confidence, MEDIUM severity

`libs/python/normalize/core.py:78-88` (`normalize_tsv`) only strips BOM (R1), folds CRLF→LF (R2),
and ordinal-sorts whole lines (R8). It never splits rows into cells and never calls
`normalize_cell` — decimal-locale (R3) and datetime-format (R5) differences between two TSV blobs
are **not neutralized** by this function. This is the function `tools/golden_runner/runner.py:135-138`
(`compare()`) uses for BOTH the converter output and the `.verified` baseline before an exact string
equality check. A `.NET` converter emitting `"1.50"` where the Python-generated baseline has
`"1.5"` would legitimately register as a golden **FAIL** through this path even though
`normalize_cell`/`_norm_decimal` — sitting right next to it in the same module — would consider them
equal. Cell-level canonicality is enforced only via the **separate** `polyglot_lint.lint_tsv`
path (see Dead Code #1), which is not wired into golden comparison at all. Whether this is
intentional (golden fixtures are expected to already be canonical) or a real gap depends on whether
any golden case's `seed.tsv`/`baseline.verified.tsv` pair can legitimately differ only in decimal
representation — **VERIFY** against actual golden fixtures under `golden/` (not read in this pass;
scope was `tools/**` etc., `golden/` fixtures weren't enumerated).

### 3. `float_compare: {mode: tolerance, tolerance: 1e-9}` contract is not implemented anywhere — MEDIUM confidence, MEDIUM severity

`contracts/normalization/format-conventions.schema.json:44-53` declares the harness's own contract
for numeric comparison as **tolerance-aware float compare**. The actual implementation
(`libs/python/normalize/core.py:_norm_decimal` + `golden_runner.compare`'s
`normalized_new == normalized_baseline` string equality) does **exact string comparison** of a
`Decimal`-normalized string — there is no tolerance window applied anywhere in `tools/**` or
`libs/**`. This sidesteps float-repr issues by using `Decimal` instead of `float`, which is
arguably *better* than the contract's stated design, but it means the shipped `float_compare` const
in the schema documents behavior the code does not implement — a genuine contract-vs-code drift the
project's own non-negotiable ("code that disagrees with the contract is wrong") would flag if this
schema were the domain's live contract rather than a seed placeholder (the schema is explicitly
marked `"SEED PLACEHOLDER"` / `"EXAMPLE placeholders (A4)"`, so severity is capped at MEDIUM).

### 4. `_norm_datetime` silently truncates sub-second precision — MEDIUM confidence, MEDIUM severity

`libs/python/normalize/core.py:40-48`: `dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")` has no
`%f` — fractional seconds are dropped unconditionally. Two distinct input timestamps that differ
only in milliseconds/microseconds (`2026-07-07T00:00:00.100Z` vs `2026-07-07T00:00:00.900Z`)
normalize to the **same** canonical string and would be treated as equal by both the golden
comparator and `polyglot_lint`'s R5 check. If the eventual domain data ever carries sub-second
timestamps, this is a silent-precision-loss correctness risk (values that should differ compare
equal) rather than a fail-loud rejection. No fixture in `libs/normalize-fixtures/tz_iso8601.json`
exercises a fractional-second input — **untested edge case**.

### 5. `normalize_cell` raises uncaught on an empty decimal/datetime cell that isn't the null token — HIGH confidence, MEDIUM severity

`libs/python/normalize/core.py:51-63`: the null-token check (R6) runs first, but if `value == ""`
and `kind == "decimal"` and `null_token != ""`, execution falls to `_norm_decimal("")` →
`Decimal("".replace(",", "."))` → `Decimal("")` raises `decimal.InvalidOperation` uncaught. Same for
`kind == "datetime"` → `datetime.fromisoformat("")` raises `ValueError` uncaught. The docstring at
`core.py:62` ("string / any other kind: pass through (R6 empty-string stays empty)") implies empty
IS meant to be a legitimate passthrough value generally, but the code only passes empty through for
non-decimal/non-datetime kinds. `libs/normalize-fixtures/null_vs_empty.json` only tests
`"empty-string-stays-empty"` with `"kind": "string"` — **the decimal/datetime-empty-string case is
untested and will crash** any caller that reaches it (`golden_runner.compare` via `normalize_tsv`
doesn't call `normalize_cell` at all — see Correctness #2 — so this is reachable only via
`polyglot_lint.lint_tsv`'s R3/R5 path, which per Dead Code #1 is not wired live; net risk is
currently latent, not live-triggered).

### 6. Breaking-change classifier misses "newly added required property" — HIGH confidence, MEDIUM-HIGH severity

`tools/contract_drift/drift.py:84-110` (`classify`) iterates **only `old_idx.items()`** when
deciding breaking-vs-non-breaking. The `"required"` check at `drift.py:107-109` only fires
`val - nval` (a field required in `old` but no longer required in `new`) — it never checks the
reverse (`nval - val`: a field that is newly required in `new` but was NOT required in `old`).
Adding a brand-new property AND marking it `required` in the same schema edit is a **breaking**
change for any existing instance data (it will fail validation against the new schema), but
`classify()` would return `"non-breaking"` for it, because the new required-field name never
appears as a key in `old_idx` (nothing in `old` ever produced that key) and the loop never inspects
`new_idx`-only entries.
`tools/contract_drift/tests/test_classify.py:36-39` (`test_added_optional_column_is_non_breaking`)
explicitly tests the safe case (added, NOT added to `required`) — there is **no test** for
"added AND required," confirming the gap is both real and untested. This directly undermines the
contract-drift gate's core promise (`tools/contract_drift/drift.py:10-12`,
`tools/hooks/commit_gate.py:9-11` D-05 bypass logic) since an unapproved breaking change could be
silently auto-classified `non-breaking` and, depending on the human-approval UX around
`GOLDEN_APPROVE_HUMAN`, reviewed with the wrong severity signal.

### 7. `_slug()` collision risk in strangler-guard — LOW confidence, LOW severity

`tools/strangler_guard/guard.py:37-44` (`_slug`) collapses non-alphanumerics to a single hyphen:
`src/a.b.c` and `src/a-b-c` (and `src_a_b_c`, `SRC/A/B/C`, etc.) all normalize to the same slug
`src-a-b-c`. Two distinct legacy target paths could resolve to the same derived golden-case
directory, so `require_baseline` could return an unrelated path's captured baseline as if it were
the requested target's equivalence reference — silently defeating the "never fabricates a baseline"
guarantee the module's docstring promises (P10). Low likelihood in a real repo (paths rarely
collide after normalization) but worth a uniqueness check across `golden/*` slugs.

### 8. `_pagerank_python` is a private networkx internal, imported directly — LOW confidence, LOW severity

`tools/memory_regen/repo_map.py:29`: `from networkx.algorithms.link_analysis.pagerank_alg import
_pagerank_python` — an underscore-prefixed (non-public) function, justified in the docstring
(`repo_map.py:134-141`) as avoiding a numpy/scipy dependency the public `nx.pagerank` dispatcher
would pull in on networkx 3.6. Pinned to `networkx==3.6.1` today so it works, but a private API is
not covered by networkx's semver/compat guarantees — a future `networkx` bump (even a patch) could
rename/remove it and silently break `.memory/derived/repo-map.md` regeneration with an
`ImportError`, which is NOT gated by any CI job that would fail loud on session-start injection
(`stale-derived` job only regenerates `docs/reference/**` + `contracts-index.md`, not `repo-map.md`
— worth double-checking `.github/workflows/ci.yml`'s `stale-derived` job scope against this).

---

## Hardening & Coverage Gaps

### 1. `tools/contract_hash` has zero dedicated tests — HIGH confidence, MEDIUM-HIGH severity

`tools/contract_hash/hash.py` (119 lines: `schema_hash`, `build_manifest`, `write_manifest`, `main`)
is the RFC 8785 canonicalize+SHA-256 module that the ENTIRE contract-drift gate is built on
(`tools/contract_drift/drift.py` imports `CONTRACTS_DIR, MANIFEST_PATH, REPO_ROOT, build_manifest`
directly). There is no `tools/contract_hash/tests/` directory (confirmed via directory listing) —
`build_manifest`/`schema_hash` are exercised only indirectly through `contract_drift`'s and
`memory_regen`'s test suites, which construct their own tmp trees and never target
`contract_hash`'s specific behaviors: `schema_hash`'s uncaught `json.JSONDecodeError` on a malformed
`.schema.json`, the symlink-escape defense at `hash.py:56` (`if root != resolved and root not in
resolved.parents: continue`), or `write_manifest`'s `--manifest` targeting a path outside the repo
(`hash.py:105-108` `except ValueError` fallback). Given this module underpins the drift gate that is
the harness's core "contract-first" enforcement mechanism, a direct test file is a meaningful gap.

### 2. Broad `except Exception` degrades the SessionStart drift signal silently — MEDIUM confidence, LOW-MEDIUM severity

`tools/memory_regen/inject.py:56-59` (`_drift_summary`): `except Exception:  # pragma: no cover -
degrade gracefully if the gate is unavailable` wraps the ENTIRE `run_gate()` call, not just an
expected I/O failure. Any bug newly introduced into `tools.contract_drift.drift.run_gate` (e.g. the
classifier bug in Correctness #6, or a future regression) would be swallowed here and rendered to
the user as the bland `"contract-drift: unknown (gate unavailable)"` rather than surfacing the real
exception — reducing the signal quality of the non-ignorable SessionStart injection this module's
own docstring calls "the live safety signal" (`inject.py:116`). Consider narrowing to the specific
exceptions `run_gate` can actually raise (I/O, JSON decode) so a genuine logic bug is not silently
downgraded to "unknown."

### 3. Config loaders (`harness_config`, `workspace_config`) do zero shape validation, and at least one direct consumer indexes without `.get()` — MEDIUM confidence, MEDIUM severity

`tools/harness_config/loader.py` and `tools/workspace_config/loader.py` are explicitly documented as
"Pure I/O + shape: NO enforcement logic (that belongs to the consistency test in
`tools.harness_lint`)" — a deliberate design split. However, the CI matrix-generation step in
`.github/workflows/ci.yml` (`setup` job) consumes `languages()` with **direct bracket access**:
```python
legs = [
    {"id": lang["id"], "test": lang["test"], "test_paths": lang.get("test_paths", [])}
    for lang in languages()
]
```
`lang["id"]` and `lang["test"]` are NOT `.get()`-guarded — a malformed `harness/project.toml`
`[[languages]]` entry missing either key raises `KeyError` inside the CI `setup` job's inline
Python, before the `harness_lint` consistency gate (`test_language_config.py`) has a chance to run
in a separate job. Since `harness_lint`'s consistency test and this CI matrix step are NOT the same
job/ordering-guaranteed step, a config-shape regression could produce a confusing `KeyError`
traceback in CI's `setup` job rather than the loader's own or `harness_lint`'s more actionable
error message. Consider either validating shape in the loader (raising a clear
`HarnessConfigError`) or guaranteeing `harness_lint`'s shape gate runs *before* the CI matrix step
consumes the config.

### 4. `tools/hooks/_stdin.py`'s fail-safe sentinel makes hooks fail-open on malformed input — HIGH confidence, LOW severity (by design, but worth flagging for the audit)

`tools/hooks/_stdin.py:50-59` (`parse_event`): any malformed/empty/non-dict JSON on stdin yields the
safe sentinel `Event()` (all fields `""`). Every gate built on this (`contract_guard`, `secret_scan`,
`commit_gate`) treats an empty `file_path`/`command` as "no decision" — i.e. a **malformed hook
payload always results in ALLOW**, never a fail-closed deny. This is explicitly the documented
design ("a malformed payload must never crash the gate... individual gates choose fail-open vs
fail-closed on top of it" — `_stdin.py:19-24`), and is defensible for availability, but combined
with Correctness Finding #1 (relative-glob mismatch against possibly-absolute paths), the two gaps
compound: if `file_path` normalization is ALSO wrong, there is no secondary fail-closed layer
catching it. Worth the audit explicitly re-affirming fail-open is the intended posture for every one
of these hooks, not just an accepted default.

### 5. `commit_gate.check_golden` iterates ALL discovered golden cases on every commit with no incremental/staged-only filter — LOW confidence, LOW severity (perf, not correctness)

`tools/hooks/commit_gate.py:188-217`: `discover_golden_cases()` returns every `golden/*` subdir
with a `meta.yaml`, and `check_golden()` runs **all** of them on every `git commit` (when dotnet is
present), regardless of whether the commit touches anything golden-relevant. As the `golden/` tree
grows, `commit_gate --from-hook` (bound to the `Bash` PreToolUse matcher, `timeout: 120` in
`.claude/settings.json:145-146`) risks becoming slow enough to hit its own hook timeout, turning a
legitimate commit into a timeout-induced pass-through (need to confirm Claude Code's behavior on
hook timeout — allow or deny — separately). Not a correctness bug today (case count is presumably
small), but a scaling concern worth a note for when golden cases multiply.

### 6. `harness/plugins/*.ts` — no Python-side test coverage confirmed, TS runtime unaudited — LOW confidence, VERIFY

As noted in Dead Code #5, the opencode-native plugin sources (`harness/plugins/secret-scan.ts`,
`polyglot-lint.ts`, `format-on-write.ts`, `contract-guard.ts`, `session-inject.ts`) were located but
not read line-by-line in this pass (scope was Python-heavy given the `tools/**` mandate). If these
TS plugins re-implement (rather than shell out to) the same §4.3-4.6 / permission-resolver logic
already audited above, they are a second, unverified implementation of every finding in this
document and should be a dedicated audit lane — their own docstrings (per the file names) suggest
they mirror the Python hooks 1:1, which would mean Correctness Finding #1 (relative-vs-absolute path
glob mismatch) needs checking against opencode's own hook payload shape too, which may differ from
Claude Code's.

---

*Concerns audit: 2026-07-14*
