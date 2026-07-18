# Phase 16: Local Memory Web UI (v2.1 E) - Research

**Researched:** 2026-07-18
**Domain:** Local single-user web tool (Python stdlib) + a DERIVED reference-index generator + referential-integrity surfacing over the committed `.memory/` planes
**Confidence:** HIGH (this is a code-precedent-driven phase; every shape to clone exists in-repo and was read directly)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-16-01 — Runtime & stack:** Python stdlib `http.server` bound to `127.0.0.1`, serving a **single inlined HTML/JS page**, **zero new dependencies**. New workspace member **`tools/memory_ui/`** (auto-enrolled by the existing `tools/*` glob). **Never bind `0.0.0.0`** — the bind address is the security boundary. **No** Flask/FastAPI, no CDN, no build step, no external fetch in the page.
- **D-16-02 — Pointer-index:** A DERIVED reference scanner `tools/memory_regen/pointer_index.py` → gitignored `.memory/derived/pointer-index.{json,md}`, **cloning `repo_map.py`'s generator shape** (`_REPO_ROOT`/`DERIVED_DIR`/`DERIVED_HEADER`, `render`/`write`, write→hash→delete→regenerate determinism test, **NO wall-clock/timestamp**). A pointer = any occurrence, across a fixed set of scan roots, of (a) a `.memory/...` file-path string, or (b) an agreement **slug**. Scan roots: `docs/`, `harness/`, `tools/memory_regen/inject.py`, `.memory/README.md`, `AGENTS.md`. Output keyed by memory-item → list of `{file, line, kind}` referrers. **Lives in DERIVED plane** — generated, never hand-maintained; the `.md` twin carries the `DERIVED — do not hand-edit` header. **`tools/memory_regen` must NOT write agreements** (tier contract) — it only *reads* agreements and *writes* `derived/`.
- **D-16-03 — Referential integrity:** **Surface-and-confirm.** On an edit that changes a slug/path, or a retire, query the pointer-index; if referrers exist, show "N references point here; this edit/retire will orphan them" with the `file:line` list and **block behind an explicit confirm**. **NEVER auto-rewrite external docs** (`docs/`, `harness/skills`, `inject.py`).
- **D-16-04 — Write path:** **Reuse existing writers; add no new write path.** Agreements add/retire go through `tools.agree.write` (`add`/`retire`) — provenance stamping, YAML-safe `--because`, flip-in-place retire preserved; **retire = flip `status: retired`, never delete**. The UI supplies `--because` from a **required field — it must NOT invent one**. Progress state (`activeContext.md`/`progress.md`) editable as raw markdown body; on save refresh the `updated:` stamp via the `/checkpoint` write path (never a wall-clock in the read path). Pointer-index is DERIVED and **read-only** in the UI.

### Claude's Discretion

- Frontend layout, endpoint/route naming, JSON schema of the pointer-index, and test decomposition within the shapes fixed above.
- Whether the pointer scanner **shares** confinement/exclusion helpers with `repo_map.py` or **clones** them (prefer share-not-re-derive per D-05/D-18; a fixture-parity test is an acceptable fallback if extraction proves invasive).

### Deferred Ideas (OUT OF SCOPE)

- **Auto-rewriting referrers** (docs/skills/inject.py) to fix orphaned pointers → rejected (D-16-03). Surface + confirm only.
- **Per-instance agreement overlays** (MEM2-F1) → future milestone.
- **Remote / hosted / authenticated memory UI** → permanently out of scope (REQUIREMENTS "Out of Scope").
- **Rich structured progress editor** → raw-markdown-body + stamp refresh suffices.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MEM2-07 | Local web tool to view/edit/retire memory items (progress + per-guideline agreements) with pointer-aware UX: surfaces "what points to this item" and keeps references consistent on edit/retire. Local only (no network, no auth); operates on committed memory files + a machine-built derived pointer-index. | Standard Stack (stdlib http.server, reuse `tools.agree.write` + `harness_lint.agreements`); Architecture Patterns (DERIVED-generator clone, route-logic-as-pure-functions); Runtime State Inventory (no runtime state migration — read-mostly over committed files); Validation Architecture (SC1–SC3 → observable test map). |
</phase_requirements>

## Summary

Phase 16 is a **read-mostly hygiene surface** over already-finished memory files, not a new subsystem. Three deliverables, each with an exact in-repo precedent to clone: (1) a **DERIVED reference-index generator** `tools/memory_regen/pointer_index.py` that mirrors `repo_map.py`/`contracts_index.py` byte-for-byte in structure — `_REPO_ROOT`/`DERIVED_DIR`/`DERIVED_HEADER`, `build_index`/`render`/`write`/`main`, a write→hash→delete→regenerate determinism test, and **no timestamp anywhere**; (2) a **stdlib `http.server` tool** `tools/memory_ui/` that serves one inlined HTML/JS page bound to `127.0.0.1` and exposes JSON endpoints for list/view/edit/retire; (3) **surface-and-confirm referential integrity** that queries the pointer-index before any destructive edit and blocks orphaning behind an explicit confirm.

