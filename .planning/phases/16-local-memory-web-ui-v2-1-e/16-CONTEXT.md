# Phase 16: Local Memory Web UI (v2.1 E) - Context

**Gathered:** 2026-07-18
**Status:** Ready for planning
**Mode:** `--auto` (all gray areas auto-resolved to the recommended option; every choice logged in `16-DISCUSSION-LOG.md`)

<domain>
## Phase Boundary

The MEM2 chain (Phases 12–15) built the memory channels — the committed PROCESS agreements tier
(`.memory/agreements/*`), the STATE progress files (`.memory/state/{activeContext,progress}.md`), the
`inject.py` SessionStart surface, and the `/agree` write path. Phase 16 ships the **management
surface** over those already-finished files: a lightweight **local** (no external network, no auth)
web tool to **view / edit / retire** memory items, made **pointer-aware** by a machine-built,
DERIVED pointer-index that answers "what points to this item" and keeps references consistent so a
hand-edit can no longer silently orphan a pointer.

**This is a read-mostly hygiene surface over existing writers, NOT a new memory subsystem.** The
agreements write/retire path already exists (`tools/agree/write.py`), the progress `updated:` stamp
already exists (`/checkpoint`), and the injector already reads both. Phase 16 does not re-implement
any of that — it surfaces them in a browser and adds the pointer-index + referential-integrity
guard that MEM2-04 explicitly deferred here (14-CONTEXT.md `<deferred>`).

**In scope:** local web tool (list/view/edit/retire progress + agreements); a DERIVED pointer-index
generator (`what points to this item`); referential-integrity surfacing on edit/retire (orphan
detection + confirm-before-break).
**Out of scope:** any network/remote/hosted/auth surface (REQUIREMENTS "Out of Scope"); promoting
agreements into the constitution plane; per-instance agreement overlays (MEM2-F1, deferred);
auto-rewriting external docs to fix pointers (surface + confirm only — see D-16-03).

</domain>

<decisions>
## Implementation Decisions

### Web tool runtime & stack (GA1)

- **D-16-01:** **Python stdlib `http.server` bound to `127.0.0.1`, serving a single inlined
  HTML/JS page — zero new dependencies.** *(auto-selected: recommended)* Rationale: every existing
  harness tool is a Python `tools/*` module invoked `python -m tools.X` under the uv workspace; a
  Node/opencode surface would add a second toolchain for one local page. Binding localhost with no
  auth route *is* the "no external network, no auth surface" constraint met structurally, not by
  policy. The frontend is one self-contained page (inlined CSS/JS, no CDN, no build step) so "local
  only" holds with nothing to fetch. New workspace member **`tools/memory_ui/`** (auto-enrolled by
  the existing `tools/*` glob — precedent: `tools/agree/` in 14-CONTEXT.md D-19, 4 deterministic
  lockfile lines, zero resolution).
  - **Never bind `0.0.0.0`.** Localhost only; the bind address is the security boundary.
  - No `uv add` of Flask/FastAPI — stdlib `http.server` / `BaseHTTPRequestHandler` is sufficient for
    a single-user local tool and keeps the no-dep posture.

### Pointer-index — what counts as a pointer, and where it lives (GA2)

- **D-16-02:** **A DERIVED reference scanner: `tools/memory_regen/pointer_index.py` → gitignored
  `.memory/derived/pointer-index.{json,md}`, cloning `repo_map.py`'s generator shape.**
  *(auto-selected: recommended)* A "pointer to a memory item" = any occurrence, across a fixed set of
  scan roots, of (a) a `.memory/...` file path string, or (b) an agreement **slug**. Scan roots:
  `docs/`, `harness/` (skills/commands/agents), `tools/memory_regen/inject.py`, `.memory/README.md`,
  `AGENTS.md`. Output keyed by memory-item → list of `{file, line, kind}` referrers.
  - **Lives in the DERIVED plane** (`.memory/derived/`, gitignored, regenerated every SessionStart —
    `.memory/README.md:14`, `:33-42`). It is **generated, never hand-maintained** (ROADMAP SC2). The
    UI reads the JSON; the `.md` twin carries the `DERIVED — do not hand-edit` header like repo-map.
  - **Verified by write→hash→delete→regenerate**, NOT `git diff` (the target is gitignored —
    `repo_map.py:15`, Pitfall 2). **No wall-clock / timestamp inside the generator** (determinism
    invariant shared with `repo_map.py`, `inject.py:20-22`).
  - Belongs under `tools/memory_regen/` because that package **owns** the derived plane — but note it
    must NOT write into `.memory/agreements/` (forbidden by the tier contract,
    `.memory/agreements/README.md:4-5`); it only *reads* agreements and *writes* `derived/`.

### Edit / retire referential integrity (GA3)

