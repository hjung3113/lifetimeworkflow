# Phase 1: Constitution + Golden Core - Research

**Researched:** 2026-07-08
**Domain:** Contract-first polyglot safety net (.NET 10 ↔ Python via A-model CLI) — walking skeleton
**Confidence:** HIGH (stack pinned in CLAUDE.md + verified live; loop wiring HIGH; JCS split-of-concerns HIGH; docs/bootstrap MEDIUM-HIGH)

## Summary

Phase 1 closes ONE real equivalence loop end-to-end: seed placeholder contracts → a fixture-grade .NET toy converter → a Python golden-runner that spawns it over the A-model (CLI + exit code), normalizes both sides through a language-neutral canonicalization core, and diffs against an approved `golden/` baseline — plus a contract-drift hash gate and an idempotent .NET 10 + uv bootstrap. Everything else in the harness (agents, memory, hooks, CI, emitter) is later phases; do not build surface here.

The single most important architectural clarification for the planner: **there are TWO different canonicalizers in this phase and they must not be conflated.** (1) The **JCS / RFC 8785 canonicalizer** (CONTRACT-04 drift gate) operates on `.schema.json` *files* and produces a SHA-256 — it is a repo-level tool that needs **only one implementation** (Python `rfc8785` 0.1.4, Trail of Bits). (2) The **TSV normalization comparator** (CONTRACT-02/03 golden equivalence) implements the §4.3–4.6 rules on *tabular data* and needs **two thin implementations** (.NET + Python) cross-validated by a shared fixture corpus. JCS is for JSON contract text; the §4-5 comparator is for TSV output. Mixing them is the most likely planning error.

The second clarification (Pitfall P14): the drift hash catches cross-cutting §4-5 convention changes only if those conventions are **materialized as a hashed schema file**. Author a `format-conventions.schema.json` (encoding/BOM/LF/decimal/TZ/null-token/TSV-escape as explicit fields) and include it in the hashed manifest, so mutating the null token bumps the hash exactly like reordering a column does.

**Primary recommendation:** Build two canonicalizers (one Python-only JCS hasher for contract text; one dual-language §4-5 comparator for TSV) + a Python golden-runner that subprocess-spawns the .NET toy converter, proven by a two-fixture demo (representation-only-diff PASSES, value-regression FAILS). Materialize §4-5 conventions as a hashed schema. Wire an idempotent bootstrap as a new SessionStart hook entry that coexists with GSD's existing hooks.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Contract text canonicalization + SHA-256 (drift gate) | `tools/` repo-level script (Python) | — | Operates on `.schema.json` files, language-neutral; single impl avoids two-hash drift |
| Breaking-vs-non-breaking classification | `tools/` repo-level script (Python) | — | Reads current vs baseline hash manifest; a pure diff-of-schemas decision |
| TSV §4.3–4.6 normalization (golden equivalence) | `libs/dotnet` + `libs/python` (dual thin impl) | shared fixture corpus in `contracts/` | D-04: rule is canonical, each language implements; cross-validated. Reused by Phase-4 linter |
| Toy converter (fixture-grade producer) | `components/` .NET csproj | — | The "new" side of the A-model boundary; proves CLI spawn + exit code |
| Golden-runner orchestration (spawn/capture/normalize/diff) | `tools/golden-runner` (Python) | invokes both `libs/python` core + `.NET` toy | CI + collector already Python; the runner is the harness plumbing, not domain logic |
| `/golden` + `/golden-approve` (Phase-1 minimal) | command/script layer | human CODEOWNERS gate | Machines gate, humans ratify (P9); Phase 1 = minimal executable form |
| Contract seed (YAML spec + JSON Schema companion) | `contracts/` (constitution plane) | — | Human-owned; JSON Schema is the validated/hashed source of truth |
| Toolchain bootstrap (.NET 10 + uv) | SessionStart hook → `tools/bootstrap` | — | Ephemeral container self-heals; idempotent cache-check |
| Docs skeleton (Diátaxis + adr + glossary) | `docs/` (constitution plane) | — | Human-authored; `reference/` generation deferred to Phase 3 (DOCS-03) |

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CONTRACT-01 | Seed parserimprove contracts into `contracts/` as flagged placeholders | Seed source verified at `/workspace/.../monorepo_skeleton/contracts/{log-specs,normalization,reference-data,state}` (4 YAML + golden/README). Copy verbatim, keep `TBD`/`owner: TBD` placeholder markers, add companion `.schema.json` per file. See §"JSON Schema + YAML Companion". |
| CONTRACT-02 | Single shared canonicalizing comparator (UTF-8/BOM, LF, InvariantCulture, float tol, key sort, UTC/ISO-8601) | Language-neutral spec + dual thin impl; .NET (`System.Globalization.CultureInfo.InvariantCulture`, `System.Text.Json`) + Python (`unicodedata`, `decimal`, `codecs`). Shared `(raw,canonical)` fixture corpus. See §"Normalization Comparator". |
| CONTRACT-03 | Golden fixtures + golden-runner, equivalence by normalization not byte-diff | Python golden-runner subprocess-spawns .NET toy converter, normalizes both sides, diffs. Two demo fixtures. See §"Walking-Skeleton Loop". |
| CONTRACT-04 | RFC 8785 canonicalize → SHA-256 drift gate; classify breaking; cover §4-5 | `rfc8785` 0.1.4 (Python, Trail of Bits) [VERIFIED: PyPI + slopcheck OK]. Hash a manifest of ALL `.schema.json` incl. materialized `format-conventions.schema.json` (P14). See §"Drift Gate". |
| BOOT-01 | `dotnet-install.sh --channel 10.0` install | Env has NO dotnet (verified). Idempotent install-dir + cache-check pattern. See §"Bootstrap". |
| BOOT-02 | uv workspace + ruff/pyright/pytest skeleton | uv 0.8.17 present (bump to 0.11.x). Root `pyproject.toml` workspace + `libs/python` + `tools/*` members. See §"Bootstrap". |
| BOOT-03 | Wire bootstrap into SessionStart | Add a NEW hook entry to `.claude/settings.json` SessionStart array; coexists with GSD's 2 existing entries. See §"Bootstrap / SessionStart". |
| DOCS-01 | Diátaxis tree + glossary | 4 dirs (tutorials/how-to/reference/explanation) + `glossary.md`. Seed from parserimprove `docs/` (00-04 + GLOSSARY). See §"Docs Skeleton". |
| DOCS-02 | `docs/adr/` MADR structure | MADR 4.x template, `adr/0001` records the walking-skeleton architecture. See §"Docs Skeleton". |
</phase_requirements>