The write path is entirely delegated: agreements flow through `tools.agree.write.add`/`retire` (which already enforce the anti-invent `--because` guard, YAML-safe provenance, and flip-in-place retire), and progress edits refresh the `updated:` stamp the way `/checkpoint` does (quoted-date frontmatter). The UI **must never** write agreement files directly, fabricate a `--because`, or introduce a wall-clock into the injector read path. The pointer-index is gitignored (session-ephemeral like `repo-map.md`, NOT the committed-derived `contracts-index.md` exception), so it needs **no** CI stale-derived gate — but that also means a `git diff` gate is blind to it, so its determinism must be proven by regenerate-and-hash.

**Primary recommendation:** Build `pointer_index.py` first as a faithful `repo_map.py` clone (it is the load-bearing new engine and the UI's data source), factor the `http.server` handler's route logic into **pure functions that take injected directories** (so tests never open a socket and never touch real `.memory/agreements/`), and wire the generator into the existing SessionStart/`/refresh-memory`/`/orient` regen set — accepting that touching `harness/plugins/session-inject.ts` triggers a Phase-7 emit round-trip to both runtimes.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Serve the page + route requests | Local HTTP server (`tools/memory_ui`, stdlib `BaseHTTPRequestHandler`) | — | Single-user localhost tool; the bind address (`127.0.0.1`) *is* the auth boundary (D-16-01). |
| Render/interact (list, view, edit, retire, confirm) | Browser (one inlined HTML/JS page) | — | "Local only" must be literally true — nothing to fetch, no framework, no CDN (D-16-01, `<specifics>`). |
| Build "what points to this item" index | Derived-plane generator (`tools/memory_regen/pointer_index.py`) | — | DERIVED = machine-owned, gitignored, regenerated; owned by the package that owns `derived/` (D-16-02). |
| Add/retire agreements (write) | Existing writer (`tools.agree.write`) | — | Reuse-not-reinvent; preserves provenance + anti-invent guard + flip-in-place retire (D-16-04). |
| Stamp progress `updated:` (write) | `/checkpoint` write semantics (quoted-date frontmatter) | — | Write path may use a date (like `/checkpoint`); the **read** path (`assemble()`) must stay clock-free (D-16-04, MEM2-05). |
| Parse/list agreement + state files (read) | Shared parsers (`harness_lint.agreements`, `harness_lint.frontmatter`) | — | One shared parser, never re-rolled (matches `inject.py` reuse). |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python `http.server` (`BaseHTTPRequestHandler`, `ThreadingHTTPServer`) | stdlib (py ≥3.11) | Localhost HTTP + routing for the tool | Zero-dep, sufficient for a single-user local tool; matches the "no second toolchain" posture. `[VERIFIED: local python3 import]` |
| Python `json` | stdlib | Pointer-index `.json` + API request/response bodies | Native; the UI reads `pointer-index.json`. `[VERIFIED: stdlib]` |
| Python `pathlib`, `hashlib`, `re` | stdlib | Path confinement, determinism hashing, scan matching | Same primitives `repo_map.py` uses. `[VERIFIED: read in repo]` |

### Supporting (existing in-repo modules to REUSE, not rebuild)
| Module | Purpose | Public surface the UI/generator calls |
|--------|---------|----------------------------------------|
| `tools.agree.write` | Agreement add/retire (the ONLY sanctioned agreement writer) | `add(slug, title, rule, *, because, added, related=None, agreements_dir=AGREEMENTS_DIR) -> Path`; `retire(slug, *, agreements_dir=AGREEMENTS_DIR) -> Path`; raises `AgreementRefused`. `[VERIFIED: tools/agree/write.py]` |
| `tools.harness_lint.agreements` | Discover + parse agreement files (fail-closed, confined, sorted) | `iter_agreement_files(agreements_dir) -> list[Path]`; `load_agreement(path) -> tuple[dict, str] | None`. `[VERIFIED: tools/harness_lint/agreements.py]` |
| `tools.harness_lint` (`frontmatter`) | Split YAML frontmatter/body | `parse_frontmatter(md_text) -> tuple[dict, str]` (CRLF-safe, ruamel safe loader). `[VERIFIED: tools/harness_lint/frontmatter.py]` |
| `tools.harness_lint.provenance` | Validate a written agreement (optional post-write check) | `lint_file(path) -> list[Violation]`. `[VERIFIED: grep signature]` |
| `tools.memory_regen.repo_map` | The DERIVED-generator template + (candidate) shared confinement helper | `_iter_source_files`, `DERIVED_HEADER`, `render`/`write` shape; `_REPO_ROOT`/`DERIVED_DIR`. `[VERIFIED: tools/memory_regen/repo_map.py]` |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib `http.server` | Flask / FastAPI | Explicitly forbidden (D-16-01) — adds a dep + heavier surface for a single local page. |
| Node/opencode tool | — | Would add a second toolchain for one page; every existing `tools/*` is Python `python -m` (D-16-01). |
| New agreement writer in the UI | `tools.agree.write` | Forbidden (D-16-04) — bypassing loses provenance/anti-invent/flip-in-place guarantees. |
| Committing `pointer-index` (like `contracts-index.md`) | Gitignored session-ephemeral (like `repo-map.md`) | Committed-derived would need a CI stale-derived gate; the index is a convenience view, not a gated contract — keep it ephemeral (matches `repo-map.md`). |

**Installation:** No `uv add`. New member `tools/memory_ui/pyproject.toml` mirrors `tools/agree/pyproject.toml` verbatim (name `logparser-memory-ui`, `dependencies = []`, `[tool.uv] package = false`). Auto-enrolled by the root `members = ["libs/python", "tools/*"]` glob. `pointer_index.py` is a **new module inside the existing `tools/memory_regen/`** member — no new member, no pyproject change there.

## Package Legitimacy Audit

> Not applicable — this phase installs **zero external packages** (D-16-01: stdlib only, `dependencies = []`). No registry, slopcheck, or postinstall surface to audit. All code reuses in-repo modules already vendored and tested in Phases 12–15.

## Architecture Patterns

### System Architecture Diagram

```
                          ┌─────────────────────────────────────────────┐
  Browser (localhost)     │  tools/memory_ui  (python -m tools.memory_ui)│
  ┌───────────────────┐   │  ThreadingHTTPServer(("127.0.0.1", PORT))    │
  │ one inlined        │   │  BaseHTTPRequestHandler                       │
  │ HTML/JS page       │◄──┤  GET  /            → serve inlined page       │
  │ (no CDN, no fetch  │   │  GET  /api/items   → list state+agreements    │
  │  of external URLs) │   │  GET  /api/item    → view one item body       │
  │                    │──►│  GET  /api/pointers?item=… → referrers        │
  │ edit / retire /    │   │  POST /api/agreement/add|retire  ─────────────┼──► tools.agree.write.add / retire
  │ confirm-orphan     │   │  POST /api/progress/save   ───────────────────┼──► write state body + `updated:` stamp
  └───────────────────┘   └───────┬───────────────────────┬───────────────┘        (checkpoint semantics)
                                   │ reads                 │ reads (referential-integrity check)
                                   ▼                       ▼
              ┌────────────────────────────┐   ┌───────────────────────────────────────┐
              │ .memory/state/*.md          │   │ .memory/derived/pointer-index.json     │
              │ .memory/agreements/*.md      │   │  (generated, gitignored, read-only)    │
              │  (committed, read via        │   └───────────────▲───────────────────────┘
              │   harness_lint parsers)      │                   │ writes (build→render→write)
              └──────────────────────────────┘   ┌───────────────┴───────────────────────┐
                                                  │ tools/memory_regen/pointer_index.py     │
   scan roots (read-only) ────────────────────►  │  scans docs/, harness/, inject.py,       │
   docs/  harness/  inject.py  .memory/README.md  │  .memory/README.md, AGENTS.md            │
   AGENTS.md                                       │  → {memory-item: [{file,line,kind}]}    │
                                                  │  DERIVED header, NO timestamp            │
                                                  └──────────────────────────────────────────┘
        (regen wiring): session-inject.ts regen loop + /orient + /refresh-memory  ──► runs pointer_index alongside repo_map + contracts_index
```

Data-flow trace of the primary use case (retire an agreement safely): browser POST `/api/agreement/retire?slug=X` → handler first calls the pointer-index lookup for item `X` → if referrers exist, returns `409 {orphans:[{file,line,kind}]}` and the page shows the confirm prompt → on confirmed re-POST (`confirm=1`), handler calls `tools.agree.write.retire(X)` (flip `status: retired`) → returns success. The handler never rewrites the referrers.

### Recommended Project Structure
```
tools/memory_ui/
├── __init__.py
├── pyproject.toml          # clone of tools/agree/pyproject.toml (zero deps, package=false)
├── __main__.py             # `python -m tools.memory_ui` → parse --port, start server (127.0.0.1)
├── server.py               # ThreadingHTTPServer + BaseHTTPRequestHandler shell (thin)
├── routes.py               # PURE route functions: list_items(dirs), view_item(...), retire(...), save_progress(...)
├── page.py                 # the single inlined HTML/JS string (PAGE = "...") — no external URLs
└── tests/
    ├── __init__.py
    ├── conftest.py         # sys.path wiring parents[3] (mirror tools/agree + memory_regen conftest)
    └── test_*.py           # route-logic tests via tmp_path; optional live-socket smoke test

tools/memory_regen/
├── pointer_index.py        # NEW — clone of repo_map.py shape
└── tests/
    ├── __snapshots__/test_pointer_index.ambr   # committed syrupy reference over tmp fixture
    └── test_pointer_index_determinism.py        # clone of test_repo_map_determinism.py
```

### Pattern 1: DERIVED generator (clone `repo_map.py` / `contracts_index.py`)
**What:** A module with module-level `_REPO_ROOT = Path(__file__).resolve().parents[2]`, `DERIVED_DIR = _REPO_ROOT/".memory"/"derived"`, output paths, a `DERIVED_HEADER` string, and the quartet `build_index()` → `render()` → `write()` → `main()`. **No timestamp, no wall-clock, no raw float** in the body; deterministic sort of everything before render.
**When to use:** For `pointer_index.py` — the JSON twin serializes the same sorted structure with `json.dumps(..., indent=2, sort_keys=True)` (deterministic); the `.md` twin renders a readable table under the `DERIVED — do not hand-edit (tools/memory_regen/pointer_index.py)` header.
**Example (structure to mirror — from `repo_map.py`):**
```python
# Source: tools/memory_regen/repo_map.py:33-43, 188-199 (read in-session)
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
JSON_PATH = DERIVED_DIR / "pointer-index.json"
MD_PATH = DERIVED_DIR / "pointer-index.md"
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/pointer_index.py)"

def write(json_path=JSON_PATH, md_path=MD_PATH, *, base_dir=None, scan_roots=None) -> tuple[Path, Path]:
    index = build_index(base_dir=base_dir, scan_roots=scan_roots)   # deterministic dict
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(render_md(index), encoding="utf-8")
    return json_path, md_path
```

### Pattern 2: Pointer scan — what counts as a referrer, keyed by memory item
**What:** Enumerate **memory items** = the state files (`.memory/state/activeContext.md`, `progress.md`) + every active/retired agreement file (`iter_agreement_files`). For each **scan root** file, read line-by-line and record a referrer when a line contains either (a) the item's `.memory/...` POSIX path string, or (b) — for agreements only — the agreement **slug** (the filename stem). Key: `{ "<memory-item-relpath>": [ {"file": "<relpath>", "line": <int>, "kind": "path"|"slug"}, ... ] }`.
**When to use:** In `build_index()`. Sort item keys and each referrer list `(file, line, kind)` before emit for determinism.
**Scan-root confinement + self-exclusion (critical):**
- Scan roots (D-16-02): `docs/`, `harness/`, `tools/memory_regen/inject.py` (single file), `.memory/README.md` (single file), `AGENTS.md` (single file). Walk directory roots recursively; include single-file roots directly.
- **MUST exclude `.memory/derived/`** from any walk — the index would otherwise reference itself and churn. (No scan root includes `derived/` today, but if `.memory/` is ever walked, skip `derived/`.) Reuse `repo_map._iter_source_files`'s symlink-confinement idiom (`root_resolved not in resolved.parents → skip`).
- Restrict to text files (`.md`, `.ts`, `.py`, `.json`, `.toml`, no-suffix like `AGENTS.md` are `.md`). Skip binary/large by suffix allow-list — mirrors `lang_for_path` gating.
**Slug→file mapping:** an agreement slug `X` maps to `.memory/agreements/X.md` (the writer's `_target_for`/`iter_agreement_files` naming). `[VERIFIED: tools/agree/write.py:33-44]`
**False-positive avoidance:** match the slug as a **word-boundaried token** (`re.search(r"(?<![\w-])" + re.escape(slug) + r"(?![\w-])", line)`), not a bare substring, so slug `plan` doesn't match `planner`. Prefer matching the **full `.memory/agreements/X.md` path** as `kind:"path"` and only fall back to bare-slug `kind:"slug"` for prose references. Record `kind` so the UI/planner can weight path-hits over slug-hits.

### Pattern 3: HTTP route logic as pure functions (testability seam)
**What:** Keep `BaseHTTPRequestHandler.do_GET`/`do_POST` as a **thin dispatch shell** that parses the path/query/body and delegates to pure functions in `routes.py` that take **injected directories** (`agreements_dir`, `state_dir`, `derived_dir`) and return `(status:int, headers:dict, body:bytes)`. This mirrors how `inject.assemble(..., agreements_dir=, state_dir=, derived_dir=)` takes injected dirs so tests never touch the real planes.
**When to use:** Everywhere — it is the only way to test without a live socket AND without writing real agreements.
**Example (dependency-injection idiom already used repo-wide):**
```python
# Source: tools/memory_regen/inject.py:128-133 (assemble takes injected plane dirs)
def assemble(budget_chars=4000, derived_dir=DERIVED_DIR, state_dir=STATE_DIR, agreements_dir=AGREEMENTS_DIR): ...
# Phase-16 routes follow the same shape:
def retire_agreement(slug, *, agreements_dir, derived_dir, confirm=False) -> tuple[int, dict, bytes]:
    orphans = pointer_lookup(slug, derived_dir=derived_dir)
    if orphans and not confirm:
        return 409, {"Content-Type": "application/json"}, json.dumps({"orphans": orphans}).encode()
    path = agree_write.retire(slug, agreements_dir=agreements_dir)   # reuse the sanctioned writer
    return 200, {"Content-Type": "application/json"}, json.dumps({"retired": path.name}).encode()
```

### Pattern 4: Progress `updated:` stamp on save (checkpoint semantics, not a read-path clock)
**What:** `/checkpoint` writes `updated: "YYYY-MM-DD"` (quoted string) into the frontmatter of `activeContext.md`/`progress.md` and commits only those files. On a UI progress save, rewrite the body and set `updated: "<today ISO>"` **quoted**, preserving the rest of the frontmatter. This is a **write-path** date (allowed, exactly like `/checkpoint`) — it is NOT a wall-clock in `assemble()` (the read path stays deterministic). `[VERIFIED: harness/commands/checkpoint.md:18-20]`
**⚠ Gap:** `/checkpoint` is a **markdown command**, not a callable Python function — there is **no** existing Python writer for the state stamp (unlike `tools.agree.write` for agreements). The planner must choose: (a) add a tiny `tools/memory_ui` helper that writes the quoted-date frontmatter + body (round-tripping via `parse_frontmatter` + a quoted-scalar dump), or (b) put the stamp writer in `tools/memory_regen` or a shared spot. Keep the date quoted so it stays a string (checkpoint.md is explicit about this).

### Anti-Patterns to Avoid
- **UI writing `.memory/agreements/*` directly** — forbidden by the tier contract and D-16-04; always go through `tools.agree.write`.
- **Fabricating `--because`** — the writer refuses blank `because` (exit 3 / `AgreementRefused`); the UI must expose a **required** field and pass it verbatim.
- **Auto-rewriting referrers** to fix orphans — forbidden (D-16-03); surface + confirm only.
- **Timestamp/float/random in the generator body** — breaks the write→hash→delete→regenerate determinism test; `repo_map.py` proves this with a regex asserting no `\d{4}-\d{2}-\d{2}` and no `0\.\d{3,}`.
- **Binding beyond `127.0.0.1`** — the bind address is the security boundary; never `0.0.0.0`, never `""`.
- **`git diff` as the generator's correctness check** — `.memory/derived/` is gitignored; a diff gate is blind (same class as the Phase-15 CR-01 emit-drift finding). Use regenerate-and-hash.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Add/retire an agreement | A new file writer | `tools.agree.write.add`/`retire` | Preserves provenance stamp, YAML-safe `--because`, flip-in-place retire, anti-invent refusal (D-16-04). |
| Discover/parse agreements | `glob` + string slicing | `harness_lint.agreements.iter_agreement_files` / `load_agreement` | Fail-closed, symlink-confined, `_`/README-excluded, sorted — the same corpus `inject.py` reads. |
| Split YAML frontmatter | Manual `---` slicing | `harness_lint.parse_frontmatter` | CRLF-safe, ruamel safe loader, one shared parser (already the repo rule). |
| DERIVED generator scaffolding | New generator shape | Clone `repo_map.py`/`contracts_index.py` | The header/render/write/main quartet + determinism test are a proven template. |
| Path confinement in the scanner | New traversal guard | Reuse `repo_map._iter_source_files` symlink-confinement idiom (share, per discretion) | Same defense `hash.py`/`repo_map.py` use; extraction or fixture-parity per D-16 discretion. |
| Serialize provenance / slug validation | New regex | `tools.agree.write._SLUG` / `_target_for` semantics | Slug rules (`^[a-z0-9]+(?:-[a-z0-9]+)*$`, no `_`-prefix, no path escape) already codified. |

**Key insight:** This phase is ~80% reuse (like `contracts_index.py`). The only genuinely new logic is the **pointer scan** (Pattern 2) and the **HTTP shell** (Pattern 3). Everything touching agreements, frontmatter, and the derived-plane contract already exists and is tested.

## Runtime State Inventory

> This is a read-mostly tool over committed files, not a rename/migration. No stored keys, service configs, or IDs are being renamed. Included for completeness.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — the tool reads/edits committed `.memory/state/*.md` + `.memory/agreements/*.md` in place; no datastore, no key renames. Active agreement set is legitimately **empty** today. | None — exercise against `tmp_path` fixtures only (never write real agreements). |
| Live service config | None — no external service; the server is spawned on demand (`python -m tools.memory_ui`) and bound to localhost. | None. |
| OS-registered state | None — no daemon/task registration; the server runs foreground for the session. | None. |
| Secrets/env vars | None new. Agreements/state must never contain secrets (existing rule); the UI adds no env var, no token, no auth secret (localhost bind is the boundary). | None. |
| Build artifacts | New workspace member `tools/memory_ui/` adds ~4 deterministic `uv.lock` lines (zero-dep member, mirrors `tools/agree` per 14-CONTEXT D-19); `pointer_index.py` adds none (module inside existing member). | `uv sync` once after adding the member; verify the lock delta is the expected zero-resolution member entry. |

**Nothing found in categories Stored/Service/OS/Secrets:** verified by reading the phase decisions (read-mostly over committed files) and the tier contracts.

## Common Pitfalls

### Pitfall 1: The generator determinism trap (gitignored → git-diff-blind)
**What goes wrong:** A timestamp, unsorted dict, or raw float sneaks into `pointer-index.{json,md}`; because `.memory/derived/` is gitignored, a `git diff --exit-code` gate never catches the churn.
**Why it happens:** Reflexively adding "generated at <date>"; relying on the wrong verification (git diff) as `repo_map.py:15` warns.
**How to avoid:** Clone `test_repo_map_determinism.py` exactly — `render` twice is byte-identical; write→sha256→delete→regenerate→same hash; regex-assert no `\d{4}-\d{2}-\d{2}` and no raw float; commit a syrupy snapshot over a **tmp fixture** (keyed to `base_dir` so `tmp_path` never leaks). `json.dumps(sort_keys=True)`.
**Warning signs:** Two consecutive `write()` calls differ; a snapshot that changes between runs.

### Pitfall 2: Tests that write real agreements or open real sockets
**What goes wrong:** A test calls `add()`/`retire()` against the real `.memory/agreements/` or starts a server on a fixed port, polluting the repo / flaking on port collisions.
**Why it happens:** Not threading `agreements_dir=`/`derived_dir=` through; testing via the socket instead of route functions.
**How to avoid:** Inject dirs everywhere (Pattern 3); reuse the `tmp_agreements_tree` fixture already exported from `harness_lint.tests.conftest` (re-exported by `memory_regen`'s conftest). For any live-socket smoke test, bind port `0` (ephemeral) and read `server.server_address[1]`.
**Warning signs:** `.memory/agreements/*.md` appears in `git status` after a test run.

### Pitfall 3: Touching `inject.py` / `session-inject.ts` triggers hidden gates
**What goes wrong:** Wiring `pointer_index` into the SessionStart regen loop edits `harness/plugins/session-inject.ts` (the regen array at line ~36) and/or `harness/commands/{orient,refresh-memory}.md` — which are **emitter source**; the change must round-trip to `.opencode/` + `.claude/` or the emit-drift gate fails (Phase-15 lesson). If any code path reads `inject.py`, the byte-identity determinism test + no-wall-clock static gate must stay green.
**Why it happens:** Treating `harness/` files as ordinary edits.
**How to avoid:** After wiring, re-run `tools/harness_emit` and commit both runtime trees (mirror Phase 15's plan); do NOT add a wall-clock to `inject.py`. Note the pointer-index is gitignored/session-ephemeral, so it needs **no** stale-derived CI gate (unlike `contracts-index.md`).
**Warning signs:** emit-drift gate red; `test_inject_determinism` red.

### Pitfall 4: Orphan detection reads a stale index
**What goes wrong:** The referential-integrity check reads `pointer-index.json` that predates the current tree, so it misses (or invents) referrers.
**Why it happens:** The index is regenerated at SessionStart but the docs changed mid-session.
**How to avoid:** On a destructive action, either regenerate the index inline (cheap — it's a text scan) or clearly label the confirm prompt with the index's provenance ("based on the last regen; run /refresh-memory to update"). Prefer inline regeneration before the orphan check for correctness.
**Warning signs:** Confirm prompt lists a `file:line` that no longer contains the reference.

## Code Examples

### Reusing the sanctioned agreement writer with the anti-invent guard
```python
# Source: tools/agree/write.py:47-79 (add) — because is REQUIRED, blank → AgreementRefused
from tools.agree.write import add, retire, AgreementRefused
try:
    add(slug, title, rule, because=user_supplied_because, added=date.today().isoformat(),
        related=related, agreements_dir=agreements_dir)   # UI passes the user's words verbatim
except AgreementRefused as exc:
    # surface exc's REFUSED: message to the page; never fabricate a because to retry
    ...
```

### Determinism test to clone for the generator
```python
# Source: tools/memory_regen/tests/test_repo_map_determinism.py:35-44 (write→hash→delete→regen)
def test_write_delete_regenerate_is_byte_identical(tmp_path, fixture_tree):
    out_json = tmp_path / "derived" / "pointer-index.json"
    pointer_index.write(json_path=out_json, md_path=tmp_path/"derived"/"pointer-index.md",
                        base_dir=fixture_tree, scan_roots=[fixture_tree])
    d1 = hashlib.sha256(out_json.read_bytes()).hexdigest()
    out_json.unlink()
    pointer_index.write(json_path=out_json, md_path=tmp_path/"derived"/"pointer-index.md",
                        base_dir=fixture_tree, scan_roots=[fixture_tree])
    assert d1 == hashlib.sha256(out_json.read_bytes()).hexdigest()
```

### Localhost-only server bootstrap
```python
# tools/memory_ui/server.py — ThreadingHTTPServer bound to 127.0.0.1 ONLY (D-16-01)
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
def serve(port: int = 8765) -> None:
    httpd = ThreadingHTTPServer(("127.0.0.1", port), MemoryUIHandler)  # never "0.0.0.0"/""
    httpd.serve_forever()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual hand-edit of `.memory/agreements/*` + hope no doc pointer breaks | UI over `tools.agree.write` + machine-built pointer-index + surface-and-confirm | This phase (MEM2-07) | Memory hygiene is systematized; hand-edits can no longer silently orphan a pointer (ROADMAP SC3). |
| Derived artifacts verified by `git diff` | Regenerate-and-hash (gitignored plane is diff-blind) | Established Phase 2, reaffirmed Phase 15 CR-01 | The pointer-index MUST use regenerate-and-hash. |

**Deprecated/outdated:** none relevant — this phase reuses current machinery only.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | No reusable Python function exists for the progress `updated:` stamp (`/checkpoint` is a markdown command); the planner must add a small stamp-writer helper. | Pattern 4 | If a callable already exists elsewhere, the plan adds a redundant helper — low blast radius; verify by grepping for a state-stamp writer before authoring. |
| A2 | Pointer-index should be **gitignored/session-ephemeral** (like `repo-map.md`), not committed-derived (like `contracts-index.md`), so no CI stale-derived gate is needed. | Standard Stack / Pitfall 3 | If the milestone wants it committed+gated, add a `!.memory/derived/pointer-index.json` negation + a stale-derived CI leg. D-16-02 says "gitignored", so this is aligned. |
| A3 | Word-boundaried slug matching (not bare substring) is the right false-positive guard; `kind:"path"` hits outrank `kind:"slug"` hits. | Pattern 2 | Over-strict matching could miss a legitimate prose reference; the `kind` tag lets the UI show both tiers, so risk is low. |
| A4 | Wiring the generator into SessionStart is in-scope (per CONTEXT "Integration Points") and therefore an emit round-trip is required. | Pitfall 3 | If the phase scopes wiring out, the emit round-trip is unnecessary; confirm during planning whether SC2 requires SessionStart wiring or just a runnable generator. |

## Open Questions

1. **Where does the progress-stamp writer live?**
   - What we know: `/checkpoint` writes `updated: "YYYY-MM-DD"` quoted; no Python callable does this today.
   - What's unclear: whether to add the helper in `tools/memory_ui` (tool-local) or a shared location.
   - Recommendation: put it in `tools/memory_ui` (it is a UI write action), round-trip frontmatter via `parse_frontmatter` and write a quoted-date scalar; keep it out of `inject.py`/`assemble()` (read path stays clock-free).

2. **Inline-regenerate vs. read-cached pointer-index on the orphan check?**
   - What we know: the scan is cheap (text grep over a bounded root set).
   - What's unclear: whether SessionStart-regen freshness is sufficient.
   - Recommendation: regenerate inline before the orphan check for correctness (Pitfall 4); it is fast and avoids stale-index false negatives.

3. **Does SC2 require SessionStart wiring, or just a runnable generator?**
   - What we know: CONTEXT "Integration Points" says wire it into the regen set; ROADMAP SC2 only says "generated, not hand-maintained".
   - Recommendation: wire it (matches curator/`/refresh-memory` posture), and budget for the emit round-trip; if the planner wants to minimize blast radius, a runnable `python -m tools.memory_regen.pointer_index` + `/refresh-memory` mention may satisfy SC2 without touching `session-inject.ts`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.11+ (`http.server`, `json`, `pathlib`, `hashlib`, `re`) | The tool + generator | ✓ | ≥3.11 (repo pins `requires-python=">=3.11"`) | — (stdlib) |
| `uv` workspace | New member enrollment | ✓ | 0.11.x (CLAUDE.md) | — |
| A web browser | Viewing the page | ✓ (developer-provided) | any | Page is plain HTML; `curl` the JSON endpoints for headless verification |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** none — zero external packages by design.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.x (`pytest>=8.4,<9`) + syrupy 5.2.0 (snapshot) `[VERIFIED: root pyproject.toml]` |
| Config file | root `pyproject.toml` (`[tool.pytest.ini_options]`, `testpaths=["libs/python","tools"]`) |
| Quick run command | `uv run pytest tools/memory_ui tools/memory_regen/tests/test_pointer_index_determinism.py -x` |
| Full suite command | `uv run pytest` (non-example suite) |

### Phase Requirements → Test Map
| Req ID | Behavior (Success Criterion) | Test Type | Automated Command | File Exists? |
|--------|------------------------------|-----------|-------------------|-------------|
| MEM2-07 SC1 | Tool lists state + agreements | unit (route fn over tmp dirs) | `uv run pytest tools/memory_ui/tests/test_routes.py::test_list_items -x` | ❌ Wave 0 |
| MEM2-07 SC1 | View one item body | unit | `...::test_view_item -x` | ❌ Wave 0 |
| MEM2-07 SC1 | Edit agreement → delegates to `tools.agree.write` (no direct write) | unit | `...::test_edit_calls_agree_writer -x` | ❌ Wave 0 |
| MEM2-07 SC1 | Add refuses blank `--because` (anti-invent) | unit | `...::test_add_blank_because_refuses -x` | ❌ Wave 0 |
| MEM2-07 SC1 | Retire flips `status: retired` in place (never deletes) | unit | `...::test_retire_flips_in_place -x` | ❌ Wave 0 |
| MEM2-07 SC1 | Progress save refreshes quoted `updated:` stamp, body preserved | unit | `...::test_progress_save_stamps_quoted_date -x` | ❌ Wave 0 |
| MEM2-07 SC1 | Server binds `127.0.0.1` only (never `0.0.0.0`) | unit/smoke | `...::test_binds_localhost_only -x` | ❌ Wave 0 |
| MEM2-07 SC2 | Pointer-index build is deterministic (render twice byte-identical) | unit | `uv run pytest tools/memory_regen/tests/test_pointer_index_determinism.py::test_render_twice_is_byte_identical -x` | ❌ Wave 0 |
| MEM2-07 SC2 | write→hash→delete→regenerate byte-identical (NOT git diff) | unit | `...::test_write_delete_regenerate_is_byte_identical -x` | ❌ Wave 0 |
| MEM2-07 SC2 | `.md` twin carries DERIVED header; no timestamp/float | unit | `...::test_derived_header_and_no_timestamp -x` | ❌ Wave 0 |
| MEM2-07 SC2 | Committed syrupy snapshot over tmp fixture | snapshot | `...::test_render_matches_committed_snapshot` | ❌ Wave 0 |
| MEM2-07 SC2 | Scanner excludes `.memory/derived/`; word-boundaried slug (no `plan`→`planner`) | unit | `...::test_no_self_reference_and_no_false_positive -x` | ❌ Wave 0 |
| MEM2-07 SC3 | Retire with referrers returns confirm-required (409/orphans) and does NOT write | unit | `tools/memory_ui/tests/test_referential_integrity.py::test_orphan_blocks_without_confirm -x` | ❌ Wave 0 |
| MEM2-07 SC3 | Confirmed retire proceeds via `tools.agree.write`; referrers untouched | unit | `...::test_confirmed_retire_proceeds_and_leaves_docs_untouched -x` | ❌ Wave 0 |
| MEM2-07 SC3 | Referrer list is `file:line` accurate against a tmp docs fixture | unit | `...::test_referrer_file_line_accuracy -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tools/memory_ui tools/memory_regen/tests/test_pointer_index_determinism.py -x`
- **Per wave merge:** `uv run pytest` (non-example suite) + `test_inject_determinism` if `inject.py`/`session-inject.ts` were touched.
- **Phase gate:** Full non-example suite green + (if wired) emit-drift gate clean before `/gsd:verify-work`.

### Wave 0 Gaps
- [ ] `tools/memory_ui/tests/conftest.py` — sys.path wiring (parents[3]) + re-export `tmp_agreements_tree`.
- [ ] `tools/memory_ui/tests/test_routes.py` — list/view/edit/add/retire/progress-save + localhost-bind.
- [ ] `tools/memory_ui/tests/test_referential_integrity.py` — orphan surface-and-confirm.
- [ ] `tools/memory_regen/tests/test_pointer_index_determinism.py` — clone of `test_repo_map_determinism.py`.
- [ ] `tools/memory_regen/tests/__snapshots__/test_pointer_index.ambr` — committed syrupy reference.
- [ ] Tmp docs/harness fixture with known `.memory/...` path + agreement-slug references (for `file:line` assertions).
- Framework install: none — pytest/syrupy already resolved in the workspace.

## Security Domain

> `security_enforcement` assumed enabled (absent in config). This is a localhost single-user tool; the attack surface is deliberately minimized structurally.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | By design there is no auth surface — the `127.0.0.1` bind is the boundary (D-16-01). Never bind `0.0.0.0`. |
| V3 Session Management | no | No sessions/cookies; single-user local process. |
| V4 Access Control | partial | Slug/path inputs confined via `tools.agree.write._target_for` semantics (no `_`-prefix, no path escape, `relative_to` check). |
| V5 Input Validation | yes | Validate slug against `^[a-z0-9]+(?:-[a-z0-9]+)*$`; validate item path params stay within `.memory/state`/`.memory/agreements` via `resolve().relative_to(base)`; reject traversal. |
| V6 Cryptography | no | No secrets/crypto; agreements/state must never contain secrets (existing rule) — do not add any. |
| V12/V13 (files/API) | yes | Serve only the inlined page + JSON; never serve arbitrary filesystem paths; POST bodies size-bounded and JSON-parsed with the stdlib. |

### Known Threat Patterns for a localhost stdlib HTTP tool
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via item/slug param (`../../contracts/x`) | Tampering/Elevation | Reuse `_target_for` confinement (`resolve().relative_to(base)`); reject on failure. `[VERIFIED: tools/agree/write.py:33-44]` |
| Binding beyond loopback exposes the tool on the network | Info Disclosure/Elevation | Hardcode `("127.0.0.1", port)`; assert in tests; never accept a `--host` flag. |
| DNS-rebinding / cross-origin POST to the local server | Tampering | For a local single-user tool the risk is low; optionally check `Host` header is `127.0.0.1[:port]`/`localhost` and reject others. Flag as discretion. |
| Agreement written without user feedback (fabricated `--because`) | Repudiation | `tools.agree.write.add` refuses blank `because` (exit 3); UI passes a required field verbatim, never a default. |
| Auto-mutating constitution/source planes | Elevation | Forbidden (D-16-03); UI never writes docs/skills/`inject.py`. |

## Sources

### Primary (HIGH confidence)
- `tools/memory_regen/repo_map.py`, `contracts_index.py`, `inject.py` — DERIVED-generator template, header/render/write quartet, injected-dir idiom, no-wall-clock invariant (read in-session).
- `tools/memory_regen/tests/test_repo_map_determinism.py`, `tests/conftest.py` — the determinism test to clone + fixture wiring.
- `tools/agree/write.py`, `tools/agree/tests/test_agree_refusal.py` — `add`/`retire` signatures, `AgreementRefused`, anti-invent `--because` guard, slug/path confinement, flip-in-place retire.
- `tools/harness_lint/agreements.py`, `frontmatter.py`, `tests/conftest.py` (`tmp_agreements_tree`) — shared parsers + shared test corpus.
- `harness/commands/checkpoint.md` — quoted `updated:` stamp write semantics.
- `harness/plugins/session-inject.ts` — SessionStart regen loop (where to wire the generator; emit round-trip implication).
- `.memory/README.md`, `.memory/agreements/README.md`, `.gitignore` (17–26) — four-plane model, tier contract (memory_regen never writes agreements), derived-gitignore + `contracts-index.md` negation.
- `pyproject.toml` (root), `tools/agree/pyproject.toml`, `tools/memory_regen/pyproject.toml` — workspace member layout + pytest config.
- `.planning/{REQUIREMENTS,ROADMAP}.md`, `16-CONTEXT.md` — MEM2-07, SC1–SC3, locked decisions.
- Local `python3` import check — `http.server` stdlib availability.

### Secondary / Tertiary
- None required — all findings are grounded in in-repo code and committed contracts; no WebSearch was needed for this phase.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — stdlib-only + in-repo modules read directly with exact signatures.
- Architecture: HIGH — every pattern is a clone of an existing, tested precedent.
- Pitfalls: HIGH — derived from the Phase-2/15 determinism + emit-drift history and the read tier contracts.
- One open item (A1/Question 1): the progress-stamp writer has no existing callable — flagged for the planner.

**Research date:** 2026-07-18
**Valid until:** 2026-08-17 (stable — all internal precedents; re-verify only if `tools.agree.write` or the derived-plane contract changes).
