# `tools/memory_ui` — Local Memory Web UI

A lightweight, **local-only** tool to view, edit, and retire the repo's memory items
(progress state + per-guideline agreements) with **pointer-aware referential integrity**.
It surfaces "what points to this item" and refuses to let an edit or retire silently orphan a
reference. Delivers **MEM2-07** (Milestone v2.1, Phase 16).

Zero third-party dependencies — Python standard library only (`http.server`).

## Run it

```bash
uv run python -m tools.memory_ui          # serves http://127.0.0.1:8765
uv run python -m tools.memory_ui --port 9000
```

Then open the printed `http://127.0.0.1:<port>` URL in a browser. Stop with Ctrl-C.

There is deliberately **no `--host` flag**: the server binds `127.0.0.1` unconditionally. That
loopback bind *is* the access-control boundary — there is no auth surface because nothing off the
local machine can reach it.

## What it manages

| Plane | Files | Actions |
|-------|-------|---------|
| **STATE (progress)** | `.memory/state/activeContext.md`, `.memory/state/progress.md` | view, edit body, save (refreshes the `updated:` stamp) |
| **PROCESS (agreements)** | `.memory/agreements/<slug>.md` | view, add, retire (flip `status: retired`, never delete) |

The **DERIVED pointer-index** (`.memory/derived/pointer-index.json`, produced by
`tools/memory_regen/pointer_index.py`) backs the "Referrers — what points to this" panel. It is a
generated, gitignored artifact — the UI reads it and regenerates it inline before a destructive
action so the orphan check always sees fresh referrers.

## Behavior guarantees

- **Reuses the sanctioned writers.** Agreements are added/retired only through
  `tools.agree.write` — the same provenance-stamped, YAML-safe, flip-in-place path `/agree` uses.
  The UI never writes an agreement file directly.
- **Anti-invent.** Adding an agreement *requires* a "Because" field; the tool never fabricates
  provenance. A blank `--because` is refused.
- **Surface-and-confirm (never auto-rewrite).** When an edit/retire would orphan referrers, the
  tool shows a confirm dialog listing the referring `file:line`s and states plainly that it will
  **not** rewrite those files — you reconcile them by hand. It never edits `docs/`, `harness/`,
  `inject.py`, or any other referrer.
- **Deterministic derived plane.** The pointer-index generator uses no wall-clock/timestamp/random
  and writes only under `.memory/derived/` (verified by regenerate-and-hash, not `git diff` — the
  dir is gitignored). It never writes into `.memory/agreements/`.
- **No external fetch.** The page is a single self-contained HTML/JS document — no framework, no
  CDN, no web fonts, no network calls beyond the tool's own `/api/*` endpoints.

## Architecture

| File | Role |
|------|------|
| `__main__.py` | entrypoint; `--port` only; binds `127.0.0.1` |
| `server.py` | thin `ThreadingHTTPServer` + `BaseHTTPRequestHandler`; parses request (size-bounded body), delegates to routes, regenerates the pointer-index before a retire |
| `routes.py` | **pure** functions over injected `state_dir` / `agreements_dir` / `derived_dir`, each returning `(status, headers, body)` — no socket, no global state |
| `_stamp.py` | refreshes the progress `updated:` stamp (quoted ISO date), preserving sibling frontmatter keys; kept out of the `inject.assemble()` read path so that stays clock-free |
| `page.py` | the single inlined HTML/CSS/JS page |

The pure-route seam is what makes the tool testable without opening a socket or writing real
memory files — tests inject temp dirs (see `tests/`).

## HTTP endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | the inlined page |
| GET | `/api/items?show_retired=0` | list progress + agreement items |
| GET | `/api/item?id=<name>` | item body (state files return body-only, no frontmatter) |
| GET | `/api/pointers?item=<name>` | referrers for an item, from the pointer-index |
| POST | `/api/progress/save` | save a progress item's body (refreshes `updated:`) |
| POST | `/api/agreements/add` | add an agreement (requires title, slug, rule, because) |
| POST | `/api/agreements/retire` | retire an agreement; returns `409 {orphans}` unless confirmed |

## Tests

```bash
uv run pytest tools/memory_ui -q
```

Route logic, the localhost-only bind, the orphan surface-and-confirm path, the progress-stamp
idempotency (edit→save round-trip produces exactly one frontmatter block), and the bounded-body
guard are all covered against temp fixtures — no live socket, no real `.memory/agreements/` writes.

## Scope

Local only, single user, read-mostly-then-edit. Remote/hosted/authenticated memory UIs are
explicitly out of scope (see `.planning/REQUIREMENTS.md` → MEM2-07 / Out of Scope).