## Standard Stack

All core versions are already pinned in CLAUDE.md and `.planning/research/STACK.md` — do NOT re-litigate. Verified live this session where relevant.

### Core (this phase)
| Library | Version | Purpose | Provenance |
|---------|---------|---------|-----------|
| **.NET SDK** | 10.0.100 (channel `10.0`) | Toy converter + (later) tests | [CITED: CLAUDE.md] — env has none; install via `dotnet-install.sh` |
| **uv** | 0.11.x (env has 0.8.17) | Python workspace/deps | [VERIFIED: env `uv --version` = 0.8.17; bump needed] |
| **rfc8785** (Python) | 0.1.4 | RFC 8785 JCS canonicalization for drift hash | [VERIFIED: PyPI + slopcheck OK] Trail of Bits `github.com/trailofbits/rfc8785.py` |
| **jsonschema** (Python) | 4.26.0 | Validate YAML/JSON instances vs Draft 2020-12 | [VERIFIED: PyPI + slopcheck OK, installed 4.26.0] |
| **check-jsonschema** | 0.37.4 | CLI/pre-commit schema validation | [VERIFIED: PyPI + slopcheck OK, installed 0.37.4] |
| **JsonSchema.Net** | 9.2.2 | .NET-side schema validation (Draft 2020-12) | [VERIFIED: NuGet, author Greg Dennis, System.Text.Json] |

### Supporting (test/quality — may be minimal in Phase 1)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **pytest** | 8.4.x pinned (env resolves 9.1.1) | Python test runner for golden-runner + comparator fixtures | See version note below |
| **syrupy** | 5.2.0 pinned (latest 5.5.1) | Snapshot testing (Python golden analogue) | Optional in P1; golden-runner does its own normalized diff |
| **ruff** | 0.15.x (installed 0.15.20) | Lint+format | [VERIFIED: PyPI + slopcheck OK] |
| **pyright** | 1.1.409 pinned (installed 1.1.411) | Type check | [VERIFIED: PyPI + slopcheck OK] |
| **xunit.v3** | 3.2.2 | .NET tests (toy converter can defer heavy tests) | [CITED: CLAUDE.md] |
| **Verify.XunitV3** | 31.20.0 | .NET snapshot/golden | [CITED: CLAUDE.md] — optional P1 |

### Version reconciliation notes (flag for planner)
- **pytest**: CLAUDE.md/STACK.md pin `>=8.4,<9` deliberately (syrupy 5.2.0 compat unverified against pytest 9). The live env resolved **9.1.1**. `[ASSUMED]` that pinning 8.4.x is still desired — plan should pin explicitly in `pyproject.toml` to avoid drift, OR bump the pin to 9.x after a green syrupy run. **Decision for discuss/planner.**
- **pyright 1.1.411 vs pinned .409** and **ruff 0.15.20 vs "0.15.x"** and **syrupy 5.5.1 vs 5.2.0**: all forward-compatible patch/minor bumps; pin the CLAUDE.md values in `pyproject.toml` for reproducibility, treat newer as acceptable. Low risk.

**Installation (Python side, in uv workspace):**
```bash
uv self update                                   # 0.8.17 -> 0.11.x
uv add rfc8785 jsonschema                        # runtime: hasher + validator
uv add --dev pytest syrupy ruff pyright check-jsonschema
```
**Installation (.NET side, from bootstrap hook):**
```bash
curl -sSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh
bash /tmp/dotnet-install.sh --channel 10.0 --install-dir "$HOME/.dotnet"
# toy converter csproj references (tests optional in P1):
#   <PackageReference Include="JsonSchema.Net" Version="9.2.2" />
```

