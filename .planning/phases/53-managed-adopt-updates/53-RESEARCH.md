# Phase 53: Managed Adopt Updates - Research

**Researched:** 2026-08-01
**Domain:** Adoption re-run semantics (contract-first Python tooling, atomic file writes, JSON Schema drift gates)
**Confidence:** HIGH for existing-code claims (all read live); MEDIUM/LOW flagged inline for gate mechanics and one genuine cross-document conflict (see Assumptions Log / Open Questions).

## Summary

Phase 53 turns `/adopt`'s currently-one-shot apply into a re-runnable update cycle. The three
success criteria decompose cleanly onto code that already exists: `disposition()`'s total 7-step
chain (`tools/adoption_scan/destinations.py:326-366`) gets an 8th value (`update`) inserted between
its current steps 6 and 7; `apply_disposition`/`apply_manifest` (`tools/adoption_apply/apply.py:376-478`)
gain an `update` branch that reuses `_atomic_replace` (already used by `_apply_marker_merge`); and a
new `.harness/adoption/installed.json` record in the TARGET tree closes the loop so a second draft,
run from a fresh batch directory in a new session, can tell "unchanged" from "harness moved" from
"human edited".

The single highest-risk item this research surfaces is **not** technical difficulty — it is a
**direct numeric conflict** between 53-CONTEXT.md's locked decision (a brand-new sibling contract
`contracts/harness/adoption/installed.schema.json`) and the milestone-wide binding boundary in
`.planning/ROADMAP.md:230-232` ("contracts 6 ... do not increase") which explicitly spans phases
51-54, not just Phase 54's closeout. The current contract count is verified at exactly 6
(`find contracts -name '*.schema.json' | wc -l` → 6, confirmed live and independently confirmed in
`52-ADOPTION-EVIDENCE.md:71`). Adding `installed.schema.json` makes 7; if `conflicts.json` is also
schema-validated against a new file (CONTEXT.md's own wording: "schema-validated"), that is a
possible 8th. Phase 54's goal statement (`ROADMAP.md:314`) requires "closeout counts are no greater
than the milestone baseline: ... 6 contracts" with no compensating contract removal named anywhere
in Phase 54's scope (`DEBT-01` is a code-dedup task, not a contract deletion). This is flagged in
Open Questions/Assumptions Log rather than silently resolved — the planner (or a human) must decide
before contract-plane work starts: either the human confirms a transient bump is acceptable and adds
a Phase-54 compensating removal, or the "new sibling schema" decision is revisited to instead extend
`manifest.schema.json`'s own `$defs` (contradicting 53-CONTEXT.md's own stated rationale for keeping
the manifest hash untouched), or `installed.json`/`conflicts.json` are validated by a hand-written
Python shape-check instead of a `.schema.json` file (avoiding the count bump entirely while keeping
the "schema-validated" property CONTEXT.md asks for, just not via a new committed contract).

**Primary recommendation:** Implement `update` as new code (disposition chain, apply branch, CLI
wiring) exactly as 53-CONTEXT.md's Discretion section allows, but gate the constitution-plane script
(manifest enum + new schema file) behind an explicit human resolution of the contract-count conflict
above — do not let a plan silently write a 7th contract file without the human seeing this tension
first.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Disposition classification (`update` vs `conflict` vs `preserve`) | Backend / library (`tools/adoption_scan`) | — | Pure function over hashes, no I/O side effects; already the home of the other 6 values |
| Durable write of an updated file | Backend / library (`tools/adoption_apply`) | Filesystem | `_atomic_replace` already implements the exact idiom needed; no new write primitive |
| Installed-record persistence | Target filesystem (`.harness/adoption/installed.json` in the TARGET tree) | Backend library (reader/writer module) | CONTEXT.md's own locked reasoning: batch dirs are task-local and don't survive across sessions, so the target is the only durable anchor |
| Conflict reporting | Backend library, batch-local artifact (`conflicts.json`) | CLI (stderr summary) | Same confinement discipline as `inventory.json`/`plan.json`/`manifest.json` — `refuse_if_outside_root` |
| Contract schema authorship | Human (constitution plane) | Off-plane script (agent-authored, human-run) | `contract_guard.py` denies agent Write/Edit on `contracts/**` unconditionally; the repo's established pattern (Phase 52's `apply-inventory-enum.py`) is agent writes a script, human runs it with `GOLDEN_APPROVE_HUMAN=1` |
| CI/documentation surface (`adopt.md`, `brownfield-adoption` skill) | Documentation (harness source of truth under `harness/`) | Emitted `.claude/` / `.opencode/` (derived, regenerated) | NG-01: editing existing files is permitted, adding new commands/skills is not |

## Standard Stack

No new external dependencies. This phase is pure extension of already-installed, already-vetted
in-repo modules — `jsonschema` (Draft202012Validator, already imported in `cli.py:33`), `hashlib`
(stdlib), `rfc8785` (already a dependency of `tools/contract_hash/hash.py:21`). No installation
step, no Package Legitimacy Audit is required.

### Core (reused, not newly installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `jsonschema` | already pinned (see `pyproject.toml`) | Draft 2020-12 validation of `installed.json`/`conflicts.json` | Already the validator for `inventory`/`plan`/`manifest` (`cli.py:33,127-140`); the repo's own idiom is to reuse `_load_schema`/`_validate` verbatim |
| `rfc8785` | already pinned | JCS canonical-hash gate for the new/changed contract | `tools/contract_hash/hash.py:21` is the ONLY canonicalizer in the repo; never reimplement |