- **D-16-03:** **Surface-and-confirm: detect orphaning, block the destructive action behind an
  explicit confirm, and list the referrers for manual reconciliation — never silently auto-rewrite
  external docs.** *(auto-selected: recommended)* On an edit that changes a slug/path, or a retire,
  the tool queries the pointer-index: if referrers exist, it shows "N references point here; this
  edit/retire will orphan them" with the referrer file:line list, and requires an explicit confirm
  to proceed. Rationale: auto-rewriting `docs/`, `harness/skills`, or `inject.py` from a memory-UI
  action would let a hygiene tool mutate the constitution/source planes — unacceptable blast radius.
  The tool's job is to make the break **visible and deliberate** (ROADMAP SC3: "surfaced and
  reconciled … can no longer silently break references"), not to perform the cross-file rewrite.

### Write path & which items are editable (GA4)

- **D-16-04:** **Reuse the existing writers; add no new write path.** *(auto-selected: recommended)*
  - **Agreements:** add/retire go through `tools.agree.write` (`add` / `retire`) so provenance
    stamping, the YAML-safe serialization of `--because` (14-CONTEXT.md D-15), and the flip-in-place
    retire (D-09) are preserved. **Retire = flip `status: retired`, never delete** (§7b). The UI
    supplies the `--because` from a required field — it must NOT invent one (the anti-invent guard,
    D-03, still governs).
  - **Progress state** (`activeContext.md` / `progress.md`): editable as raw markdown body; on save,
    refresh the `updated:` stamp via the `/checkpoint` write path (MEM2-05) rather than writing a
    wall-clock inside the tool. `assemble()` must stay deterministic — the tool never introduces a
    clock into the read path.
  - **Pointer-index:** DERIVED and **read-only** in the UI — regenerate, never hand-edit (D-16-02).

### Claude's Discretion

- Frontend layout, endpoint/route naming, JSON schema of the pointer-index, and test decomposition
  within the shapes fixed above.
- Whether the pointer scanner shares confinement/exclusion helpers with `repo_map.py` or clones them
  (prefer share-not-re-derive per the D-05/D-18 precedent, but a fixture-parity test is an acceptable
  fallback if extraction proves invasive).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Authoritative design source
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §7d "NEW requirement — a simple local web UI to manage
  memory (referential integrity)" (lines 299–306) — **the authoritative statement of MEM2-07**:
  pointer-aware UX, "what points to this item", consistency on edit/retire, local/no-network/no-auth,
  operates on committed files + a pointer index treated as derived.
- `.planning/MEMORY-UPGRADE-PROPOSAL.md` §7a (tight progress shape) and §7b (agreements entry shape,
  retire = status flip) — the item shapes the UI edits.
- `.planning/REQUIREMENTS.md` — MEM2-07 (line 34) + "Out of Scope" table (remote/hosted/auth UI
  explicitly excluded).
- `.planning/ROADMAP.md` "### Phase 16" — the three Success Criteria this phase is verified against.

### Ratified decisions
- `docs/adr/0006-process-memory-channel-and-provenance-reframe.md` — the four-plane model; DERIVED
  plane is gitignored/regenerated, CONSTITUTION is gated. The pointer-index is DERIVED.
- `docs/adr/0007-constitution-gate-dev-enforce-decoupling.md` — `HARNESS_DEV_BYPASS`; relevant if any
  step must land a constitution-plane write during this phase.

### Channel + plane contracts
- `.memory/README.md` §"(2) DERIVED plane" (lines 33–42) — DERIVED = machine-owned, gitignored,
  regenerated, `DERIVED — do not hand-edit` header, "delete + rerun the generator". Binds D-16-02.
- `.memory/agreements/README.md` — the agreements tier contract; **`tools/memory_regen` must never
  write agreements** (lines 4–5). The pointer generator reads agreements, writes only `derived/`.
- `.memory/state/activeContext.md`, `.memory/state/progress.md` — the `updated:` stamp shape and the
  tight progress content the UI edits.

### Code precedents to clone (do not invent new shapes)
- `tools/memory_regen/repo_map.py` — the DERIVED generator template: `_REPO_ROOT`/`DERIVED_DIR`,
  `DERIVED_HEADER`, `render`/`write`, write→hash→delete→regenerate determinism test, no timestamp.
  The pointer-index generator clones this.
- `tools/memory_regen/contracts_index.py` — a second derived-index precedent (`index_rows`/`render`/
  `write`) if a tabular `.md` twin is wanted.
- `tools/memory_regen/inject.py` — the agreements read filter (`iter_agreement_files`,
  `_agreements_block`) and the determinism/no-wall-clock invariants the read path must preserve.