## Package Legitimacy Audit

Ran slopcheck 0.6.1 this session. All packages that this phase newly introduces or installs verified `[OK]`.

| Package | Registry | Age | Downloads | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-----------|-------------|-----------|-------------|
| rfc8785 | PyPI | ~1.5 yr (0.1.4) | moderate | github.com/trailofbits/rfc8785.py | [OK] | Approved (NEW this phase) |
| jsonschema | PyPI | 10+ yr | ~200M/mo | github.com/python-jsonschema/jsonschema | [OK] | Approved |
| check-jsonschema | PyPI | multi-yr | high | github.com/python-jsonschema/check-jsonschema | [OK] | Approved |
| ruff | PyPI | multi-yr | very high | github.com/astral-sh/ruff | [OK] | Approved |
| pyright | PyPI | multi-yr | very high | github.com/microsoft/pyright | [OK] | Approved |
| pytest | PyPI | 10+ yr | very high | github.com/pytest-dev/pytest | [OK] | Approved |
| JsonSchema.Net | NuGet | multi-yr | high | github.com/json-everything/json-everything | (NuGet verified: author Greg Dennis, STJ-based) | Approved |
| jsoncanonicalizer (.NET) | NuGet | 1.0.0 | low | metadata generic ("Package Description", author=id) | not scanned | **REJECTED — do not use** |

**Packages removed / rejected:** `jsoncanonicalizer` (NuGet 1.0.0) — generic placeholder metadata (author == package id, description == "Package Description") is a slop/low-trust signal. **Not needed anyway** (see Drift Gate: JCS is Python-only). The canonical .NET JCS lib is Anders Rundgren's WebPKI `JsonCanonicalizer`, but Phase 1 requires **no .NET-side JCS at all**.
**Packages flagged [SUS]:** none.
**Note:** slopcheck's `install` subcommand runs `pip install` after the check; the check output for every scanned package was `[OK]`. `--json` flag is not supported in slopcheck 0.6.1 (used plain output).

## Architecture Patterns

### System Architecture Diagram — the one walking-skeleton loop

```
  contracts/                              tools/ (repo-level, Python)
  ├─ log-specs/standard-log.spec.yaml ───┐
  ├─ .../*.schema.json  (hashed SoT)      │      ┌─────────────────────────────┐
  └─ normalization/format-conventions ────┼─────▶│ contract-hash (rfc8785→JCS→ │
     .schema.json  (§4-5 materialized)    │      │ SHA-256 per file → manifest)│
                                          │      └──────────────┬──────────────┘
                                          │                     ▼
                                          │      ┌─────────────────────────────┐
                                          │      │ contract-drift (manifest vs  │
                                          │      │ .hashes baseline → breaking /│──▶ gate PASS/FAIL
                                          │      │ non-breaking classification) │
                                          │      └─────────────────────────────┘
                                          │
  golden/<case>/                          │   tools/golden-runner (Python)
  ├─ input/seed.tsv ──────────────────────┼──▶ 1. read job, spawn:
  ├─ expected/baseline.tsv  ("legacy")    │        subprocess([dotnet toyconv, --in seed.tsv])   ★ A-MODEL
  └─ meta.yaml (allowed diffs)            │      2. capture stdout + exit code
                                          │      3. normalize BOTH sides via ──┐
  components/toy-converter/ (.NET 10) ◀───┘         libs/python §4-5 core       │
   reads seed TSV → emits normalized TSV                                        ▼
   (fixture-grade; NO real parse logic)              4. diff(normalized_new, normalized_baseline)
                                                        ├─ equal  → PASS  (repr-only fixture)
  libs/{dotnet,python}/normalize/                       └─ differ → FAIL  (value-regression fixture)
   §4.3-4.6 rules, cross-checked by                   5. on real change: write .received,
   shared (raw,canonical) fixture corpus                 /golden-approve promotes to .verified
                                                         ONLY with human CODEOWNERS sign-off (P9)
```

Trace of the primary use case: a seed TSV enters via `golden/<case>/input/`, the runner spawns the .NET toy converter (A-model boundary), both the converter output and the approved baseline pass through the identical §4-5 normalization core, and a normalized diff decides PASS/FAIL. A parallel path hashes the contract schemas to detect drift.