### Alternatives Considered
None — this phase adds no new library surface by design (NG-01, and CONTEXT.md's Claude's
Discretion section scopes new work to module placement, not new dependencies).

## Package Legitimacy Audit

Not applicable — no external packages are installed in this phase.

## Architecture Patterns

### System Architecture Diagram

```
                         ┌─────────────────────────────┐
                         │  harness checkout (source)  │
                         │  destinations.py:            │
                         │   harness_proposed_hashes()  │
                         └───────────────┬──────────────┘
                                         │ {destination: source_sha256}
                                         ▼
  target tree ──read──►  disposition(rel, target_root, proposed_sha,           ┌─ create
  (existing file          existing_sha=<from inventory>,                        ├─ preserve
   sha256, via                installed_sha=<from .harness/adoption/            ├─ conflict
   scan.build_inventory)         installed.json, NEW>)                          ├─ marker-merge
                                         │                                       ├─ derived-regenerate
                                         ▼                                       ├─ human-ratification-required
                              7-step chain (existing) + NEW step inserted        └─ update  (NEW)
                              between existing step 6 (preserve) and 7 (conflict):
                                6.5  target_hash == installed_sha AND
                                     installed_sha != proposed_sha  -> update
                                     (installed_sha is None         -> falls through,
                                      never resolves to update)
                                         │
                                         ▼
                         build_manifest()  →  manifest.json (dispositions[] with "update" rows)
                                         │
                                         ▼
                    apply_manifest()  ──dispatch──►  apply_disposition()
                       │                                  │
                       │                                  ├─ "update"  → _atomic_replace(target_path, harness_payload)
                       │                                  │              (same idiom marker-merge already uses)
                       │                                  ├─ "conflict" → write conflicts.json row (destination,
                       │                                  │                installed_sha256, target_sha256); target
                       │                                  │                file untouched; accumulate, never abort
                       │                                  └─ "create"/"marker-merge"/... → unchanged
                       │
                       ▼
        after apply: rewrite .harness/adoption/installed.json
        (content-derived only — entries whose bytes actually changed;
         a true no-op run must NOT rewrite this file at all, or a
         before/after tree-hash proof would show a phantom write)
                       │
                       ▼
        CLI exit code: 0 (clean, no conflicts) / 1 (fault/refusal, existing)
                        / 3 (NEW — one or more conflicts recorded, run still completed)
```

### Recommended Project Structure

No new top-level packages. CONTEXT.md's Claude's Discretion leaves module placement open; the
lazy/consistent choice given the existing module boundaries:

```
tools/adoption_apply/
├── apply.py            # add: "update" branch in apply_disposition; DISPOSITION_ENUM import
│                        #      grows to 7 values (imported from destinations.py, never retyped)
├── installed.py         # NEW, small: read_installed_record(target_root) / write_installed_record(...)
│                        #      — pure functions, mirrors cli.py's _load_schema/_validate reuse
├── cli.py               # _cmd_apply: read installed.json before apply, write it after,
│                        #      emit conflicts.json, map conflicts -> exit 3
└── tests/
    ├── test_installed_record.py     # NEW
    └── test_update_disposition.py   # NEW (or folded into test_atomic_apply.py / test_dispositions.py)

tools/adoption_scan/
└── destinations.py      # disposition(): new `installed_sha` kwarg + step 6.5;
                          #      DISPOSITION_ENUM tuple grows to 7 values (single source, re-exported)

contracts/harness/adoption/
├── manifest.schema.json     # EDIT: dispositionEnum gains "update" (7th value) — constitution plane
└── installed.schema.json    # NEW sibling schema — constitution plane (see conflict flagged above)
```

### Pattern 1: `update` as an inserted, not appended, chain step
**What:** `disposition()` currently returns `preserve` when `existing_sha == proposed_sha` (step 6)
and `conflict` otherwise (step 7, catch-all). The `update` value must be checked BEFORE step 7 but
its condition is orthogonal to step 6's (it depends on `installed_sha`, not `proposed_sha`, for the
"is this a target-side edit" test).
**When to use:** Any destination that is NOT gsd-owned/constitution/derived/marker-capable/create
(i.e., only for destinations that would otherwise hit step 6 or 7).
**Example (pseudocode against real signatures, `destinations.py:326-366`):**
```python
# existing = Path(target_root) / rel; already resolved above
if existing_sha is None:
    existing_sha = _existing_hash(existing)
if existing_sha == proposed_sha:
    return "preserve"
# NEW: only reachable when existing_sha != proposed_sha (harness source has moved
# relative to what's on disk). Distinguish "target changed" from "harness changed"
# using the recorded installed_sha256 — NEVER proposed_sha, per CONTEXT.md's own
# rejected-alternative note ("comparing against the source hash instead cannot tell
# who changed what").
if installed_sha is not None and existing_sha == installed_sha:
    return "update"
return "conflict"
```
Safety property to preserve (explicit in CONTEXT.md and mirrored from the existing `proposed_sha`
idiom at `destinations.py:60-63`): `installed_sha=None` (never recorded, e.g. first-ever adopt) must
never resolve to `update` — `None` can never equal a real sha256 hex string, so the fallthrough to
`conflict`/`preserve` is automatic and requires no extra guard, exactly mirroring how `proposed_sha`
already behaves at step 6 today.

