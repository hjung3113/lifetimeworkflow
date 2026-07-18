---
phase: 16-local-memory-web-ui-v2-1-e
reviewed: 2026-07-18T02:18:35Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - tools/memory_regen/pointer_index.py
  - tools/memory_ui/routes.py
  - tools/memory_ui/server.py
  - tools/memory_ui/page.py
  - tools/memory_ui/_stamp.py
  - tools/memory_ui/__main__.py
  - harness/plugins/session-inject.ts
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 16: Code Review Report

**Reviewed:** 2026-07-18T02:18:35Z
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Phase 16's local memory-management web tool gets the security-sensitive invariants right: the
HTTP server hardcodes a `127.0.0.1` bind with no host override (`tools/memory_ui/server.py`),
agreement writes are delegated to the sanctioned `tools.agree.write` module with a verbatim
user-supplied `because` (no fabricated provenance), the retire path is a real surface-and-confirm
gate that returns `409 {"orphans": [...]}` and never rewrites referrer files, `pointer_index.py`
is deterministic (no wall-clock/random) and writes only under the gitignored `.memory/derived/`
plane, path/slug inputs are confined via `_confine`/`_target_for`, the POST body is size-bounded
before JSON parsing, and `page.py` has no external network reference. These were verified by
reading the code and, for the confine/orphan/determinism claims, by cross-referencing the existing
test suite (`tools/memory_ui/tests/*`, `tools/memory_regen/tests/test_pointer_index.py`).

However, there is one confirmed BLOCKER: the state-file edit/save round trip corrupts
`.memory/state/*.md` by duplicating the YAML frontmatter block on every save, because
`view_item` returns the **whole file** (frontmatter + body) to the UI, but `save_progress` /
`_stamp.stamp_progress` treat the submitted text as **body-only** and prepend a freshly generated
frontmatter block in front of it. This was reproduced directly against the shipped code (see
CR-01) — a normal "click Edit, click Save" cycle in the actual browser flow (`page.py`'s
`editState`) corrupts the file, and repeating the cycle nests the corruption further each time.

## Critical Issues

### CR-01: Edit/save round trip duplicates and nests YAML frontmatter, corrupting state files

**File:** `tools/memory_ui/routes.py:89-95` (`view_item`) and `tools/memory_ui/routes.py:201-213`
(`save_progress`), consumed by `tools/memory_ui/page.py:426-432` (`renderDetail`, GET body) and
`tools/memory_ui/page.py:474-508` (`editState`, POST body), landing in
`tools/memory_ui/_stamp.py:44-68` (`stamp_progress`).

**Issue:** `view_item` returns `target.read_bytes()` — the **entire file**, frontmatter fence
included — as the "body" for a state item:

```python
# routes.py:89-95
def view_item(item_id: str, *, state_dir: Path, agreements_dir: Path) -> tuple:
    if item_id in _STATE_ITEMS:
        target = _confine(item_id, Path(state_dir))
        if target is None or not target.is_file():
            return 404, dict(_JSON), _json_body({"error": f"not found: {item_id}"})
        return 200, dict(_MD), target.read_bytes()
```

`page.py`'s `editState(id, bodyText)` (`renderDetail` fetches this via `/api/item` and passes it
straight through) loads that whole-file text verbatim into the `<textarea>`, and `Save changes`
POSTs `ta.value` unmodified as `body`:

```javascript
// page.py:489-494
actions.append(button("Save changes", "primary", async () => {
    const res = await api("/api/progress/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ item: id, body: ta.value }),
```

`save_progress` forwards that whole-file text to `_stamp.stamp_progress` as `body_text`, and
`stamp_progress` treats it as pure post-frontmatter body, prepending a brand-new frontmatter block
in front of it:

```python
# _stamp.py:60-67
target = Path(path)
frontmatter, _old_body = parse_frontmatter(target.read_text(encoding="utf-8"))
frontmatter["updated"] = DoubleQuotedScalarString(today)
target.write_text(
    f"---\n{_dump_frontmatter(frontmatter)}---\n\n{body_text}",
    ...
)
```