### Recommended Project Structure (Phase-1 subset of ARCHITECTURE.md)
```
contracts/                       # CONSTITUTION PLANE (human-owned, seeded placeholders)
├── log-specs/
│   ├── standard-log.spec.yaml           # seeded (keep TBD markers)
│   └── standard-log.schema.json         # NEW companion — validated + hashed SoT
├── normalization/
│   ├── correction-rules.catalog.yaml    # seeded
│   ├── correction-rules.schema.json     # NEW companion
│   └── format-conventions.schema.json   # NEW — §4-5 materialized (P14 fix), hashed
├── reference-data/{equipment-master.yaml,.schema.json}
├── state/{equipment-progress.yaml,.schema.json}
├── golden/
│   ├── README.md                        # seeded
│   └── repr-only/  value-regression/     # the TWO demo fixture cases
│       ├── input/seed.tsv
│       ├── expected/baseline.verified.tsv
│       └── meta.yaml
└── .hashes/manifest.json                # GENERATED drift baseline (per-file JCS SHA-256)
docs/
├── tutorials/  how-to/  reference/  explanation/   # Diátaxis (reference/ deferred gen → P3)
├── adr/0001-walking-skeleton-golden-core.md        # MADR
└── glossary.md
libs/
├── python/normalize/                    # §4-5 core (Python thin impl)
└── dotnet/Normalize/                    # §4-5 core (.NET thin impl)
components/
└── toy-converter/ (.NET 10 csproj)      # fixture-grade producer
tools/
├── contract-hash/   contract-drift/     # Python; JCS + classify
├── golden-runner/                       # Python; spawn/capture/normalize/diff
└── bootstrap/                           # dotnet-install + uv resolve (idempotent)
pyproject.toml                           # uv workspace root
```

### Pattern 1: Two canonicalizers, cleanly separated
**What:** JCS (RFC 8785) canonicalizes JSON *contract text* for the drift hash; the §4-5 comparator canonicalizes *TSV data* for golden equivalence. Different inputs, different libraries, different failure meanings.
**When:** JCS runs on `contracts/**/*.schema.json`; the §4-5 comparator runs on producer TSV output.
**Anti-pattern:** trying to hash TSV with JCS or normalize TSV with a JSON canonicalizer — they share the *word* "canonical" and nothing else.

### Pattern 2: Materialize cross-cutting conventions as a hashed schema (P14 fix)
**What:** Encode §4.3–4.6 (encoding=utf-8, bom=false, newline=lf, decimal_sep=".", culture=invariant, timezone=utc-iso8601, null_token=<agreed>, tsv_escape=<rule>, interval="[start,end)") as explicit fields inside `format-conventions.schema.json` (or as `const` values / a `$defs` block). Include that file in the hashed manifest.
**Why:** The drift hash then changes when the null-token policy changes, not only when a column moves — closing the P14 hole. Demo success-criterion 2 must mutate a §4-5 field (e.g., flip `bom: false`→`true`) and show the gate trips.

### Pattern 3: A-model boundary via subprocess + exit-code contract (§4.5)
**What:** Python golden-runner calls `subprocess.run([dotnet_exe, toyconv_dll, "--in", seed, "--out", tmp])` (or reads stdout). Exit code map: `0`=success, non-zero=failure reason (§4.5). No in-process interop (locked, §0).
**When:** Every golden run. This is the whole point of the walking skeleton — exercise the real polyglot process boundary, not a mock.

### Pattern 4: `/golden-approve` human gate, Phase-1 minimal form
**What:** Baseline files use a two-state convention (`.received` = machine-proposed, `.verified` = human-approved — the Verify/syrupy idiom). The runner and any agent may write `.received`. Promotion to `.verified` requires an explicit human action.
**Phase-1 minimal enforcement (no plugins/CI yet — those are P4/P5):**
- `/golden-approve` script refuses to promote unless an explicit human-confirmation signal is present (e.g., interactive `y` + a `--approve` flag the agent is instructed never to auto-pass, or presence of a human-set env/token). Document that the *hard* enforcement (contract-guard deny, CODEOWNERS) lands in Phase 4/5; Phase 1 ships the *executable refusal* + the `.received`/`.verified` separation so the audit surface exists.
- Every promotion must reference an ADR/rationale (P9). A `.verified` update with no linked decision is the smell to make impossible later.

### Anti-Patterns to Avoid
- **Byte-diff golden compare** (P4): normalize before diff, always.
- **Hashing only the column list** (P14): hash the full schema surface incl. materialized conventions.
- **Agent self-blessing goldens** (P9): only humans promote `.received`→`.verified`.
- **Building harness surface** (P1): no agents/skills/plugins/emitter this phase.
- **One-language golden truth**: the §4-5 rule is canonical; both languages implement it and a shared fixture corpus proves parity (D-04).
- **Replacing GSD SessionStart hooks**: append a new entry; do not overwrite the existing two.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RFC 8785 JSON canonicalization | Custom key-sort + number-format serializer | `rfc8785` 0.1.4 (Python) | Number canonicalization (ES6 `Number.prototype.toString`, `-0`, exponent form) is subtle; Trail of Bits impl is spec-exact |
| JSON Schema Draft 2020-12 validation | Custom validator | `jsonschema` 4.26.0 (Py) / `JsonSchema.Net` 9.2.2 (.NET) / `check-jsonschema` CLI | Draft 2020-12 `$dynamicRef`/`unevaluatedProperties` are hard; reference impls exist both sides |
| InvariantCulture decimal formatting (.NET) | Manual string munging | `CultureInfo.InvariantCulture` + `decimal.ToString("R"/"G17")` | Locale bugs (§4.6 `1,5` vs `1.5`) are the exact hazard; the framework handles it |
| Decimal parse/compare (Python) | `float()` round-trip | `decimal.Decimal` + explicit tolerance | float repr causes spurious last-digit diffs (§4.6) |
| BOM strip / newline normalize | Byte scanning | Py `codecs`/`str.encode('utf-8')` (no BOM) + `\n` join; .NET `new UTF8Encoding(false)` + explicit `\n` | Standard, well-tested; hand-rolled BOM detection misses UTF-8 BOM edge cases |
| Unicode normalization | Custom | `unicodedata.normalize` (Py) / `string.Normalize()` (.NET) | If NFC/NFD matters for identifier equality, use the stdlib |
| MADR ADR format | Freeform docs | MADR 4.x template | Established number/immutable/supersede convention (DOCS-02) |
| .NET SDK acquisition | Docker image / manual | `dotnet-install.sh --channel 10.0` | Idempotent, cache-aware, official (D-08; Docker rejected) |

