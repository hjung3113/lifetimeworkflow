# Phase 16: Local Memory Web UI (v2.1 E) - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-18
**Phase:** 16-local-memory-web-ui-v2-1-e
**Mode:** `--auto` — all gray areas auto-selected; recommended (first) option chosen for each, no interactive prompts.
**Areas discussed:** Web tool runtime & stack, Pointer-index source & location, Edit/retire referential integrity, Write path & editable items

---

## Web tool runtime & stack (GA1)

| Option | Description | Selected |
|--------|-------------|----------|
| Python stdlib `http.server` + single inlined HTML/JS, localhost-bound | Zero new deps; matches `tools/*` uv-workspace convention; localhost bind = structural no-network/no-auth | ✓ |
| Node / opencode plugin surface | Adds a second toolchain for one local page | |
| Static HTML + separate CLI (no server) | No live edit round-trip; clumsier UX | |

**Auto-selection:** Option 1 (recommended). → D-16-01. New member `tools/memory_ui/`.
**Notes:** Never bind `0.0.0.0`; localhost is the security boundary. No Flask/FastAPI.

---

## Pointer-index source & location (GA2)

| Option | Description | Selected |
|--------|-------------|----------|
| DERIVED reference scanner → `.memory/derived/pointer-index.{json,md}`, clones `repo_map.py` | Generated every session, gitignored, `DERIVED` header, regenerate-not-git-diff test | ✓ |
| Hand-maintained index file | Violates derived-plane rule; drifts | |
| Live git-grep per request | No persistent index; slower; no "what points here" cache for UI | |

**Auto-selection:** Option 1 (recommended). → D-16-02. Generator `tools/memory_regen/pointer_index.py`.
**Notes:** Pointer = `.memory/...` path string or agreement slug across roots `docs/`, `harness/`, `inject.py`, `.memory/README.md`, `AGENTS.md`. Reads agreements, writes only `derived/` (never writes agreements — tier contract). No wall-clock in generator.

---

## Edit/retire referential integrity (GA3)

| Option | Description | Selected |
|--------|-------------|----------|
| Surface-and-confirm — detect orphaning, block behind explicit confirm, list referrers | Makes the break visible & deliberate; never mutates external planes | ✓ |
| Auto-rewrite referrers to keep pointers valid | A hygiene UI mutating constitution/source planes — unacceptable blast radius | |
| Warn-only (no block) | Weaker than SC3's "surfaced and reconciled" | |

**Auto-selection:** Option 1 (recommended). → D-16-03.
**Notes:** Shows "N references point here; retire/edit will orphan them" + `file:line` list; explicit confirm required. Tool never performs the cross-file rewrite.

---

## Write path & editable items (GA4)

| Option | Description | Selected |
|--------|-------------|----------|
| Reuse existing writers (`tools.agree.write` for agreements; `/checkpoint` path for progress stamp); pointer-index read-only | Preserves provenance-lint + YAML-safe + flip-in-place retire + determinism | ✓ |
| New unified writer in `tools/memory_ui/` | Duplicates write logic; risks provenance/determinism drift | |
| Direct file writes from the server | Bypasses provenance stamp and the anti-invent guard | |

**Auto-selection:** Option 1 (recommended). → D-16-04.
**Notes:** Retire = flip `status: retired`, never delete. UI supplies user's `--because` (must not invent). Progress `updated:` refreshed via `/checkpoint` path, no clock in the tool. Pointer-index regenerate-only.

---

## Claude's Discretion

- Frontend layout, endpoint/route naming, pointer-index JSON schema, test decomposition.
- Whether the pointer scanner shares confinement/exclusion helpers with `repo_map.py` or clones them (prefer share; fixture-parity test is the fallback).

## Deferred Ideas

- Auto-rewriting referrers to fix orphaned pointers → rejected this phase (D-16-03); revisit only as a separate gated cross-file-rename tool.
- Per-instance agreement overlays (MEM2-F1) → future milestone.
- Remote / hosted / authenticated memory UI → permanently out of scope.
- Rich structured progress editor → not needed; raw-body edit + stamp refresh suffices.