### Pattern 2: `existing_sha` hint threading (WR-03 precedent, extend don't duplicate)
**What:** `build_manifest()` already threads an `existing_sha` hint from the inventory
(`destinations.py:390-408`, WR-03) to avoid re-reading target files disposition() would otherwise
re-hash. The same threading pattern is the correct seam for `installed_sha`.
**Example (real signature to extend, `destinations.py:369-375`):**
```python
def build_manifest(
    inventory: dict,
    target_root: Path,
    proposed_hashes: dict[str, str],
    *,
    catalog: list[dict] | None = None,
    installed_hashes: dict[str, str] | None = None,   # NEW — {destination: installed_sha256}
) -> dict:
    ...
    result = disposition(
        destination, target_root, proposed_hashes.get(destination),
        existing_sha=existing_sha,
        installed_sha=(installed_hashes or {}).get(destination),   # NEW
    )
```
`installed_hashes` is read by the CLI from `.harness/adoption/installed.json` before calling
`build_manifest` — see Pattern 3.

### Pattern 3: `.harness/adoption/installed.json` is bookkeeping, never a destination-catalog row
**What:** CONTEXT.md is explicit and this research confirms it structurally: `destination_catalog()`
(`destinations.py:236-282`) enumerates `_CATEGORY_GLOBS` (`destinations.py:142-181`) — none of which
match `.harness/**`, so a target's `.harness/adoption/installed.json` is **never enumerated today**
by construction (no glob starts with or contains `.harness`). No code change is needed to keep it
out of the catalog; there is, however, no PROOF of that fact beyond "the glob list doesn't mention
it" — a regression test asserting `.harness/adoption/installed.json` is absent from
`destination_catalog()`'s output is cheap insurance against a future glob (e.g. a careless
`"**/*.json"` addition) reintroducing it. This mirrors the belt-and-suspenders pattern already used
for `.workflow/tasks/**` (`_EXCLUDED_PREFIX`, `destinations.py:183-185`) — Claude's Discretion is
whether `.harness` needs its own structural exclusion constant or whether "no glob matches it" is
sufficient; given the repo's own stated defense-in-depth idiom for the `.workflow/tasks/**` case,
adding `_HARNESS_BOOKKEEPING_PREFIX = (".harness",)` alongside `_EXCLUDED_PREFIX` and skipping it the
same way is the lower-risk, one-line-diff choice.

### Pattern 4: `refuse_unsafe_destination` is NOT the choke point for `.harness/adoption/installed.json`
**What:** `refuse_unsafe_destination` (`apply.py:110-202`) is the choke point for MANIFEST-DRIVEN
writes (destinations that appear in `manifest["dispositions"]`). Since `installed.json` is
deliberately never a disposition row (Pattern 3), its own read/write does NOT go through this
function — it needs its own, much simpler confinement check (it always writes to exactly one fixed
relative path under a known target_root, so a single `refuse_if_outside_root`-style call, or simply
resolving `target_root / ".harness/adoption/installed.json"` and confirming it lands under
`target_root`, suffices). Do not force it through the manifest-disposition machinery just for
uniformity — that machinery exists to classify FOREIGN template destinations against 7 rules; the
installed record is adopt's own single, always-known path.

### Anti-Patterns to Avoid
- **Reusing `create`'s collision-checked `os.link` path for `update`:** CONTEXT.md explicitly
  rejects this ("would destroy `apply.py`'s 'never silently overwrite' invariant"). `update` must
  use `_atomic_replace` (the same primitive `_apply_marker_merge` already uses at `apply.py:373`),
  not `atomic_create`.
- **Comparing against `proposed_sha` instead of `installed_sha` for the update/conflict split:**
  CONTEXT.md names this as a rejected alternative — it "cannot tell who changed what." The
  discriminator MUST be `installed_sha` (what adopt itself wrote last time), not `proposed_sha`
  (what the harness would write now).
- **Writing `installed.json` on a no-op run:** CONTEXT.md is explicit — "the record is
  content-derived only — no timestamps, no run counters." A no-op MUST NOT touch
  `.harness/adoption/installed.json` at all, or the before/after tree-hash proof (Validation
  Architecture, below) fails by construction.