**Key insight:** In this domain the "deceptively complex" work is exactly the polyglot representation layer (number formatting, BOM, canonical JSON). Those are the bugs the harness exists to catch — so use spec-exact libraries for them and reserve custom code for the thin glue (the §4-5 rule orchestration and the loop wiring).

## Runtime State Inventory

Greenfield harness build — not a rename/refactor. The repo currently contains only `.claude/`, `.planning/`, `CLAUDE.md` (verified via `ls`). No stored data, live services, OS-registered state, secrets, or build artifacts carry a name that Phase 1 changes.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — verified by repo `ls` (no DB, no datastore) | none |
| Live service config | None — no external services wired this phase | none |
| OS-registered state | None — bootstrap installs .NET to `$HOME/.dotnet` fresh each ephemeral container | idempotent install (not a rename) |
| Secrets/env vars | None introduced Phase 1 | none |
| Build artifacts | None yet (greenfield); `.dotnet/`, `.venv/`, `bin/`/`obj/` will be created — add to `.gitignore` | gitignore the derived toolchain/build dirs |

## Common Pitfalls

### Pitfall 1: Conflating the JCS hasher with the §4-5 comparator
**What goes wrong:** Planner writes one "canonicalizer" task, or makes .NET compute the drift hash.
**Why:** Both are called "canonicalization."
**How to avoid:** Two separate deliverables — Python-only JCS hasher (contract text) + dual-language §4-5 comparator (TSV). .NET needs zero JCS code this phase.
**Warning signs:** A `.NET` task references RFC 8785; a single module tries to normalize both `.schema.json` and `.tsv`.

### Pitfall 2: Drift hash misses cross-cutting conventions (P14)
**What goes wrong:** Hash covers only column specs; flipping BOM/null policy stays green.
**How to avoid:** Materialize §4-5 as `format-conventions.schema.json` and include in the hashed manifest. Success-criterion-2 demo must mutate a §4-5 field.
**Warning signs:** The hash input is a single column-list file.

### Pitfall 3: Byte-diff false reds (P4)
**What goes wrong:** BOM/CRLF/decimal-locale/TZ differences flip the golden red.
**How to avoid:** Normalize both sides through the §4-5 core before diffing; report representation-failures separately from semantic-failures. The two-fixture demo (repr-only PASS, value-regression FAIL) is the acceptance proof.
**Warning signs:** Diff output shows only whitespace/encoding deltas.

### Pitfall 4: Agent self-blessing the golden (P9)
**What goes wrong:** Runner auto-updates the baseline to make a run pass.
**How to avoid:** `.received`/`.verified` split; only human promotes; promotion cites an ADR. Phase-1 ships executable refusal (hard CODEOWNERS/plugin enforcement is P4/P5).
**Warning signs:** A `.verified` file changed in the same commit that turned a fail green, no ADR link.

### Pitfall 5: Bootstrap non-idempotency / clobbering GSD hooks (BOOT-03)
**What goes wrong:** Reinstalls .NET every session (slow) or replaces GSD's existing SessionStart hooks.
**How to avoid:** Cache-check (`test -x $HOME/.dotnet/dotnet && dotnet --version | grep -q '^10\.'` → skip). Add a NEW entry to the existing `.claude/settings.json` `SessionStart` array (currently 2 GSD entries); do not overwrite. Keep the bootstrap fast/quiet on the cached path.
**Warning signs:** Session start is slow; GSD's `gsd-session-state.sh`/`gsd-check-update.js` stop firing.

### Pitfall 6: Over-building the walking skeleton (P1)
**What goes wrong:** Full contract set, many fixtures, command surface.
**How to avoid:** ONE contract exercised end-to-end, TWO fixtures, minimal `/golden` + `/golden-approve`. Defer the rest.

## Code Examples

### JCS canonicalize + hash one schema file (Python, drift gate)
```python
# Source: github.com/trailofbits/rfc8785.py (rfc8785 0.1.4)  [VERIFIED: PyPI]
import json, hashlib, rfc8785
def schema_hash(path: str) -> str:
    obj = json.loads(open(path, "rb").read())
    canon = rfc8785.dumps(obj)          # bytes, RFC 8785 canonical form
    return hashlib.sha256(canon).hexdigest()
# manifest = {rel_path: schema_hash(p) for p in glob("contracts/**/*.schema.json")}
# drift = compare manifest vs contracts/.hashes/manifest.json
```

