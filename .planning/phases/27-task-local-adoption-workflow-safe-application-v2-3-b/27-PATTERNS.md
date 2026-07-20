# Phase 27: Task-Local Adoption Workflow + Safe Application (v2.3 B) - Pattern Map

**Mapped:** 2026-07-21
**Files analyzed:** 15 (new package: 4 modules + 4 test files + 3 fixture trees; 1 new contract;
2 harness source docs — command + skill; 1 hash-manifest rebaseline)
**Analogs found:** 15 / 15 (every file has at least a role-match analog; several have an exact,
named-in-RESEARCH analog)

No CONTEXT.md exists for this phase; the file list below is extracted from 27-RESEARCH.md's
"Recommended Project Structure" + 27-VALIDATION.md's Wave 0 requirements, cross-checked against the
live tree (`tools/adoption_scan/` confirmed present as Phase 26's shipped sibling; no
`tools/adoption_apply/` yet).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `tools/adoption_apply/pyproject.toml` | config | — | `tools/adoption_scan/pyproject.toml` | exact |
| `tools/adoption_apply/__init__.py`, `__main__.py` | utility/CLI entry | request-response | `tools/adoption_scan/__main__.py` + `cli.py` | exact |
| `tools/adoption_apply/batch.py` | service (CAS-bound state) | CRUD | `tools/task_control/manager.py` (`create`/`missing_artifacts`/`_cas_write`) | exact |
| `tools/adoption_apply/apply.py` | service (file I/O writer) | file-I/O | `tools/task_control/manager.py::_atomic_create` + `tools/handoff/handoff.py::_atomic_write_once` + `tools/harness_emit/merge.py` | exact |
| `tools/adoption_apply/approval.py` | service (human-gate) | request-response | `tools/golden_runner/approve.py` | exact |
| `tools/adoption_apply/tests/conftest.py` | test | — | `tools/adoption_scan/tests/conftest.py` | exact |
| `tools/adoption_apply/tests/test_batch_layout.py` | test | CRUD | `tools/task_control/tests/*` (CAS-write tests) | role-match |
| `tools/adoption_apply/tests/test_atomic_apply.py` | test | file-I/O | `tools/adoption_scan/tests/test_dispositions.py` + `tools/adoption_scan/tests/test_readonly.py` | role-match |
| `tools/adoption_apply/tests/test_constitution_refusal.py` | test | request-response | `tools/hooks/*` tests (hook decision tests) | role-match |
| `tools/adoption_apply/tests/test_approval_invalidation.py` | test | request-response | `tools/golden_runner/tests/test_approve_gate.py` (if present) — else model directly on `approve.py`'s refusal shape | role-match |
| `tools/adoption_apply/tests/fixtures/polyglot-single/**` | fixture | — | `tools/adoption_scan/tests/conftest.py::tmp_minirepo` (programmatic, not static) | role-match (different materialization strategy — see note below) |
| `tools/adoption_apply/tests/fixtures/client-server/**` | fixture | — | `tests/fixtures/workspace/{member-a,member-b}` | exact |
| `tools/adoption_apply/tests/fixtures/partial-collision-crlf/**` | fixture | — | `tmp_minirepo`'s hash-equal/hash-different pair (h) + CRLF synthesis pattern from `harness_emit/merge.py::_normalize` | role-match |
| `contracts/harness/adoption/approval.schema.json` | model/contract | CRUD | `contracts/harness/task-control/attestation.schema.json` (sibling shape, NOT `$ref`'d) | role-match (deliberately new, not extended — see RESEARCH Alternatives Considered) |
| `harness/commands/adopt.md` | command | request-response | `harness/commands/golden-approve.md` (human-gate wrapper) + `harness/commands/pipeline.md` (multi-step composition, `subtask: true`) | exact |
| `harness/skills/brownfield-adoption/SKILL.md` | provider (skill/runbook) | request-response | `harness/skills/pipeline-map/SKILL.md` | exact |

## Pattern Assignments

### `tools/adoption_apply/pyproject.toml` (config)

**Analog:** `tools/adoption_scan/pyproject.toml` (read in full)

```toml
[project]
name = "logparser-adoption-scan"
version = "0.0.0"
description = "..."
requires-python = ">=3.11"
dependencies = []

[tool.uv]
package = false
```

Copy verbatim except `name` (use e.g. `logparser-adoption-apply`) and `description`. Keep
`dependencies = []` — RESEARCH is explicit: **no new external package**, `uv.lock` must be
unchanged (`27-VALIDATION.md` gate: `uv sync --all-packages && git diff --exit-code uv.lock`).
`package = false` marks it a virtual workspace member (imported by module path, no wheel build) —
same as `adoption_scan`, `contract_hash`, `docs_sync`, `memory_regen` per that file's own comment.

---

### `tools/adoption_apply/__init__.py` + `__main__.py` (CLI entry point)

**Analog:** `tools/adoption_scan/__main__.py` (full file, 7 lines) + `tools/adoption_scan/cli.py`

```python
# tools/adoption_scan/__main__.py — copy this shape verbatim, only the import target changes
"""Package entrypoint so ``python -m tools.adoption_scan`` runs the CLI."""

from tools.adoption_scan.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

`cli.py`'s shape to mirror for `tools/adoption_apply`'s own CLI module (batch.py/apply.py/approval.py
likely need one `argparse` entrypoint each, or one router — RESEARCH's Assumption A4 recommends a
single `/adopt` command with argument-routed sub-verbs mirroring `cli.py`'s single `main(argv)`
pattern):

- `_REPO_ROOT = Path(__file__).resolve().parents[2]` (module depth: `tools/adoption_apply/x.py` →
  parents[2] is repo root — same depth as `adoption_scan`).
- `argparse.ArgumentParser(prog="tools.adoption_apply")`, explicit `required=True` args, no silent
  defaults for destination paths (mirrors `--out` having **no default**, D-11 rationale: never let
  the tool default into writing where it might contaminate its own next run).
- Exit codes: `2` for a bad CLI argument / precondition (mirrors `cli.py`'s `--target`/`--out`
  overlap check → `return 2`), `1` for a schema-validation failure, and (new for apply/approve)
  `3` for a refused human-ratification gate — copy `golden_runner/approve.py::main`'s `except
  GoldenApprovalRefused: ... return 3` exactly (see approval.py pattern below).
- `Draft202012Validator(schema).iter_errors(document)` — the exact validation call already used for
  `inventory`/`plan`/`manifest`; reuse verbatim for the new `approval` document, loaded from
  `contracts/harness/adoption/approval.schema.json`.

---

### `tools/adoption_apply/batch.py` (CAS-bound task-local batch layout, ADOPT-04)

**Analog:** `tools/task_control/manager.py` — `missing_artifacts()` (lines 223-235, quoted in
RESEARCH), `create()` (line 175), `_cas_write()` (lines 106-147, read in full below).

**Core CRUD pattern — the artifact-kind convention a batch must satisfy without any `manager.py`
change** (`tools/task_control/manager.py:223-235`):
```python
def missing_artifacts(task_dir, required=None):
    root = Path(task_dir)
    missing = []
    for artifact in (required if required is not None else _required_artifacts(root)):
        if artifact == "task_packet":
            present = all((root / name).is_file() for name in ("task.json", "state.json", "evidence.json"))
        else:
            artifact_root = root / "artifacts" / artifact
            present = artifact_root.is_dir() and any(
                child.is_dir() and any(child.iterdir()) for child in artifact_root.iterdir()
            )
        if not present:
            missing.append(artifact)
    return missing
```
A batch is `artifacts/adoption/<batch-id>/` — `<batch-id>` plays the role of `<run-id>` in this
exact convention. **Do not add `"adoption"` to `transitions.json`'s
`required_artifacts_by_target_phase`** unless the planner deliberately decides to (Open Question 1
in RESEARCH — default is NO change, a constitution-plane edit needs its own human-ratification
checkpoint if ever made).

**CAS write pattern to reuse for batch state mutations** (`tools/task_control/manager.py:106-147`):
```python
def _cas_write(task_dir, expected_revision, next_state, *, lock_held=False, allow_head_change=False):
    ...
    lock_path = path.with_name(f".{path.name}.lock")
    lock_context = nullcontext() if lock_held else lock_path.open("a+b")
    with lock_context as lock:
        if not lock_held:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        current = _read_state(task_dir)
        if current["revision"] != expected_revision:
            raise TaskControlError(f"stale writer: expected revision {expected_revision}, found {current['revision']}")
        if next_state["revision"] != expected_revision + 1:
            raise TaskControlError("mutation must increment revision by exactly one")
        _validate_state(next_state)
        previous_state_sha256 = sha256(path)
        _atomic_replace(path, next_state)
        ...
        return next_state
```
`batch.py` does **not** need its own CAS/lock scheme — a batch lives inside the *existing* task
packet's transaction boundary. Batch state mutations should be expressed as ordinary
`tools.task_control.manager` calls (`transition`/`attest`/whatever the planner wires) so the SAME
`fcntl.flock` + `expected_revision` check protects them; a hand-rolled second lock file for
`artifacts/adoption/<batch-id>/` is the anti-pattern RESEARCH's "Don't Hand-Roll" table calls out.

**`create()` idiom for a one-time batch-metadata file** (`manager.py:175-183`, itself thin sugar
over `_atomic_create`, see apply.py section below for the full body):
```python
def create(task_dir, state):
    """Create initial state exactly once; state must be revision-zero INTAKE."""
    path = _state_path(task_dir)
    ...
    _atomic_create(path, state)
```

---

### `tools/adoption_apply/apply.py` (atomic/collision-safe/idempotent writer + structural constitution refusal, ADOPT-05)

**Analogs (three, composed):**
1. `tools/task_control/manager.py::_atomic_create` (lines 150-173, full body below)
2. `tools/handoff/handoff.py::_atomic_write_once` (lines 130-161, full body below — a second
   independently-audited instance of the *same* idiom, confirming it is the established convention,
   not a one-off)
3. `tools/harness_emit/merge.py::splice_managed_block` / `merge_settings` (already quoted in full
   above)
4. `tools/hooks/contract_guard.py::CONSTITUTION_GLOBS`/`_on_constitution_plane` for the structural
   refusal
5. `tools/adoption_scan/destinations.py` for `MARKER_CAPABLE`, `DISPOSITION_ENUM`, `_existing_hash`
   reuse

**Atomic create idiom — copy this exact sequence** (`tools/task_control/manager.py:150-173`):
```python
def _atomic_create(path: Path, value: dict[str, Any]) -> None:
    """Create *path* exactly once using a durable temp plus hard-link publication."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical_bytes(value))
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError as exc:
            raise TaskControlError("state already exists") from exc
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
```

**Second confirmed instance — `tools/handoff/handoff.py:130-161`** (note the extra
already-exists-with-identical-payload short-circuit, useful for `apply.py`'s idempotent-reapply
requirement):
```python
def _atomic_write_once(path: Path, document: dict[str, Any]) -> None:
    payload = _canonical(document)
    if path.exists():
        if path.read_bytes() != payload:
            raise HandoffError(
                "handoff already exists for a different snapshot; create a new revision first"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise HandoffError("handoff already exists for a different snapshot")
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
```
For `apply.py`'s `create` disposition: use the `manager.py::_atomic_create` shape (raise on
collision, never silently compare-and-skip) because ADOPT-05 requires refusing "silent overwrite ·
concurrent target drift" as an explicit error, not a quiet no-op — the disposition-level idempotence
(re-run resolves to `preserve` before `atomic_create` is even called) is what RESEARCH's Pattern 2
already establishes; do not fold `handoff.py`'s payload-compare short-circuit into the low-level
primitive, keep that decision at the `apply.py`/disposition layer instead (matches RESEARCH's Code
Examples section exactly).

**Structural constitution refusal — reuse the CONSTANT, don't re-derive it**
(`tools/hooks/contract_guard.py:36,43,50-57`):
```python
from tools.harness_perms import resolve_path
...
CONSTITUTION_GLOBS = ["contracts/**", "docs/adr/**", "golden/**"]

def _on_constitution_plane(file_path: str) -> bool:
    relative_path = repo_relative(file_path)
    return bool(relative_path) and resolve_path(CONSTITUTION_GLOBS, relative_path) == "deny"
```
`apply.py` imports `CONSTITUTION_GLOBS` (and `tools.harness_perms.resolve_path`, whose full body is
`"deny" if any(fnmatchcase(path, glob) for glob in deny_globs) else "allow"` —
`tools/harness_perms/resolver.py:47-49`) directly:
```python
from tools.hooks.contract_guard import CONSTITUTION_GLOBS
from tools.harness_perms import resolve_path

class ConstitutionRefusal(ValueError):
    """A destination is on the CODEOWNERS-gated constitution plane; apply refuses structurally."""

def refuse_if_constitution(destination: str) -> None:
    if resolve_path(CONSTITUTION_GLOBS, destination) == "deny":
        raise ConstitutionRefusal(
            f"apply refused: '{destination}' requires human ratification "
            "(contracts/·docs/adr/·golden/), never auto-applied"
        )
```
This is the exact same import `tools/adoption_scan/destinations.py` already makes at line 87:
`from tools.hooks.contract_guard import CONSTITUTION_GLOBS  # noqa: F401 (re-exported for callers)`
— confirming this cross-module import direction (`adoption_apply` → `tools.hooks.contract_guard`)
is an already-established, non-circular pattern in this repo, not a new dependency shape.
**Call `refuse_if_constitution` at the START of every apply-mode file operation, per destination,
every call** — not cached/hoisted once per batch (RESEARCH Pattern 3's explicit "so a single
malformed/edited manifest row can never slip a constitution write through").

**Marker-merge reuse (verbatim, do not write a third merge implementation)** — full functions
already read above at `tools/harness_emit/merge.py:1-238`:
```python
from tools.harness_emit.merge import splice_managed_block, merge_settings
import json

existing_text = target_path.read_text(encoding="utf-8")
merged_text = splice_managed_block(existing_text, adoption_block_body)
# then atomic_replace(target_path, merged_text.encode())

existing_settings = json.loads(target_path.read_bytes())
merged_settings = merge_settings(existing_settings)
# then atomic_replace(target_path, json.dumps(merged_settings, indent=2).encode() + b"\n")
```
The 3 marker-capable destinations are named as data, not re-derived, at
`tools/adoption_scan/destinations.py:101`:
```python
MARKER_CAPABLE: frozenset[str] = frozenset({"AGENTS.md", "CLAUDE.md", ".claude/settings.json"})
```
Import `MARKER_CAPABLE` from `destinations.py` the same way `CONSTITUTION_GLOBS` is imported from
`contract_guard.py` — reuse, never re-list the 3 strings a second time.

**Disposition-iteration discipline (Pitfall 3)** — `destinations.py`'s manifest shape has TWO
top-level arrays, `dispositions[]` (`$ref: "#/$defs/dispositionRecord"`) and `excluded[]`
(`$ref: "#/$defs/excludedDestinationRecord"`), confirmed via the live schema. `apply.py` MUST
iterate `manifest["dispositions"]` only, and must **fail loud** (never
`dispositions.get(destination, "create")`) on an unrecognized destination.

**`DISPOSITION_ENUM` (6 values, `tools/adoption_scan/destinations.py:117-124`) — total, apply.py's
switch must cover exactly these, refusing (not defaulting) on any other value:**
```python
DISPOSITION_ENUM: tuple[str, ...] = (
    "create", "preserve", "conflict", "marker-merge", "derived-regenerate",
    "human-ratification-required",
)
```

**Hash re-check for concurrent-drift refusal** — reuse `destinations.py::_existing_hash` (line 277)
rather than reimplementing a hash-file helper; import it directly (accept the private-name
import — RESEARCH explicitly names this an acceptable coupling, "or promote it to a shared location
if too tight, but the FUNCTION should not be reimplemented").

---

### `tools/adoption_apply/approval.py` (human-ratification gate, ADOPT-06)

**Analog:** `tools/golden_runner/approve.py` (full file, 103 lines, read above).

**Core refuse-by-default pattern to mirror exactly** (note the THREE independent required signals —
`approve`, a reference identifier, and an env-matched confirmation value):
```python
class GoldenApprovalRefused(Exception):
    """Promotion .received → .verified refused (missing human sign-off / ADR / received file)."""

def promote(case, *, approve=False, adr=None, human_token=None):
    if not approve:
        raise GoldenApprovalRefused(
            "REFUSED: promotion requires an explicit human --approve flag "
            "(agents must not self-bless the golden baseline, P9)."
        )
    if not adr:
        raise GoldenApprovalRefused(
            "REFUSED: promotion requires an --adr reference "
            "(every baseline change cites a decision, P9)."
        )
    expected_value = os.environ.get(HUMAN_VALUE_ENV)
    if not expected_value or human_token != expected_value:
        raise GoldenApprovalRefused(
            f"REFUSED: promotion requires the human confirmation value ({HUMAN_VALUE_ENV}); "
            "an agent must not fabricate it."
        )
    ...

def main(argv=None) -> int:
    ...
    try:
        verified = promote(args.case, approve=args.approve, adr=args.adr, human_token=args.confirm)
    except GoldenApprovalRefused as exc:
        print(str(exc))
        return 3
    print(f"PROMOTED: {verified} (ADR: {args.adr}).")
    return 0
```
`approval.py`'s `AdoptionApprovalRefused` should mirror this shape 1:1, substituting the reference
tuple: instead of `--adr <id>`, ADOPT-06 requires exact-match on `(draft_hash, task_revision,
git_ref)`, recomputed **fresh** at promotion time (never cached from an earlier call — Pitfall 2).
The environment-variable name for the human confirmation value should be reused unchanged from
`tools/golden_runner/approve.py` and `tools/hooks/contract_guard.py` (same precedent variable both
already use) — not a new adoption-specific variable, per RESEARCH's Code Examples section.

CLI exit-code convention to copy: `2` bad args, `3` refused (`GoldenApprovalRefused`/
`AdoptionApprovalRefused`), `0` success — matches `golden-approve.md`'s documented contract.

---

### `contracts/harness/adoption/approval.schema.json` (new contract, ADOPT-06)

**Sibling-shape analog (NOT `$ref`'d):** `contracts/harness/task-control/attestation.schema.json`
(full file, 24 lines, read above):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://harness.local/contracts/harness/task-control/attestation.schema.json",
  "title": "Task context attestation contract",
  "type": "object",
  "additionalProperties": false,
  "required": ["constraints"],
  "properties": { "constraints": { "type": "array", "items": { ... } } }
}
```
Copy the `$schema`/`$id`/`title`/`type: object`/`additionalProperties: false` envelope shape
verbatim (this is the standard header for every contract in `contracts/harness/`), but do **not**
extend `attestation.schema.json`'s `constraints[]` array — RESEARCH's Alternatives Considered is
explicit that this is a *different* binding tuple (draft-hash + task-revision + git-ref for a
promotion decision, vs. constraint-source binding at CLARIFY/SPEC time) and D-11's convention is
"no cross-file `$ref`, duplicate the shape if reused." Model the new schema's required fields on
`manifest.schema.json`'s existing hash/revision-shaped fields (same repo, same `contracts/harness/
adoption/` directory) rather than the attestation schema's constraint-binding fields, which are a
different vocabulary. This is a **constitution-plane write** — pairs with a
`contracts/.hashes/manifest.json` rebaseline in one atomic, human-ratified commit (Manual-Only
Verification row in 27-VALIDATION.md: the human confirmation environment value must be set in a
human-run session).

---

### `harness/commands/adopt.md` (thin `/adopt` command, ADOPT-07)

**Analogs (two, composed):** `harness/commands/golden-approve.md` (human-gate wrapper shape) +
`harness/commands/pipeline.md` (multi-step composition + `subtask: true` shape).

**Frontmatter shape — copy exactly** (`harness/commands/golden-approve.md:1-7`):
```markdown
---
description: >-
  Use when a human reviewer has approved a proposed golden baseline and wants to promote it —
  wraps the human-gated approval tool, which refuses (exit 3) without an explicit human flag,
  an ADR reference, and a confirmation value. Invoke only after a human sign-off, never by an agent.
agent: orchestrator
---
```
`agent: orchestrator` is **locked** by ADR-0009's "no new graph command and no new persona"
precedent, cited directly by RESEARCH for `/adopt`. Add `subtask: true` (as `pipeline.md` does,
line 8) if `/adopt`'s sub-verbs (`discover`/`draft`/`apply`/`promote`) form a multi-step composed
flow rather than a single tool invocation — `pipeline.md` is the template for "renders/composes
several things, still one agent."

**Body shape — "thin macro, do NOT re-implement" pattern** (`golden-approve.md:9-19`):
```markdown
Thin macro over the **already-coded** refusal gate. Do NOT re-implement approval logic —
`tools.golden_runner.approve` already encodes "machines gate, humans ratify" (CMD-03, P9).

## Invocation

The case id and human signals are taken from `$ARGUMENTS` and passed **positionally** to the
approve module (no shell-string construction from arguments):

!`python -m tools.golden_runner.approve $ARGUMENTS`
```
`/adopt` should follow the identical "no shell-string construction from arguments" discipline —
this is also ADOPT-07's "임의 command 미실행" (no arbitrary command execution) fixture-proof
requirement; the command body must invoke fixed `python -m tools.adoption_apply...` argv forms, one
per sub-verb, never interpolate manifest/draft content into a shell string.

**Emitted, dual-runtime shape** (confirmed via live diff of the two emitted trees):
- `.claude/commands/pipeline.md` — frontmatter unchanged except a leading
  `# generated by tools.harness_emit — do not hand-edit` comment and the folded (non-block)
  `description: "..."` string; body byte-identical to the source.
- `.opencode/command/pipeline.md` — same transform (generated-comment + folded description);
  `agent`/`subtask` keys pass through unchanged (confirmed: `diff` shows only the frontmatter
  description-folding + comment-insertion, no key remapping for these two keys).

This is the exact SC-4 byte-identical round-trip `/adopt` must satisfy — write ONE source doc at
`harness/commands/adopt.md`; do not hand-edit either emitted copy.

---

### `harness/skills/brownfield-adoption/SKILL.md` (runbook skill, ADOPT-07)

**Analog:** `harness/skills/pipeline-map/SKILL.md` (frontmatter + opening sections read above).

**Frontmatter shape — copy exactly** (`harness/skills/pipeline-map/SKILL.md:1-8`):
```markdown
---
name: pipeline-map
description: >-
  Use when you need to trace a request across the pipeline dataflow, see which stage produces or
  consumes a given contract, or find the component agent that owns a stage — reads the declared
  [[components]]/[pipeline] topology via tools.harness_config. Consult when routing by stage instead
  of by language, or when an edge's contract does not line up end to end.
---
```
`name: brownfield-adoption` (matches the directory name, `harness/skills/brownfield-adoption/`, per
this repo's own convention — `pipeline-map` skill lives at `harness/skills/pipeline-map/`).
`description` must be a "use when / does X / invoke when Y" one-paragraph block, ≤1024 chars per
CLAUDE.md's Claude skill limits — mirror `pipeline-map`'s three-clause shape (use-when, what-it-does,
when-to-consult).

**Body shape** — `pipeline-map/SKILL.md` opens with a one-paragraph statement of what the skill
teaches ("How work flows through the harness as a map instead of a guess..."), then a `## <slot
name>` section describing the underlying data/module, then a `## Reading it via the loader` how-to
section. `brownfield-adoption/SKILL.md` should mirror this shape: opening statement of what the
skill teaches (the discover → draft → human review → promote → apply runbook), a section per stage
of that lifecycle, and concrete module references (`tools.adoption_scan`, `tools.adoption_apply`)
the same way `pipeline-map` references `tools.harness_config`. Keep body <~500 lines per CLAUDE.md's
"body < ~500 lines (target ~150)" emit-time limit.

---

## Fixture Reuse — the file-by-file findings VALIDATION's Wave 0 explicitly required

**`tools/adoption_scan/tests/fixtures/minirepo/` does not exist as a static directory.** It is a
**programmatically materialized** pytest fixture — `tmp_minirepo(tmp_path)` in
`tools/adoption_scan/tests/conftest.py:38-159` — not a checked-in file tree. Read in full (all 159
lines). Its docstring states explicitly: *"This same tree seeds Phase 27's future application
fixtures."* Contents built at test time under `tmp_path/minirepo/`:

| Item | Path | Purpose |
|---|---|---|
| (a) secret-by-path | `.env` | secret-path-glob exclusion |
| (b) secret-by-content | `sink/secret_config.py` (a credential-shaped literal, built by string concatenation so the fixture source itself never carries a contiguous credential-shaped literal — this repo's own secret-scan hook would otherwise refuse to write the fixture file) | secret-content-pattern exclusion |
| (c) binary | `binary.dat` (leading NUL bytes) | binary detection |
| (d) vendored | `node_modules/pkg/index.js` | vendor exclusion |
| (e) generated | `generated.py` (`# @generated` first-line marker) | generated exclusion |
| (f) over-cap | `assets/oversized.dat` (300 KiB) | size-cap, non-dump |
| (g1) source-dump (over-cap+segment) | `backups/repo-dump.txt` (300 KiB) | dump-path detection |
| (g2) source-dump (under-cap+banner) | `notes/full-context.txt` (repomix-style banner) | banner-marker detection |
| (h) hash-equal pair + hash-different sibling | `widget_a.py` == `widget_b.py`; `widget_a_modified.py` differs | preserve vs conflict dispositions (Plan 03) |
| (i) extensionless | `README` | ambiguous-file handling |
| (j) escaping symlink | `escape` → `/etc/passwd` | symlink-escape (skips test if unprivileged) |
| (k) manifest | `pyproject.toml` | language/manifest detection |
| (l) CI surface | `.github/workflows/ci.yml` (with a benign, concatenation-built comment shaped like a common CI credential-env-var reference, to exercise the false-positive path without embedding a real secret-shaped literal) | CI-surface detection |
| (m) test surface | `tests/test_widget.py` | test-surface detection |
| (n) ADR surface | `docs/adr/0001-decision.md` | ADR-surface detection |
| (o) marker-capable root file | `AGENTS.md` (carries literal BEGIN/END HARNESS-MANAGED markers) | marker-merge surface |
| (p) schema surface under contracts/ | `contracts/widget.schema.json` | positive schema-surface match |
| (q) CODEOWNERS surface | `.github/CODEOWNERS` | CODEOWNERS detection |
| (r) schema-looking file OUTSIDE contracts/ | `tools/widget_tool.schema.json` | negative-match proof |

Vocabulary is strictly domain-neutral (`widget`/`source`/`sink`) per GEN-04 — never
log-parser/dotnet/semiconductor terms. **No CRLF/BOM file exists in `tmp_minirepo` today** — every
`write_text`/`write_bytes` call above uses plain `\n` and no BOM.

**`tests/fixtures/workspace/{member-a,member-b}/` (repo-root level, NOT under `tools/`) — read file
tree directly:**
```
tests/fixtures/workspace/member-a/contracts/.hashes/manifest.json
tests/fixtures/workspace/member-a/contracts/greeting.schema.json
tests/fixtures/workspace/member-a/golden/greeting-edge/expected/baseline.verified.tsv
tests/fixtures/workspace/member-a/golden/greeting-edge/input/seed.tsv
tests/fixtures/workspace/member-b/contracts/.hashes/manifest.json
tests/fixtures/workspace/member-b/contracts/greeting.schema.json
```
This is a real, static, checked-in two-member workspace fixture (each member has its own
`contracts/` + hash manifest; `member-a` additionally has a `golden/` case). It is the exact shape
RESEARCH's Assumption A3 recommends reusing for the `client-server` fixture (2-repo scaffolding).

**Recommendation for the planner (confirming RESEARCH's Open Question 3), now with the actual
contents in hand:**
- `polyglot-single` fixture: **NEW**, but should be a **static, checked-in** tree (not a
  `conftest.py`-materialized `tmp_path` fixture like `tmp_minirepo`) since `tools/adoption_apply`'s
  own tests need a target with actual create/preserve/conflict/marker-merge dispositions applied and
  re-verified across a resume — a static tree under `tools/adoption_apply/tests/fixtures/
  polyglot-single/` is easier to diff/snapshot than a `tmp_path` fixture. It MAY structurally borrow
  individual synthetic elements from `tmp_minirepo` (e.g. the hash-equal/hash-different trio (h), the
  marker-capable root `AGENTS.md` (o)) but should NOT literally import/call `tmp_minirepo` — Phase 27
  needs its own `tools/adoption_apply/tests/conftest.py`, copying `adoption_scan`'s `sys.path` wiring
  pattern (lines 19-29) but NOT its `tmp_minirepo` fixture body (that fixture is scoped to Phase 26's
  scan/plan/destinations tests, not apply).
- `client-server` fixture: **extend/reuse** `tests/fixtures/workspace/{member-a,member-b}` — copy
  its two-member shape (each member with its own `contracts/`+hash-manifest) as the starting point,
  add adoption-relevant additions (e.g. an `AGENTS.md` in one member) as needed.
- `partial-collision-crlf` fixture: **NEW** — none of the existing fixtures carry a CRLF/BOM file
  today (confirmed: `tmp_minirepo` has none), so this fixture must synthesize one itself. Use
  `tools/harness_emit/merge.py::_normalize`'s own CRLF-handling contract as the semantic reference
  (`text.replace("\r\n", "\n").replace("\r", "\n")` — merge.py already treats CRLF as an input
  normalization case, giving `apply.py`/the fixture a known-correct behavior to assert against) and
  build the hash-equal/hash-different collision pair the same way `tmp_minirepo`'s item (h) does
  (`widget_a.py == widget_b.py`, `widget_a_modified.py` differs).

---

## Shared Patterns

### Atomic create-once (never overwrite)
**Source:** `tools/task_control/manager.py::_atomic_create` (lines 150-173) and
`tools/handoff/handoff.py::_atomic_write_once` (lines 130-161) — same idiom, two independently
audited instances.
**Apply to:** `apply.py`'s `create` disposition handler; any new task-local artifact write in
`batch.py`.
**Rule:** `tempfile.mkstemp` in the SAME directory as the target → write/flush/fsync → publish via
`os.link(tmp, path)` (raises `FileExistsError` on collision, no separate `exists()` check / no race
window) → best-effort parent-directory `fsync` → always `os.unlink(tmp)` in a `finally`. Never
`os.replace()` for a `create` disposition (silently overwrites, confirmed live by RESEARCH).

### CAS revision-guarded mutation
**Source:** `tools/task_control/manager.py::_cas_write` (lines 106-147).
**Apply to:** any batch-state mutation in `batch.py` — route through `tools.task_control.manager`'s
existing transition/attest calls rather than building a second lock/version scheme.
**Rule:** `fcntl.flock(LOCK_EX)` on a sidecar `.{name}.lock` file → re-read current state → compare
`current["revision"] == expected_revision` (else `TaskControlError`) → require
`next_state["revision"] == expected_revision + 1` exactly → validate → atomic-replace.

### Marker-fenced merge for shared files
**Source:** `tools/harness_emit/merge.py::splice_managed_block` / `merge_settings` (full file, 238
lines, read above); destination list `tools/adoption_scan/destinations.py::MARKER_CAPABLE` (line
101).
**Apply to:** `apply.py`'s `marker-merge` disposition handler — the ONLY 3 destinations:
`AGENTS.md`, `CLAUDE.md`, `.claude/settings.json`.
**Rule:** import and call these functions verbatim; never write a second fence/marker scheme
(RESEARCH explicitly forbids inventing a new `<!-- BEGIN ADOPTION-MANAGED -->` fence).

### Structural constitution-plane refusal
**Source:** `tools/hooks/contract_guard.py::CONSTITUTION_GLOBS` (line 43) +
`tools/harness_perms/resolver.py::resolve_path` (lines 47-49, full body:
`"deny" if any(fnmatchcase(path, glob) for glob in deny_globs) else "allow"`).
**Apply to:** `apply.py`, called per-destination, before any `open()`/`os.link()`/`os.replace()`.
**Rule:** import `CONSTITUTION_GLOBS` from `tools.hooks.contract_guard` (already a precedent import
direction — `destinations.py` does this too, line 87); never copy the literal
`["contracts/**", "docs/adr/**", "golden/**"]` a second time. This check is independent of, and in
addition to, the Claude-only `PreToolUse(Write|Edit)` hook — `apply.py` must be safe when invoked as
a bare CLI/subprocess with no Claude tool-call event in the loop at all.

### Refuse-by-default human-ratification gate
**Source:** `tools/golden_runner/approve.py::promote`/`GoldenApprovalRefused`/`main` (full file, 103
lines, read above); the same human-confirmation environment variable is also reused by
`contract_guard.py`.
**Apply to:** `approval.py`'s promotion path.
**Rule:** every required human signal (`--approve` flag, a reference, and an env-matched
confirmation value) is checked independently and raises immediately on the first missing one; CLI
`main()` catches the refusal exception and returns exit code `3`; the reference tuple
(`draft_hash`, `task_revision`, `git_ref`) is recomputed **fresh** at promotion time and compared by
exact equality — never cached, never fuzzy-matched (Pitfall 2).

### git ref / HEAD resolution
**Source:** `tools/task_control/manager.py::refresh_ref` and `tools/handoff/handoff.py::_git`
(`subprocess.run(["git", "-C", str(root), ...], text=True, capture_output=True, check=False)`).
**Apply to:** `approval.py`'s git-ref binding.
**Rule:** fixed argv shape only — never interpolate manifest/draft/scanned content into the argv
list (this is also the ADOPT-07 "no arbitrary command execution" fixture-proof requirement,
applying equally to `apply.py`/`batch.py`/`approval.py`).

### JSON Schema validation before use
**Source:** `tools/adoption_scan/cli.py:82-92` (`Draft202012Validator(schema).iter_errors(document)`
loop, sorted by error path).
**Apply to:** `approval.py`'s new `approval.schema.json` document; any batch-metadata document
`batch.py` writes.
**Rule:** validate every document against its schema before writing it to disk; on failure, print
the first error and return exit code `1` — matches the exact pattern already used for
`inventory`/`plan`/`manifest`.

## No Analog Found

None — every file in Phase 27's scope has at least a role-match analog already committed in this
repo. This is consistent with RESEARCH's framing: "Phase 27 is integration glue, not new
infrastructure."

## Metadata

**Analog search scope:** `tools/task_control/`, `tools/handoff/`, `tools/harness_emit/`,
`tools/golden_runner/`, `tools/hooks/`, `tools/harness_perms/`, `tools/adoption_scan/` (incl.
`tests/conftest.py` read in full), `tests/fixtures/workspace/`, `harness/commands/`,
`harness/skills/pipeline-map/`, `contracts/harness/task-control/attestation.schema.json`,
`contracts/harness/adoption/manifest.schema.json`, `.claude/commands/pipeline.md`,
`.opencode/command/pipeline.md` (diffed against source for the dual-runtime emit shape).
**Files scanned:** ~14 read directly this session (several in full, several by targeted grep+read).
**Pattern extraction date:** 2026-07-21