- **Recording `harness/project.toml`'s `installed_sha256` as the pre-splice harness payload:**
  WR-08's whole point is that the applied bytes are `harness_payload + b"\n" + sidecar_bytes`
  (`cli.py:292`) — the recorded hash MUST be of those post-splice bytes, or `harness/project.toml`
  falls into `conflict` on literally the very next draft, forever (exactly WR-08's named defect).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Durable single-file replace | A new fsync/rename sequence | `tools/adoption_apply/apply.py::_atomic_replace` (already exists, already used by marker-merge) | Exact same safety properties needed for `update`; the module's own docstring names this as one of exactly two "complete, self-contained" write idioms |
| RFC 8785 canonical hashing for the contract-drift gate | A bespoke JSON canonicalizer | `tools/contract_hash/hash.py::schema_hash`/`write_manifest` | Already the sole canonicalizer in the repo; `build_manifest()`'s glob (`SCHEMA_GLOB = "**/*.schema.json"`, `hash.py:29`) auto-discovers a new schema file with zero code change — only re-running `write_manifest()` is needed |
| JSON Schema Draft 2020-12 validation for `installed.json`/`conflicts.json` | A hand-rolled shape checker | `jsonschema.Draft202012Validator` via `cli.py`'s existing `_load_schema`/`_validate` helpers (`cli.py:127-140`) | Verbatim reuse pattern already established for `inventory`/`plan`/`manifest` |
| Tree-hash before/after proof for the no-op claim | A new comparison script from scratch | `.planning/phases/52-evidence-bounded-real-target-adoption/scripts/compare-worktree-writes.py` (D-21) — copy/adapt the `git status --porcelain=v2 --untracked-files=all` diff idiom | Already proven against the exact same real target in Phase 52; reuses `expected_lock_sidecars`/`HARNESS_MANAGED_LOCK_SIDECARS` verbatim (never retyped) |
| Contract-plane edit mechanics | A generic "apply this JSON patch" tool | A phase-local, idempotent, `--check`/`--write` off-plane script modeled EXACTLY on `.planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py` | This is the repo's own established, reviewed pattern for exactly this situation (an agent cannot write `contracts/`, a human runs a vetted script instead) |

**Key insight:** every primitive Phase 53 needs already exists somewhere in this repo, proven
against this exact real target in Phase 51/52. The work is wiring (new branch, new hint parameter,
new record file), not new infrastructure.

## Common Pitfalls

### Pitfall 1: A missing `installed_sha` silently resolving to `update` via a truthy-but-wrong check
**What goes wrong:** If the new step is written as `if existing_sha == installed_sha: return
"update"` and `installed_sha` defaults to `""` or `0` instead of `None`, a destination that was
NEVER recorded (first-ever adopt, or a destination added to the catalog after the last install)
could spuriously satisfy the comparison in a language with weak equality — not a real risk in
Python (`None == ""` is `False`), but the analogous bug is real if the reader function returns a
sentinel string instead of `None` for "not found." **Why it happens:** copy-pasting the
`_EXCLUDED_SENTINEL` idiom (`destinations.py:96`, a sentinel that can never equal a real sha256)
without checking the sentinel truly can't collide. **How to avoid:** use `None`, exactly like
`proposed_sha`'s existing contract, and add a test asserting a destination with `installed_sha=None`
never returns `update` regardless of what `existing_sha`/`proposed_sha` are (the mutation-test
target: flip the guard, confirm RED). **Warning signs:** a `disposition()` unit test that only
covers the happy path (installed_sha present, matches) and never covers installed_sha absent.

### Pitfall 2: The no-op proof rewriting `installed.json` anyway
**What goes wrong:** If `_cmd_apply` unconditionally calls
`write_installed_record(target_root, computed_entries)` after every apply (rather than only when
`computed_entries != previously_read_entries`), a byte-identical re-run still touches
`.harness/adoption/installed.json`'s mtime or produces a semantically-identical-but-differently-
serialized JSON (key order, trailing newline), which shows up as a changed path in the
`git status --porcelain` before/after diff and defeats SC-2's own "observable no-op" criterion.
**Why it happens:** it is simpler to always write than to diff-before-write. **How to avoid:**
compare the freshly computed installed-record dict against the one read at the start of `_cmd_apply`
(structural equality, not byte equality of a re-serialization) and skip the write entirely when
equal — mirroring `create_or_resume_batch`'s existing "SAFE RESUME... no write" idiom
(`batch.py:121-143`). **Warning signs:** `git status` shows `.harness/adoption/installed.json` as
modified on a run where `applied=0 updated=0 conflicts=0`.

### Pitfall 3: `conflicts.json` from a PRIOR run being read as if it were this run's report
**What goes wrong:** Unlike `.lock` sidecars (which are deliberately never unlinked, D-15),
`conflicts.json` is a per-batch artifact under a FRESH batch directory each session
(`batch_id_for` is content-derived from `(target_ref, UTC date)`, `batch.py:109-118`) — so a stale
`conflicts.json` from an earlier same-day batch could theoretically be read by a naive "does
conflicts.json exist" check without confirming it belongs to THIS run's manifest. **Why it happens:**
batch resumption (`create_or_resume_batch`) is designed to let same-day re-drafts resume the SAME
directory — so a `conflicts.json` written by a previous `apply` invocation against that batch could
still be sitting there when a later `apply` invocation (after a manifest edit) runs again. **How to
avoid:** always overwrite `conflicts.json` at the start of a fresh `apply` run (or delete-then-write)
rather than appending, and never treat its mere existence as meaningful without checking its
`batch_id`/`target_ref` match the current invocation. **Warning signs:** a conflict from a previous
run still being reported after the underlying divergence was manually resolved.

### Pitfall 4: The lock-sidecar "no bytes written" claim breaking under the no-op proof
**What goes wrong:** `_apply_marker_merge` creates `.lock` sidecars that are NEVER unlinked (D-15,
confirmed at `apply.py:319-322`, `HARNESS_MANAGED_LOCK_SIDECARS`). A naive before/after tree-hash
comparison that does not allowlist these three sidecars (`.AGENTS.md.lock`, `.CLAUDE.md.lock`,
`.claude/.settings.json.lock`) will see them as "new/changed" on the FIRST re-run after the initial
adopt, incorrectly failing an otherwise-true no-op claim. **Why it happens:** the sidecar's mtime (or
its very existence, on a fresh clone) changes even when its content is byte-identical, because
`_apply_marker_merge` reopens it (`"a+b"` mode) and re-flocks it on every call, even when the merge
result is unchanged. **How to avoid:** reuse `compare-worktree-writes.py`'s exact allowlist pattern
(`expected_lock_sidecars`/`HARNESS_MANAGED_LOCK_SIDECARS`, imported verbatim, never retyped) when
building Phase 53's no-op proof script — this is precisely why Phase 52's script already carries this
allowlist and Phase 53 should copy, not rebuild, it. **Warning signs:** a "no-op" claim that reds
only on the SECOND run of a from-scratch adopted target, not the third+ — that shape is diagnostic
of the lock-sidecar mtime, not a real content write.