### §4-5 TSV normalization — Python side (representative subset)
```python
# Source: stdlib codecs/decimal/datetime; rules per integration_contracts §4.3-4.6  [CITED]
from decimal import Decimal
from datetime import datetime, timezone
def normalize_cell(v: str, kind: str, null_token: str) -> str:
    if v == null_token: return "\x00NULL"          # explicit null vs empty (§4.3)
    if kind == "decimal": return format(Decimal(v).normalize(), "f")  # '.' invariant (§4.6)
    if kind == "datetime":                          # UTC ISO-8601 fixed (§4.4)
        return datetime.fromisoformat(v).astimezone(timezone.utc).isoformat()
    return v
def normalize_tsv(raw: bytes) -> str:
    text = raw.decode("utf-8-sig")                  # strip BOM (§4.3)
    lines = text.replace("\r\n", "\n").split("\n")  # LF (§4.3)
    # ... split on \t, per-column normalize_cell, deterministic row sort ...
    return "\n".join(sorted(lines))                 # deterministic order before diff
```

### §4-5 TSV normalization — .NET side (representative subset)
```csharp
// Source: System.Globalization / System.Text  [CITED: integration_contracts §4.6]
using System.Globalization;
static string NormDecimal(string v) =>
    decimal.Parse(v, CultureInfo.InvariantCulture)
           .ToString("0.############", CultureInfo.InvariantCulture); // '.' only, no thousands
static string NormDateTime(string v) =>
    DateTimeOffset.Parse(v, CultureInfo.InvariantCulture,
        DateTimeStyles.AssumeUniversal | DateTimeStyles.AdjustToUniversal)
        .UtcDateTime.ToString("yyyy-MM-ddTHH:mm:ssZ", CultureInfo.InvariantCulture);
// write output with new UTF8Encoding(false) and explicit "\n" (no BOM, LF)
```

### Idempotent .NET bootstrap (bash, SessionStart)
```bash
# Source: learn.microsoft.com dotnet-install-script  [CITED]
DOTNET_ROOT="$HOME/.dotnet"; export PATH="$DOTNET_ROOT:$PATH"
if [ -x "$DOTNET_ROOT/dotnet" ] && "$DOTNET_ROOT/dotnet" --version 2>/dev/null | grep -q '^10\.'; then
  :  # cached — skip (idempotent)
else
  curl -sSL https://dot.net/v1/dotnet-install.sh -o /tmp/dotnet-install.sh
  bash /tmp/dotnet-install.sh --channel 10.0 --install-dir "$DOTNET_ROOT"
fi
command -v uv >/dev/null && uv sync 2>/dev/null || true    # resolve workspace, idempotent
```