Because `body_text` already contains the file's own original `---...---` frontmatter fence, the
write produces a file with the frontmatter duplicated. Reproduced directly against the shipped
code:

```
$ uv run python -c "... routes.view_item(...) -> routes.save_progress(...) ..."
--- file on disk after ONE save round-trip ---
---
updated: "2026-07-18"
owner: harness
---

---
updated: "2026-07-16"
owner: "harness"
---

# Progress

tiny.
```

A second edit/save cycle (which is exactly what happens if the user clicks Edit again — the GET
now returns the already-corrupted file — then Save) nests it a third level deep, and so on. This
is a data-corruption bug reachable through the tool's normal, intended UI flow (Edit → Save),
not an edge case. `test_progress_save_stamps_quoted_date` (`tools/memory_ui/tests/test_routes.py`)
does not catch it because it calls `save_progress` directly with a hand-crafted body-only string,
never exercising the `view_item → save_progress` round trip the real UI performs.

**Fix:** `view_item` must strip the frontmatter fence before returning a state file's body (or
`save_progress`/`stamp_progress` must strip a leading frontmatter fence from the incoming
`body_text` before treating it as the body). The cleanest fix keeps `parse_frontmatter` as the
single source of truth for the split, e.g.:

```python
# routes.py — view_item, state branch
if item_id in _STATE_ITEMS:
    target = _confine(item_id, Path(state_dir))
    if target is None or not target.is_file():
        return 404, dict(_JSON), _json_body({"error": f"not found: {item_id}"})
    from tools.harness_lint import parse_frontmatter
    _fm, body = parse_frontmatter(target.read_text(encoding="utf-8"))
    return 200, dict(_MD), body.encode("utf-8")
```

or, symmetrically, have `stamp_progress` defensively re-split `body_text` with
`parse_frontmatter` and discard any embedded frontmatter before writing. Either fix should be
covered by a new test that performs the exact `view_item` → (unmodified) → `save_progress` round
trip and asserts the file has exactly one frontmatter block afterward.

## Warnings

### WR-01: `/api/pointers` ignores the injected/mocked plane dirs — always scans the real repo

**File:** `tools/memory_ui/server.py:120-128`

**Issue:** Every other route dispatch in `do_GET`/`do_POST` reads the module-level `STATE_DIR` /
`AGREEMENTS_DIR` / `DERIVED_DIR` globals (which tests monkeypatch to a tmp corpus), but the
`/api/pointers` handler hardcodes `base_dir=_REPO_ROOT` and
`scan_roots=pointer_index._default_scan_roots()` regardless of any monkeypatch:

```python
if path == "/api/pointers":
    item = query.get("item", [""])[0]
    referrers = routes.pointer_lookup(
        _item_key(item),
        base_dir=_REPO_ROOT,
        scan_roots=pointer_index._default_scan_roots(),
    )
```

In production this happens to be correct (base dir == repo root), but it means this endpoint is
untestable against a synthetic corpus the way every other route is, and any future refactor that
threads a different `_REPO_ROOT`-like override (e.g. for a monorepo submodule use) will silently
skip this endpoint. It is also the one route not exercised by `tools/memory_ui/tests/test_server.py`
at all.

**Fix:** Thread the same pattern the other handlers use — read module-level `STATE_DIR`/
`AGREEMENTS_DIR`-equivalent base/scan-root globals so tests can monkeypatch them, e.g. expose a
`BASE_DIR = _REPO_ROOT` and `SCAN_ROOTS = None` module global and read those in the handler
instead of the hardcoded names.

### WR-02: Missing `Content-Length` treated as an empty (but valid) body — no defense against unread socket data

**File:** `tools/memory_ui/server.py:74-89`