### Pitfall 5: A vacuous "no-op" test that never actually exercises the update path
**What goes wrong:** (This repo's signature defect, explicitly named in CONTEXT.md and AGENTS.md.)
A test asserting `applied=0 updated=0 conflicts=0` after a SECOND run of the SAME batch/target with
NOTHING changed is trivially true even if the `update`/`conflict` code paths are entirely unreachable
— it proves nothing about whether `update`/`conflict` classification WORKS, only that "nothing
happened, nothing happened." **Why it happens:** the easiest fixture to write is "run apply twice,
assert the second summary is all-zero," which passes even with `disposition()`'s new branch deleted
entirely (every destination would just fall through old step 6→`preserve`, still yielding a
"no-op"-shaped summary with different field names). **How to avoid:** the no-op test MUST be paired
with (a) a positive `update` test that mutates a harness-source file between draft 1 and draft 2 and
asserts a destination flips FROM `preserve` (or whatever the very first apply gave it) TO `update`
in the second manifest, actually gets rewritten, and (b) a positive `conflict` test that mutates the
TARGET-side file after the first apply and asserts the SAME destination now resolves to `conflict`
with the file byte-unchanged after the second apply — see Validation Architecture, Req→Test map,
below. **Warning signs:** a green "no-op" test suite with zero tests that ever construct a genuine
`installed_sha != existing_sha` or `existing_sha != proposed_sha, existing_sha == installed_sha`
scenario.

### Pitfall 6: The new contract silently blowing the milestone's own governed-surface count
**What goes wrong:** described at length in Summary — CONTEXT.md's locked "new sibling schema"
decision, taken literally, raises the contract count from 6 to 7 (or 8, if `conflicts.json` also
needs its own schema file), directly contradicting `ROADMAP.md:230-232`'s milestone-wide binding
boundary and `ROADMAP.md:314`'s Phase-54 closeout requirement, neither of which name a compensating
removal. **Why it happens:** CONTEXT.md's smart-discuss session evaluated the SC-1/SC-2/SC-3 tradeoffs
in isolation from the roadmap's numeric constraint (both are legitimate, separately-authored planning
artifacts that were not cross-checked against each other at authoring time). **How to avoid:** do not
let a plan silently write the new schema file and rebaseline the hash without the human seeing this
specific numeric conflict; see Open Questions #1 for the three concrete resolution paths. **Warning
signs:** `find contracts -name '*.schema.json' | wc -l` returning 7 or 8 anywhere before Phase 54's
own closeout accounting, with no corresponding entry in Phase 54's plan removing an existing schema.

## Code Examples

### Existing 7-step chain to extend (verified against live source)
```python
# tools/adoption_scan/destinations.py:326-366 (current, unedited)
def disposition(
    rel: str, target_root: Path, proposed_sha: str | None, *, existing_sha: str | None = None,
) -> str | None:
    if is_gsd_owned(rel):
        return None
    if resolve_path(CONSTITUTION_GLOBS, rel) == "deny" or rel == "libs/normalize-spec.md":
        return "human-ratification-required"
    if resolve_path(DERIVED_GLOBS, rel) == "deny":
        return "derived-regenerate"
    if rel in MARKER_CAPABLE:
        return "marker-merge"
    existing = Path(target_root) / rel
    if not existing.exists():
        return "create"
    if existing_sha is None:
        existing_sha = _existing_hash(existing)
    if existing_sha == proposed_sha:
        return "preserve"
    return "conflict"
```

### Existing durable-replace primitive to reuse for `update` (verified)
```python
# tools/adoption_apply/apply.py:239-268 (current, unedited) — already used by _apply_marker_merge
def _atomic_replace(path: Path, payload: bytes) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload); handle.flush(); os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise
```