### Shared cross-validation fixture corpus (the D-04 drift catcher)
```
libs/normalize-fixtures/          # ONE corpus, consumed by BOTH language test suites
├── decimal_locale.json           # {"raw":"1,5"|"1.5", "canonical":"1.5", "kind":"decimal"}
├── bom_crlf.json                 # {"raw_bytes_b64":"...", "canonical":"a\tb"}
├── tz_iso8601.json               # {"raw":"2026-07-07 00:00:00+09:00","canonical":"2026-07-06T15:00:00Z"}
└── null_vs_empty.json            # {"raw":"", "canonical":"<empty>"} vs null_token
# Python pytest and .NET xunit both load these; identical canonical output = parity proven.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Newtonsoft-based JSON schema (.NET) | `JsonSchema.Net` (System.Text.Json) | ongoing | No Newtonsoft dep; Draft 2020-12 native |
| xunit v2 | xunit.v3 3.2.2 (Microsoft.Testing.Platform) | 2026 | Cleaner CI exit codes, matches .NET 10 |
| Hand-rolled canonical JSON | `rfc8785` (Trail of Bits) / WebPKI JsonCanonicalizer | 2024+ | Spec-exact number canonicalization |
| Matrix `canonicaljson` | `rfc8785` for strict RFC 8785 | — | `canonicaljson` 2.0.0 is Matrix's variant (number handling differs); use `rfc8785` for the drift gate |

**Deprecated/outdated for this phase:**
- `.NET` JCS library `jsoncanonicalizer` 1.0.0 (NuGet): generic placeholder metadata — avoid; not needed (JCS is Python-only here).
- Docker-image bootstrap / manual `/bootstrap`: rejected in D-08.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Pinning pytest to 8.4.x (vs the 9.1.1 the env resolves) is still desired | Version reconciliation | Low — a pin decision; syrupy 5.x should work on pytest 9 but unverified |
| A2 | `.received`/`.verified` two-file convention is acceptable as the Phase-1 minimal human-gate form (hard enforcement deferred to P4/P5) | Pattern 4 | Medium — if a stronger P1 gate is wanted, add a commit-time check; but plugins/CI are explicitly out of P1 scope |
| A3 | Adding a new entry to the existing `.claude/settings.json` SessionStart array is the correct BOOT-03 wiring (vs a wrapper script) | Bootstrap | Low — both work; array-append is least invasive and preserves GSD hooks |
| A4 | The exact §4-5 null-token, TSV-escape rule, and identifier casing are still `TBD` in the seed and will be chosen as placeholder demo values (domain values are Out of Scope) | CONTRACT-01/02 | Low — placeholders are explicitly allowed; must be flagged as example values, not domain truth |
| A5 | Materializing §4-5 as `format-conventions.schema.json` (vs custom JSON Schema keywords) is the simplest P14-closing shape | Pattern 2 | Low — alternative is `x-` annotations inside each spec schema; either is hashable |

## Open Questions (RESOLVED)

1. **Which single contract drives the walking-skeleton loop?**
   - Know: the TSV `standard-log.spec` is the richest and most representative seed.
   - Unclear: whether the demo TSV should carry 2-3 columns (timestamp/equipment_id/decimal value) sufficient to exercise §4.4 + §4.6 in one fixture.
   - Recommendation: use `standard-log` with a minimal 3-column placeholder (datetime + string id + decimal) so one fixture touches TZ, decimal-locale, BOM, and LF at once.

2. **Golden capture output: stdout vs file?**
   - Know: A-model allows both (§4.5 "exit code + 산출물(파일/DB)").
   - Recommendation: toy converter writes to `--out` file AND the runner also accepts stdout; pick file for the demo (matches §③ file boundary) — simpler atomicity story.

3. **pytest pin (see A1)** — resolve in planning: pin 8.4.x or bump to 9.x after a green syrupy run.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| .NET SDK 10 | toy converter, BOOT-01 | ✗ | — | `dotnet-install.sh --channel 10.0` (the phase deliverable) |
| uv | Python workspace, BOOT-02 | ✓ | 0.8.17 | bump to 0.11.x via `uv self update` |
| Python 3.11 | golden-runner, tools | ✓ | 3.11.15 | — |
| Node.js | GSD hooks / later emitter | ✓ | 22.22.2 | — (not needed for P1 core) |
| pip/network to PyPI | rfc8785, jsonschema install | ✓ | pip 24.0 | — (verified installs succeeded) |
| curl + network to dot.net | bootstrap | ✓ (proxy) | — | pre-cache the install script |

**Missing dependencies with no fallback:** none — the one missing item (.NET SDK) is installed by this very phase's BOOT-01 deliverable.
**Missing dependencies with fallback:** uv present but old (self-update).

## Validation Architecture

nyquist_validation is **enabled** (`config.json workflow.nyquist_validation: true`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework (Python) | pytest 8.4.x (pin) / env has 9.1.1 — resolve A1 |
| Framework (.NET) | xunit.v3 3.2.2 (optional in P1; toy converter may ship with a minimal smoke test) |
| Config file | `pyproject.toml` (uv workspace + pytest config) — created in Wave 0 |
| Quick run command | `uv run pytest tools/golden_runner/tests -x` |
| Full suite command | `uv run pytest && uv run ruff check . && bash tools/contract_drift/check.sh` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONTRACT-01 | Seed YAML + companion schema validate against Draft 2020-12 | unit | `uv run check-jsonschema --schemafile <schema> <instance>` | ❌ Wave 0 |
| CONTRACT-02 | Both language cores produce identical canonical output on shared corpus | unit (parity) | `uv run pytest libs/python/normalize/tests -x` + `dotnet test libs/dotnet` | ❌ Wave 0 |
| CONTRACT-03 (PASS) | repr-only fixture (BOM/CRLF/decimal/TZ) passes golden | integration | `uv run pytest tools/golden_runner/tests/test_repr_only.py -x` | ❌ Wave 0 |
| CONTRACT-03 (FAIL) | value-regression fixture fails golden | integration | `uv run pytest tools/golden_runner/tests/test_value_regression.py -x` | ❌ Wave 0 |
| CONTRACT-04 (drift) | mutating a §4-5 field bumps the hash + trips gate | unit | `uv run pytest tools/contract_drift/tests/test_convention_mutation.py -x` | ❌ Wave 0 |
| CONTRACT-04 (classify) | breaking vs non-breaking classification | unit | `uv run pytest tools/contract_drift/tests/test_classify.py -x` | ❌ Wave 0 |
| CONTRACT-03 (approve) | `/golden-approve` refuses baseline write without human sign-off | unit | `uv run pytest tools/golden_runner/tests/test_approve_gate.py -x` | ❌ Wave 0 |
| BOOT-01 | `dotnet --version` starts with `10.` after bootstrap | smoke | `bash tools/bootstrap/verify.sh` (asserts dotnet 10 + uv resolve) | ❌ Wave 0 |
| BOOT-02/03 | uv workspace resolves; SessionStart runs bootstrap idempotently | smoke | `uv sync --frozen` + second-run cache-hit assertion | ❌ Wave 0 |
| DOCS-01/02 | Diátaxis dirs + adr/0001 + glossary exist | structural | `test -d docs/tutorials && test -f docs/adr/0001-*.md && test -f docs/glossary.md` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest <touched module>/tests -x` (< 30s)
- **Per wave merge:** full suite (`uv run pytest && ruff check && contract-drift check`)
- **Phase gate:** the two-fixture golden demo green (repr PASS / regression FAIL) + drift-mutation demo trips the gate + bootstrap smoke green, before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `pyproject.toml` — uv workspace root + pytest config + tool pins (resolve A1)
- [ ] `tools/golden_runner/tests/conftest.py` — subprocess/toy-converter fixtures
- [ ] `libs/normalize-fixtures/` — shared `(raw,canonical)` corpus (consumed by Py + .NET)
- [ ] `components/toy-converter/` csproj + minimal xunit smoke (needs .NET 10 → BOOT-01 first)
- [ ] `tools/bootstrap/verify.sh` — asserts dotnet 10 + uv resolve
- [ ] Framework install: `uv add --dev pytest syrupy ruff pyright check-jsonschema` + `uv add rfc8785 jsonschema`