**Issue:** `_read_json_body` treats an absent/zero `Content-Length` as `{}` without ever touching
`self.rfile`:

```python
length = int(self.headers.get("Content-Length") or 0)
if length <= 0:
    return {}
```

For `http.server`'s synchronous per-connection model this is usually benign for this tool's own
JS client (which always sets `Content-Length` via `fetch`), but any POST that omits
`Content-Length` (e.g. chunked transfer-encoding, or a body sent by a non-JS client/curl without
the header) will have its body bytes left unread on the socket, which can corrupt the next
request read on a keep-alive connection. Combined with `ThreadingHTTPServer`'s use of persistent
connections by default, this is a latent protocol-desync bug, not just an academic one.

**Fix:** Reject requests with a POST body but no/invalid `Content-Length` (e.g., `Transfer-Encoding:
chunked`) with `411 Length Required`, or explicitly check `self.headers.get("Transfer-Encoding")`
and refuse chunked bodies outright, rather than silently treating them as empty.

### WR-03: `view_item`/detail panel exposes and edits raw frontmatter to the user, compounding CR-01's blast radius

**File:** `tools/memory_ui/page.py:408-439`, `tools/memory_ui/page.py:474-508`

**Issue:** Independent of CR-01's corruption bug, the detail panel's read-only `pre.body-view`
(line 428) and the edit textarea (line 480) both display the raw frontmatter fence to the user as
if it were prose body content. Even after CR-01 is fixed, showing `---\nupdated: "..."\n---`
inside a text area labelled "edit the body" is confusing and invites the user to hand-edit
provenance-adjacent metadata that the tool is supposed to own exclusively via `_stamp.py`.

**Fix:** Once `view_item` is fixed to return body-only content (see CR-01), this resolves itself
for state files; keep the raw-file view for agreements (read-only, never edited) as-is.

## Info

### IN-01: `add_agreement`'s unused `derived_dir` parameter

**File:** `tools/memory_ui/routes.py:106-124`

**Issue:** `derived_dir` is accepted and immediately discarded (`_ = derived_dir`) "for signature
symmetry" with `retire_agreement`. This is a documented, deliberate no-op, but it is dead
parameter surface that a future reader may assume is load-bearing (e.g., that it participates in
slug-collision detection, as the docstring hints at "future").

**Fix:** Either wire it into an actual slug-collision-against-pointer-index check now, or drop the
parameter until it is needed — a documented-but-unused parameter is a minor foot-gun for future
maintainers.

### IN-02: `pointer_index.build_index` is O(files × lines × items) with a per-line dict iteration

**File:** `tools/memory_regen/pointer_index.py:150-163`

**Issue:** For every line of every scanned file, the inner loop iterates every memory item
(`path_by_item.items()`) and runs a regex search for agreement items. This is a performance
consideration (explicitly out of v1 scope per the review charter) rather than a bug, but worth
flagging since the item count grows unboundedly with the number of agreements and the scan-root
file set is not tiny (`docs/`, `harness/` recursively).

**Fix:** Not required for v1; if agreement/referrer counts grow, consider building one combined
regex (path-string + slug alternation) per file pass instead of the current per-item nested loop.

### IN-03: `main()` in `pointer_index.py` accepts and discards `argv`

**File:** `tools/memory_regen/pointer_index.py:226-235`

**Issue:** `main(argv: list[str] | None = None)` reads `sys.argv[1:]` into `argv` and marks it
`# noqa: F841 (reserved for future flags)`, but never uses it — the CLI silently ignores any
arguments passed to `python -m tools.memory_regen.pointer_index`. Not a bug (there are no flags to
support yet), but a caller passing e.g. `--help` gets no diagnostic and no argparse-standard
`unrecognized arguments` error — it just silently regenerates the index.

**Fix:** Either wire a minimal `argparse.ArgumentParser()` that rejects unknown args, or drop the
unused parameter entirely until a real flag is added.

---

_Reviewed: 2026-07-18T02:18:35Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