- `tools/agree/write.py` — the `add` / `retire` writers the UI calls (provenance + YAML-safe + flip-
  in-place retire). Do not bypass these.
- `tools/harness_lint/agreements.py` — `iter_agreement_files` / `load_agreement`; the shared agreement
  parser to reuse for listing/parsing, not re-roll.
- `tools/agree/`, `tools/memory_regen/pyproject.toml` — the workspace-member layout `tools/memory_ui/`
  follows.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/agree/write.py::add` / `::retire` — the sanctioned agreement write/retire path; the UI is a
  frontend over these, not a new writer (D-16-04).
- `tools/harness_lint/agreements.py::iter_agreement_files` / `::load_agreement` — parse/list
  agreements for the view; already fail-closed on `_`-prefix / README / status.
- `tools/memory_regen/repo_map.py` + `contracts_index.py` — complete DERIVED-generator templates
  (header, render/write, gitignore-aware determinism test) the pointer-index clones (D-16-02).
- `tools/memory_regen/inject.py` — reads both planes today; the source of truth for "how a memory
  item is located and parsed" and the determinism constraints.

### Established Patterns
- **DERIVED plane = generated, gitignored, never hand-edited, verified by regenerate-not-git-diff.**
  The pointer-index MUST follow this (`.memory/README.md:33-42`, `repo_map.py:15`).
- **Reuse existing writers; single rule, reused.** Agreements only via `tools.agree.write`; progress
  `updated:` only via the `/checkpoint` path — mirrors the D-05/normalize.core "one rule, reused"
  discipline and keeps provenance-lint + determinism invariants intact.
- **New tool = new `tools/*` workspace member**, auto-enrolled by the `tools/*` glob (precedent:
  `tools/agree/`, 14-CONTEXT.md D-19). Cheap and deterministic.
- **Localhost bind is the security boundary** — no auth code, just never bind beyond `127.0.0.1`.

### Integration Points
- `tools/memory_ui/` (new) ← serves the page + calls `tools.agree.write` and the `/checkpoint` write
  path; reads `.memory/derived/pointer-index.json`.
- `tools/memory_regen/pointer_index.py` (new) ← writes `.memory/derived/pointer-index.{json,md}`;
  wire into the SessionStart derived-regen alongside repo-map + contracts-index.
- `.gitignore` — `.memory/derived/` is already ignored; the new pointer-index files inherit that (do
  NOT add tracked files under `derived/`).
- Touching `inject.py`'s read path (if needed) means **re-verifying Phase 13's byte-identity
  determinism test and the no-wall-clock static gate** — both live, must stay green.

### ⚠ Agents must never author `.memory/agreements/*` content
Carried from Phase 14: agreements are written **only** on explicit user feedback. The active set is
legitimately **empty** today. Exercise the UI/generator against `tmp_path` fixtures, never by writing
real agreements to "test" it. The UI's write field supplies the user's `--because`; it must not
fabricate one.

### ⚠ Verify pointer-index with regenerate, not `git diff`
`.memory/derived/` is gitignored — a `git diff --exit-code` gate is blind to it (this is the same
class of bug as the carried Phase-15 CR-01 emit-drift finding). Test the generator by
write→hash→delete→regenerate→compare-hash, exactly as `repo_map.py` documents.

</code_context>

<specifics>
## Specific Ideas

- The pointer-index `.md` twin should carry the standard `DERIVED — do not hand-edit
  (tools/memory_regen/pointer_index.py)` header so it reads like repo-map / contracts-index.
- The referential-integrity prompt is a **teaching surface**: name the item, count the referrers, and
  list them as `file:line` so the user can reconcile by hand — mirror the `REFUSED:`/`REVIEW:` tone
  the harness uses elsewhere.
- Keep the frontend one file, no framework, no CDN — "local only" must be literally true (nothing to
  fetch), not just policy.

</specifics>

<deferred>
## Deferred Ideas

- **Auto-rewriting referrers (docs/skills/inject.py) to fix orphaned pointers** → rejected for this
  phase (D-16-03): a hygiene UI must not mutate the constitution/source planes. Surface + confirm
  only. Revisit only with a separate, gated cross-file-rename tool if it ever becomes a hard need.
- **Per-instance agreement overlays** (`examples/*`, MEM2-F1) → deferred to a future milestone (§6
  Q3 MVP is one global core set).
- **Remote / hosted / authenticated memory UI** → permanently out of scope (REQUIREMENTS "Out of
  Scope"). MEM2-07 is local-only by definition.
- **Editing progress via a rich structured editor** (beyond raw-markdown-body + stamp refresh) → not
  needed for the hygiene goal; raw body edit through the `/checkpoint` path suffices.

</deferred>

---

*Phase: 16-local-memory-web-ui-v2-1-e*
*Context gathered: 2026-07-18*