## Security Domain

`security_enforcement` is not set to `false`; treated as enabled. Phase 1 is a local build with no auth/session/network surface, so most ASVS categories are N/A, but two apply.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | no auth surface this phase |
| V3 Session Management | no | — |
| V4 Access Control | yes (human gate) | `/golden-approve` + `.received`/`.verified` split; constitution plane human-owned (hard CODEOWNERS/plugin deny deferred to P4/P5) |
| V5 Input Validation | yes | JSON Schema (Draft 2020-12) validation of all contract instances via `jsonschema`/`check-jsonschema`; the golden-runner validates seed inputs |
| V6 Cryptography | yes (integrity, not secrecy) | SHA-256 via `hashlib` over RFC 8785 canonical bytes — never hand-roll the hash or the canonicalization |
| V12/V5 File handling | yes | golden `input/` must be non-sensitive small samples (seed README rule); no credentials in fixtures |

### Known Threat Patterns for {Python subprocess + .NET CLI + contract files}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Command injection via job args to `subprocess` | Tampering/Elevation | `subprocess.run([list], shell=False)` — never string+shell; validate paths |
| Slopsquatted dependency (rfc8785 etc.) | Tampering | slopcheck gate (done — all [OK]); pin exact versions in lockfile |
| Golden baseline tampering / self-bless | Repudiation/Tampering | `.received`/`.verified` split + ADR-linked promotion (P9) |
| Drift hash blind spot (§4-5 not hashed) | Tampering | Materialize conventions as hashed schema (P14) |
| Secret/PII leaking into golden fixtures | Info Disclosure | Non-sensitive sample rule; (secret-scan hook is P4) |
| Path traversal in `--out`/`--in` | Tampering | Resolve + confine to workspace tmp dir |

## Sources

### Primary (HIGH confidence)
- `/workspace/presentationformat/archive/parserimprove/uploads/integration_contracts_design.md` §4.1, §4.3–4.6, §5, §6, §④ (A-model) — cross-cutting contract rules, exit-code map, change mgmt — read directly
- `/workspace/.../monorepo_skeleton/contracts/{log-specs,normalization,reference-data,state,golden}` — seed source, read verbatim (4 YAML + golden README)
- `.planning/research/{STACK,ARCHITECTURE,PITFALLS}.md` + `CLAUDE.md` — pinned stack, build order, P4/P9/P14
- PyPI JSON API — `rfc8785` 0.1.4 (Trail of Bits), `jsonschema` 4.26.0, `check-jsonschema` 0.37.4, `syrupy` 5.5.1 latest — verified live
- NuGet registration API — `JsonSchema.Net` 9.2.2 (Greg Dennis, System.Text.Json) — verified live
- slopcheck 0.6.1 — `rfc8785`/`jsonschema`/`check-jsonschema`/`ruff`/`pyright`/`pytest` all `[OK]` — run live
- `.claude/settings.json` + `gsd-session-state.sh` — existing SessionStart hook shape (2 entries) — read directly
- `.planning/config.json` — nyquist_validation true, mode yolo — read directly

### Secondary (MEDIUM confidence)
- learn.microsoft.com dotnet-install script semantics (`--channel`, `--install-dir`) — [CITED], from CLAUDE.md-sourced research
- MADR 4.x ADR template — [CITED], established convention

### Tertiary (LOW confidence)
- `.NET` JCS library landscape (`jsoncanonicalizer` NuGet 1.0.0 generic metadata) — flagged, and avoided (not needed)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — pinned in CLAUDE.md + verified live via PyPI/NuGet/slopcheck
- Loop wiring / two-canonicalizer split: HIGH — grounded in §4-5 + D-01..07 + verified rfc8785
- Drift-gate P14 shape: HIGH — materialized-schema pattern is a direct P14 mitigation
- Bootstrap idempotency + hook coexistence: MEDIUM-HIGH — pattern verified against existing settings.json; exact GSD-hook interaction to confirm at implementation
- Docs skeleton scope: MEDIUM-HIGH — Diátaxis + MADR standard; exact page list is Claude's discretion
- `/golden-approve` Phase-1 minimal form: MEDIUM — A2 assumption; hard enforcement is explicitly a later phase

**Research date:** 2026-07-08
**Valid until:** 2026-08-07 (stable stack; re-verify PyPI/NuGet versions if bumping pins)