### Existing off-plane script pattern (Phase 52 precedent to model the new script on)
```python
# .planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py
# (verified live, lines 1-24, 98-159) — --check (default, no write) / --write (human-run,
# GOLDEN_APPROVE_HUMAN=1), idempotent (safe to re-run), rebaselines via the SHIPPED hasher:
#   uv run python <script> --check
#   GOLDEN_APPROVE_HUMAN=1 uv run python <script> --write
# Phase 53's script must do the same for TWO edits: manifest.schema.json's enum (append "update")
# and (pending Open Questions #1's resolution) installed.schema.json's creation, then call
# tools.contract_hash.hash.write_manifest() exactly once at the end, same as the precedent.
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| `/adopt apply` always treats a re-run as a fresh install (6-value enum, no `update`) | 7-value enum with `update`, driven by a target-resident `installed.json` record | This phase (MONO-12) | Re-running `/adopt` against an already-adopted target stops silently re-`create`-ing or blanket-`conflict`-ing every managed file |
| `harness/project.toml`'s splice makes it permanently `conflict` on re-adoption (WR-08, unresolved as of Phase 52) | Recording POST-splice bytes as `installed_sha256` resolves this as a side effect, per CONTEXT.md | This phase | WR-08 is closed without separate dedicated work |
| CLI exit codes: 0 (clean) / 1 (fault or refusal, AD-04) / 2 (usage/missing batch) | + 3 (conflicts recorded, run still completed — a distinct "human decision needed" outcome) | This phase | No existing caller parses these exit codes by number (verified: no grep hit for CLI exit-code consumption outside `tools/adoption_apply/tests/`), so this is additive with zero blast radius |

**Deprecated/outdated:** None — this is the first phase to touch re-run semantics; there is no prior
"update" concept to deprecate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `conflicts.json` requires its own new JSON Schema file (as opposed to being validated by a lighter hand-written shape check, or reusing an existing schema's `$defs`) | Summary, Pitfall 6, Open Questions #1 | If wrong (a schema-file-free validation is acceptable), the contract-count conflict is smaller than stated (7, not 8) — still a conflict, but less severe. This is `[ASSUMED]` because CONTEXT.md's wording ("schema-validated") does not explicitly mandate a new `.schema.json` file; it is read literally here out of caution. |
| A2 | No CI job, pre-commit hook, or external caller other than `tools/contract_drift` and `contract_guard.py` gates a `contracts/**` write | Open Questions #1, "Contract-change mechanics" | If another gate exists (e.g. a golden snapshot keyed to contract COUNT specifically, beyond the drift hash), it was not found by this research's grep pass; verify before assuming the only two gates are drift + CODEOWNERS. |
| A3 | `.harness/adoption/installed.json`'s own read/write does not need to route through `refuse_unsafe_destination` | Pattern 4 | If a reviewer later decides it SHOULD route through that choke point for uniformity, the module boundary changes (a plan choosing this shortcut should still add its OWN confinement check, not skip confinement altogether) |

**If this table is empty:** N/A — see rows above; all three are flagged specifically because they
depend on scope/interpretation judgment calls this research could not fully resolve via code reading
alone.

## Open Questions

1. **The contract-count conflict (see Summary/Pitfall 6) — requires explicit human resolution
   before any constitution-plane script is written or run.**
   - What we know: 53-CONTEXT.md locks "a new sibling schema... not an extension of
     `manifest.schema.json`" for the installed record, plus a "schema-validated" `conflicts.json`.
     `ROADMAP.md:230-232` states contracts must stay at 6 across Phases 51-54 as a *binding
     boundary*, and `ROADMAP.md:314` (Phase 54's own goal) requires closeout counts "no greater
     than... 6 contracts" with no named compensating removal.
   - What's unclear: whether the roadmap's "6 contracts" constraint was written with awareness of
     this phase's CONTEXT.md decision (they read as independently authored, non-cross-checked
     documents), and whether a transient bump (Phase 53 goes to 7/8, Phase 54 brings it back to 6
     by retiring something) was the intended design that just never got written down anywhere.
   - Recommendation: surface this explicitly to the human before planning proceeds past the
     contract-plane task. Three live options, in order of how much they preserve CONTEXT.md's
     locked reasoning: (a) human confirms the transient bump and names what Phase 54 retires to
     compensate; (b) fold the installed-record fields as new optional properties inside
     `manifest.schema.json`'s own `$defs` instead of a sibling file (contradicts CONTEXT.md's stated
     "leaves the manifest hash untouched" rationale, but the manifest hash changing on an additive,
     backward-compatible schema edit is itself classified `non-breaking` by `contract_drift`'s own
     `_index`/diff logic — see `drift.py:10-13` — so "the hash changes" is not itself harmful, only
     the file-count is); (c) validate `installed.json`/`conflicts.json` structurally in Python
     without a committed `.schema.json` file (loses machine-readable contract-first provenance for
     these two documents, which cuts against this repo's own contract-first core value).

2. **Does `_load_schema`/`_validate`'s existing pattern (`cli.py:127-140`) generalize cleanly to a
   document that is NOT part of `_DRAFT_ARTIFACTS` (i.e., not written during `draft`, but during
   `apply`)?**
   - What we know: `_validate(name, document)` just needs a `{name}.schema.json` under
     `_SCHEMA_DIR` and a dict — nothing in its signature assumes draft-time-only usage.
   - What's unclear: whether `installed.json`'s validation should happen on READ (defending against
     a hand-tampered target-resident file) as well as on WRITE — CONTEXT.md doesn't specify.
   - Recommendation: validate on both read and write, mirroring `_cmd_apply`'s existing WR-04
     re-validation of `manifest.json` before use (`cli.py:254-262`) — an untrusted, target-resident
     file deserves at least the same suspicion as a batch-local one.

3. **Exact field/module names for the installed-record reader/writer** (explicitly left to Claude's
   Discretion in CONTEXT.md) — not resolved here by design; the planner should pick names and this
   research does not prescribe them beyond the `tools/adoption_apply/installed.py` placement
   suggested in Recommended Project Structure.

## Environment Availability

Skipped — this phase has no new external dependencies beyond what Phase 51/52 already proved
available (git, the FeedbackOps worktree tooling, `uv run pytest`). No new tool/service/runtime is
introduced.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already the repo-wide framework; root `testpaths` covers `tools/` + `libs/python`, confirmed via `.github/workflows/ci.yml:185`) |
| Config file | root `pyproject.toml` (existing; no new config needed) |
| Quick run command | `uv run pytest tools/adoption_scan tools/adoption_apply tools/harness_config/tests -q` |
| Full suite command | `uv run pytest -q` (1047 passed as of Phase 52's close, per `52-REVIEW.md:60`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MONO-12 / SC-1 | Every managed file appears in `installed.json` after a first apply | unit | `pytest tools/adoption_apply/tests/test_installed_record.py::test_installed_record_covers_every_applied_destination -x` | ❌ Wave 0 |
| MONO-12 / SC-2a | A second draft/apply with NOTHING changed produces `applied=0 updated=0 unchanged=N conflicts=0` AND leaves `installed.json` byte-unchanged | unit + fixture tree-hash | `pytest tools/adoption_apply/tests/test_update_disposition.py::test_true_no_op_writes_nothing -x` | ❌ Wave 0 |
| MONO-12 / SC-2b (the positive case — Pitfall 5 guard) | A harness-source file changes between draft 1 and draft 2; the destination flips to `update`, gets rewritten, and `installed_sha256` advances | unit | `pytest tools/adoption_apply/tests/test_update_disposition.py::test_update_fires_when_harness_source_moves -x` | ❌ Wave 0 |
| MONO-12 / SC-3 | A target-side edit after apply 1 makes the SAME destination resolve to `conflict` on draft 2, `conflicts.json` names both hashes, and the target file is byte-unchanged after apply 2 | unit | `pytest tools/adoption_apply/tests/test_update_disposition.py::test_target_divergence_produces_conflict_and_leaves_file_unchanged -x` | ❌ Wave 0 |
| MONO-12 / SC-3 (exit code) | A conflict-bearing apply exits 3, not 0 or 1, and does not abort earlier/later rows | unit | `pytest tools/adoption_apply/tests/test_cli.py::test_apply_with_conflict_exits_3_and_completes_other_rows -x` | ❌ Wave 0 |
| MONO-12 (safety) | `installed_sha=None` never resolves to `update` regardless of `existing_sha`/`proposed_sha` (Pitfall 1) | unit, mutation-tested | `pytest tools/adoption_scan/tests/test_dispositions.py::test_update_never_fires_without_a_recorded_installed_hash -x` | ❌ Wave 0 |
| WR-07/WR-08 closure | The `harness/project.toml` splice's post-splice bytes are what gets recorded as `installed_sha256`, and a re-adopt of an unchanged target resolves it to `preserve`-then-`update`-never-`conflict` semantics correctly (not permanently `conflict`) | integration (real splice bytes) | `pytest tools/adoption_apply/tests/test_cli.py::test_project_toml_splice_recorded_hash_survives_reapply -x` | ❌ Wave 0 |
| Real-target proof (CONTEXT.md's "Proof & surface budget") | One real re-run against a freshly provisioned FeedbackOps worktree reproduces SC-1/2/3 with literal captured values, matching Phase 51/52's evidence discipline | manual/scripted, evidence-recorded | Adapted from `compare-worktree-writes.py` (D-21) — see below | N/A (evidence artifact, not a pytest node) |

### Sampling Rate
- **Per task commit:** quick run command above.
- **Per wave merge:** full suite command.
- **Phase gate:** full suite green before `/gsd:verify-work`, PLUS the one real-target re-run
  evidence file (mirroring `52-ADOPTION-EVIDENCE.md`'s shape) before the phase is claimed done —
  per CONTEXT.md's own "Proof & surface budget" decision, fixture tests alone are insufficient
  proof for this phase.

### Wave 0 Gaps
- [ ] `tools/adoption_apply/tests/test_installed_record.py` — covers SC-1 (every managed file
      recorded) and the read/write round-trip, including the no-op-does-not-rewrite property.
- [ ] `tools/adoption_apply/tests/test_update_disposition.py` (or fold into
      `tools/adoption_scan/tests/test_dispositions.py` + `tools/adoption_apply/tests/
      test_atomic_apply.py`, following the existing split between "disposition classification" and
      "apply-time writing") — covers SC-2a/b and SC-3's positive+negative cases, per Pitfall 5's
      warning against a vacuous no-op-only test suite.
- [ ] A new phase-local script under `.planning/phases/53-managed-adopt-updates/scripts/`
      (mirroring `compare-worktree-writes.py`'s D-21 "phase-local, not a `tools/` module" placement)
      that drives the real FeedbackOps re-run and captures before/after tree hashes for SC-2/SC-3's
      real-target evidence — this is new phase-local tooling, not a new shared module, so it does
      not count against NG-01's governed-surface budget (Phase 52's own precedent for this
      distinction).
- [ ] The off-plane constitution-plane script (`.planning/phases/53-managed-adopt-updates/scripts/
      apply-manifest-update-enum.py` or similar, modeled on `apply-inventory-enum.py`) — cannot be
      written or run until Open Questions #1 is resolved with the human.
- [ ] Mutation-test evidence (per this repo's own convention, `1481655`/`52-04-SUMMARY.md`) for
      every new or edited assertion — in particular the `installed_sha is None` guard (Pitfall 1)
      and the no-op-does-not-rewrite guard (Pitfall 2), both of which are exactly the kind of "check
      that cannot fail" this repo has repeatedly caught in review (CR-03's own three self-caught
      vacuous tests, `52-REVIEW.md:126-137`).

## Security Domain

`security_enforcement` is absent from `.planning/config.json` (treated as enabled per the
instructions), but this phase's actual surface is a local-filesystem apply tool operating on a
developer-provisioned worktree, not a network-facing service — most ASVS categories do not apply.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | No auth surface — CLI tool, local filesystem only |
| V3 Session Management | no | No sessions |
| V4 Access Control | yes (narrow) | `refuse_if_constitution`/`refuse_unsafe_destination` (existing) — constitution-plane access is gated by `GOLDEN_APPROVE_HUMAN` + CODEOWNERS, unchanged by this phase except that the new `update` branch must ALSO be refused before any write when the destination resolves onto the constitution plane (it already is, structurally, since `refuse_unsafe_destination` runs before the disposition-value dispatch in `apply_disposition`, `apply.py:396`) |
| V5 Input Validation | yes | `jsonschema.Draft202012Validator` against `installed.schema.json`/`conflicts` shape (new); reuse `_validate` verbatim |
| V6 Cryptography | yes (hashing only, not secrecy) | `hashlib.sha256` (stdlib), already the sole hash primitive in this module — never a new hash function |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| A target-resident `installed.json` is hand-edited to fake a matching `installed_sha256` so a genuinely conflicting file is misclassified as `update` and silently overwritten | Tampering | Validate `installed.json` on READ (Open Question #2) and, more importantly, the safety property already holds structurally: even a forged `installed_sha` only causes `update` (a durable-replace with the HARNESS's own known-good content) rather than `preserve`-of-something-hostile — the payload written is always `harness_proposed_hash`'s content, never target-supplied bytes, so a forged record cannot inject arbitrary content, only mis-time when a legitimate overwrite happens |
| A destination whose `.harness/adoption/installed.json` entry is stale after the destination itself was removed from `_CATEGORY_GLOBS`/the catalog | Tampering / Repudiation (stale record) | Out of scope for this phase (uninstall/prune is explicitly deferred in 53-CONTEXT.md); the installed record may over-list destinations no longer in the catalog — acceptable per the deferred-ideas boundary, but worth a one-line docstring note so it isn't mistaken for a bug later |

## Sources

### Primary (HIGH confidence — read live in this session)
- `tools/adoption_scan/destinations.py` (full file) — `DISPOSITION_ENUM`, `disposition()`,
  `build_manifest()`, `harness_proposed_hashes()`, `destination_catalog()`, `_CATEGORY_GLOBS`
- `tools/adoption_apply/apply.py` (full file) — `apply_disposition`, `apply_manifest`,
  `atomic_create`, `_atomic_replace`, `refuse_unsafe_destination`, `_apply_marker_merge`,
  `HARNESS_MANAGED_LOCK_SIDECARS`
- `tools/adoption_apply/cli.py` (full file) — `_cmd_draft`, `_cmd_apply`, `derive_language_rows`,
  the WR-07/WR-08 splice logic (`cli.py:274-307`)
- `tools/adoption_apply/batch.py` (full file) — `batch_id_for`, `create_or_resume_batch`,
  `update_status` CAS idiom
- `contracts/harness/adoption/manifest.schema.json` (full file) — current 6-value
  `dispositionEnum`
- `tools/hooks/contract_guard.py` (full file) — `CONSTITUTION_GLOBS`, `APPROVAL_ENV`, `decide()`
- `.github/CODEOWNERS` — `/contracts/` gated to `@hjung3113`, advisory-only caveat noted in-file
- `tools/contract_hash/hash.py` (full file) — `schema_hash`, `build_manifest` (glob-based,
  auto-discovers new schema files), `write_manifest`
- `tools/contract_drift/drift.py` (lines 1-80) — `diff_manifests`'s `added`/`removed`/`changed`
  split, `_index`'s breaking/non-breaking classification (additive enum = non-breaking)
- `.planning/phases/52-evidence-bounded-real-target-adoption/scripts/apply-inventory-enum.py`
  (full file) — the off-plane script precedent this phase's contract-edit script should mirror
- `.planning/phases/52-evidence-bounded-real-target-adoption/scripts/compare-worktree-writes.py`
  (lines 1-80+) — the before/after tree-diff idiom for the no-op/byte-unchanged proofs
- `.planning/phases/52-evidence-bounded-real-target-adoption/52-REVIEW.md` (full file) — WR-07,
  WR-08 verbatim text and disposition; CR-01/CR-02/CR-03 context
- `.planning/phases/52-evidence-bounded-real-target-adoption/52-ADOPTION-EVIDENCE.md` (full file)
  — SC verdicts, OBS-D ledger, W-10/W-3/W-5 recorded consequences for Phase 53
- `.planning/phases/51-real-target-observation-baseline/51-BASELINE-EVIDENCE.md` (full file) —
  OBS-D-01..04 observation ledger
- `.planning/ROADMAP.md` (lines 220-320) — the milestone-wide binding boundary and Phase 53/54 goal
  statements (source of the flagged contract-count conflict)
- `.planning/REQUIREMENTS.md` (full file) — MONO-12, NG-01, traceability table
- `harness/commands/adopt.md`, and a grep across `.claude/`/`.opencode/` emitted equivalents — no
  exit-code-number parsing found anywhere outside `tools/adoption_apply/tests/`
- `tools/adoption_scan/tests/test_dispositions.py::test_total` (lines 35-50) — the totality-proof
  test that must be extended when `DISPOSITION_ENUM` grows to 7
- `.github/workflows/ci.yml` (lines 35-70) — the `id`/`test` hard-requirement CR-03's fix is keyed
  to, confirming why `derive_language_rows` treats `test` as the one mandatory key
- Live shell verification: `find contracts -name '*.schema.json' | wc -l` → `6`

### Secondary (MEDIUM confidence)
- None beyond what's listed above as primary — this research required no external web search; the
  entire domain is in-repo, already-implemented adjacent code.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies, everything verified against live source
- Architecture: HIGH — every pattern cited against a real file:line, cross-checked against Phase
  51/52's own evidence artifacts
- Pitfalls: HIGH — five of six are directly traced to explicit CONTEXT.md rejected-alternatives or
  named Phase-52 defects (WR-05 through WR-08); the sixth (contract-count conflict) is a fresh
  cross-document finding from this research session, verified by live `find`/grep, not inferred

**Research date:** 2026-08-01
**Valid until:** 14 days (fast-moving — this milestone is actively landing phases weekly; re-verify
contract count and DISPOSITION_ENUM cardinality against live source before planning if this research
is consumed more than two weeks after today)
