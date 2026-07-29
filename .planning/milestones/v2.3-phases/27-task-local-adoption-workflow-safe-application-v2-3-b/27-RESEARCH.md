# Phase 27: Task-Local Adoption Workflow + Safe Application (v2.3 B) - Research

**Researched:** 2026-07-20
**Domain:** Task-control-plane integration + atomic filesystem apply + command/skill emission (Python, this repo's own tooling — no external library research needed)
**Confidence:** HIGH (every claim below is grounded in this repo's own committed code, read directly — not training-data knowledge of a third-party framework)

## Summary

Phase 27 is **integration glue, not new infrastructure**. Every primitive ADOPT-04..07 needs
already exists and ships in this repo: the CAS state manager (`tools/task_control/manager.py`),
the evidence/HANDOFF/resume lifecycle (`tools/evidence/capture.py`, `tools/handoff/handoff.py`),
the constitution-plane deny hook (`tools/hooks/contract_guard.py`), the marker-merge splice
(`tools/harness_emit/merge.py`), and the deterministic inventory/plan/manifest pipeline
(`tools/adoption_scan/{scan,plan,destinations}.py`, Phase 26). Phase 27's job is to (1) give an
adoption run a `.workflow/tasks/<id>/artifacts/adoption/<batch>/` home inside the *existing*
task-packet transaction boundary, (2) write a new `apply.py` that walks a
`manifest.schema.json` disposition list and actually creates/marker-merges files with atomic,
collision-safe, idempotent semantics — refusing constitution-plane destinations *before* any
`open()` call, not merely relying on the Claude-only `contract_guard` PreToolUse hook — and
(3) author one thin `/adopt` command + `brownfield-adoption` skill that composes all of the
above, with a human-ratification gate modeled directly on `tools/golden_runner/approve.py`'s
refuse-by-default exit-3 pattern.

The single highest-risk finding: **`tools/hooks/contract_guard.py` is a Claude Code
`PreToolUse(Write|Edit)` hook — it only fires when Claude's own Write/Edit tool is invoked.** An
`apply.py` that does `os.replace()`/`os.link()` directly from Python bypasses it entirely. ADOPT-05's
"contracts/·docs/adr/·golden/ destination이 mutation 전에 거부되고" (destination refused *before*
mutation) is therefore not satisfiable by relying on the hook — Phase 27 MUST duplicate the
constitution-plane check as an explicit, structural pre-condition inside `apply.py` itself, reusing
`tools.hooks.contract_guard.CONSTITUTION_GLOBS`/`_on_constitution_plane` (or the raw glob list) as
DATA, never re-deriving the glob set. This is a "don't hand-roll the glob list, DO hand-roll the
structural gate" distinction the planner must get right.

**Primary recommendation:** Build `tools/adoption_apply/` (new package, sibling to
`tools/adoption_scan/`) with three modules — `apply.py` (the atomic/collision-safe/idempotent
writer + structural constitution refusal), `approval.py` (hash+revision+ref-bound approval record,
modeled on `attestation.schema.json` + `golden_runner/approve.py`'s refusal pattern), and `batch.py`
(the `.workflow/tasks/<id>/artifacts/adoption/<batch>/` layout + CAS/evidence/HANDOFF wiring) — then
author `/adopt` + `brownfield-adoption` as a thin composition layer with **no new persona** (route
through the existing `orchestrator` agent, exactly as ADR-0009 mandated "no new graph command and no
new persona" for `/pipeline`).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Inventory/plan/manifest generation | Deterministic tool (`tools/adoption_scan`) | — | Already shipped (Phase 26); Phase 27 only consumes its output — never re-implements scanning |
| Task-local batch storage + CAS binding | Deterministic tool (`tools/task_control`, new `tools/adoption_apply/batch.py`) | Filesystem (`.workflow/tasks/<id>/artifacts/adoption/<batch>/`) | The task packet is the existing transaction boundary; a batch is just a new artifact kind under it |
| Constitution-plane refusal | Deterministic tool (new structural check in `apply.py`, reusing `contract_guard.CONSTITUTION_GLOBS`) | Claude Code hook (`tools/hooks/contract_guard.py`) as a second, independent layer | The hook only covers Claude's own Write/Edit tool calls; the apply path must refuse structurally on its own, the hook is defense-in-depth, not the primary control |
| Atomic/collision-safe file apply | Deterministic tool (new `apply.py`, reusing the `os.link`/`os.replace`+temp-file idiom already in `manager.py`/`handoff.py`) | Filesystem (POSIX `O_EXCL`/`os.link`/`os.replace`) | Same idiom as the CAS state writer — do not invent a second atomic-write primitive |
| Marker-merge for `AGENTS.md`/`CLAUDE.md`/`.claude/settings.json` | Deterministic tool (existing `tools/harness_emit/merge.py`) | — | `splice_managed_block`/`merge_settings` already exist and are exactly the 3-path `MARKER_CAPABLE` set from `destinations.py` |
| Human ratification / approval binding | Human (CLI flag + confirmation value) + deterministic tool (new `approval.py`, modeled on `tools/golden_runner/approve.py`) | `attestation.schema.json` shape (constraint-level) as a sibling pattern, not a literal reuse | Same "machines gate, humans ratify" refuse-by-default pattern as `/golden-approve`; a NEW schema is needed because approval binds to draft-hash+task-revision+git-ref, a different shape than `attestation.schema.json`'s constraint-source binding |
| `/adopt` command + `brownfield-adoption` skill | Command/skill authoring layer (`harness/commands/`, `harness/skills/`) + emitter (`tools/harness_emit`) | Existing `orchestrator` persona (no new agent) | Mirrors `/pipeline`/`/golden-approve`: thin macro over already-coded tools, `agent: orchestrator` |
| Dual-runtime byte-identical emit | Emitter (`tools.harness_emit`) | GEN-04 core→example guard | Reused unchanged; Phase 27 adds new source docs, not new emitter logic |

## User Constraints

No CONTEXT.md exists for this phase (per orchestrator note). The ROADMAP.md "### Phase 27" goal
text and the four ADOPT-04..07 requirement clauses (REQUIREMENTS.md lines 26-29) are the locked
scope, reproduced verbatim below.

### Locked Decisions (= ROADMAP success criteria + ADOPT-04..07, treated as LOCKED)

**Goal (verbatim):** "결정론적 plan을 출하된 task control plane 위에서 재개 가능·사람
ratified·비파괴 adoption 워크플로로 전환한다." (Turn the deterministic plan into a resumable,
human-ratified, non-destructive adoption workflow, running on top of the already-shipped task
control plane.)

**Success criteria (verbatim, numbered per ROADMAP):**
1. `.workflow/tasks/<id>/artifacts/adoption/<batch>/` batch가 안전하게 재개되고, 변경된
   draft/ref/revision이 승인을 무효화한다. (A batch resumes safely; a changed draft/ref/revision
   invalidates approval.)
2. `contracts/`·`docs/adr/`·`golden/` destination이 mutation 전에 거부되고, 비-헌법 apply가
   atomic·collision-safe·idempotent하다. (Constitution destinations refused before mutation;
   non-constitution apply is atomic/collision-safe/idempotent.)
3. 3개 fixture(polyglot 단일·2-레포 client/server·partial/collision, 최소 하나 CRLF/BOM)가
   통과한다. (3 fixtures pass: single-repo polyglot, 2-repo client/server, partial-adoption/collision
   — at least one with CRLF/BOM.)
4. `/adopt` + `brownfield-adoption` skill이 두 런타임에 byte-identical 왕복(새 persona 없음, 모델
   id 없음)한다. (`/adopt` + skill round-trip byte-identical to both runtimes; no new persona, no
   model ID.)

**ADOPT-04** *(NEW+REUSE)*: 각 adoption batch가 `.workflow/tasks/<task-id>/artifacts/adoption/<batch-id>/`에
존재하며 inventory·plan·draft tree·question·conflict·source ref·task revision·artifact hash·approval을
기존 CAS·evidence·HANDOFF·resume lifecycle에 결합한다. (Each adoption batch lives at that path and
binds inventory/plan/draft-tree/question/conflict/source-ref/task-revision/artifact-hash/approval
into the *existing* CAS/evidence/HANDOFF/resume lifecycle.)

**ADOPT-05** *(NEW+REUSE)*: discovery/draft 모드는 task artifact root 안에서만 쓰고, apply 모드는
review된 비-헌법 파일을 atomically create·marker-merge하되 silent overwrite·동시 target drift를
거부하고 `contracts/`·`docs/adr/`·`golden/` destination을 mutation 전에 거부한다. (Discovery/draft
mode writes only inside the task artifact root; apply mode atomically creates/marker-merges
reviewed non-constitution files, refuses silent overwrite and concurrent target drift, and refuses
constitution destinations before mutation.)

**ADOPT-06** *(NEW+REUSE)*: promotion이 제안된 contract·golden·ADR·relationship authority·conflict·unknown을
다루는 사람 결정을 요구하며, 정확한 draft hash·task revision·git ref에 결합되어 입력 변경 시
승인이 무효화된다. (Promotion requires a human decision on proposed contract/golden/ADR/relationship
authority/conflict/unknown items; approval binds to exact draft hash + task revision + git ref and
is invalidated by any input change.)

**ADOPT-07** *(NEW+REUSE)*: 하나의 얇은 `/adopt` command와 `brownfield-adoption` skill이 결정론적
툴·기존 explorer/fan-out/orchestrator/task 게이트·promotion 워크플로·runbook을 조합하고, 3개
generic fixture(polyglot 단일 레포·2-레포 client/server·partial-adoption/collision)가
idempotence·임의 command 미실행·헌법 거부·emitter closure·GEN-04를 증명하며 최소 하나의 fixture는
CRLF·BOM 입력을 포함한다. (One thin `/adopt` command + `brownfield-adoption` skill composes
deterministic tools + the existing explorer/fan-out/orchestrator/task gates + the promotion
workflow + a runbook; the 3 generic fixtures prove idempotence, no arbitrary command execution,
constitution refusal, emitter closure, and GEN-04; at least one fixture carries CRLF/BOM input.)

### Claude's Discretion

No CONTEXT.md — everything not pinned by the verbatim text above is open, with these
research-derived recommendations (planner should treat as strong defaults, not hard locks):
- New package name/location: `tools/adoption_apply/` (sibling to `tools/adoption_scan/`).
- Approval record schema name/location: new `contracts/harness/adoption/approval.schema.json`
  (see "Contract Surface Question" below — do not silently extend `attestation.schema.json`).
- Whether `/adopt` is one command with sub-verbs (`discover`/`draft`/`apply`/`promote`) or several
  thin commands — research recommends **one command, argument-routed**, mirroring `/pipeline`'s and
  `/golden-approve`'s single-entry-point style, but this is not locked by ROADMAP text.
- Fixture reuse strategy for the 2-repo client/server fixture (see "The Three Fixtures" below).

### Deferred Ideas (OUT OF SCOPE)

- `tools/hooks/secret_scan.py:44-47`'s hardcoded near-twin secret-pattern list vs. the
  `gate-registry.json` registry `scan.py` reads — explicitly documented as a deferred seam by
  26.2-PLAN.md, "belongs in a dedicated phase or ADR." Phase 27 does **not** force this
  convergence; it only needs to know `scan.py`'s classification path (which Phase 27's inventory
  reuse depends on) already reads the *registry*, not the hook's private list.
  `tools/hooks/secret_scan.py` is a different consumer entirely (Claude tool-call gate), out of
  Phase 27's blast radius.
  - Residual accepted gaps from Phase 26.2 (WR-01 disposition): `secret_patterns[1]` still misses
    single-case-only (all-lowercase-or-all-uppercase) and all-numeric/digit-less secret-shaped
    values that don't meet its 2-of-3 charset rule. This is a documented, deliberate,
    conservative-direction gap in the registry Phase 27's inventory reuse inherits as-is — not a
    regression Phase 27 introduces, and not something Phase 27 is asked to fix (ADOPT-04..07 make
    no secret-pattern precision claim).
- Phase 28/29's DOCSUP-* human-docs registry, guard, and docs-drive-loop work — Phase 27 only needs
  to supply "seed data" for Phase 28/29 later (per ROADMAP Phase 28 `Depends on` line: "Phase 27은
  seed 데이터만 공급(슬립해도 machinery 비차단)" — Phase 27 supplies seed data only, and Phase 28's
  machinery must not be blocked even if Phase 27 slips). **Do not build Phase 28/29's docs registry,
  guard, or `/docs-update` in this phase.**
- Phase 25's graph compiler/query/conductor — Phase 27 does not touch `tools/contract_graph`; it
  only reuses `relationshipCandidate`'s shape (already duplicated, not `$ref`'d, in
  `plan.schema.json` per Phase 26/D-11) as the vocabulary for adoption's proposed relationships.
- `.NET`/xUnit/Verify golden-approval toolchain — irrelevant here; Phase 27 is pure-Python glue
  over existing Python tooling. No new external package is installed by this phase (see "Package
  Legitimacy Audit").

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ADOPT-04 | Adoption batch lives at `.workflow/tasks/<id>/artifacts/adoption/<batch>/`, binds inventory/plan/draft-tree/question/conflict/source-ref/task-revision/artifact-hash/approval into existing CAS/evidence/HANDOFF/resume | See "Task-Local Batch Layout" — reuses `tools/task_control/manager.py`'s `missing_artifacts()` artifact-kind convention (`artifacts/<kind>/<run-id>/`), `tools/evidence/capture.py`'s gate-run capture, `tools/handoff/handoff.py`'s snapshot/resume |
| ADOPT-05 | Discovery/draft writes confined to task artifact root; apply is atomic/collision-safe/idempotent create+marker-merge; constitution destinations refused before mutation | See "Atomic Apply Mechanism" + "Structural Constitution Refusal" — reuses `manager.py`'s `_atomic_create`/`_atomic_replace` idiom (verified via live `os.link`/`O_EXCL` snippets), `harness_emit/merge.py`'s `splice_managed_block`/`merge_settings` |
| ADOPT-06 | Promotion requires human decision on contract/golden/ADR/relationship-authority/conflict/unknown; approval bound to draft-hash+task-revision+git-ref, invalidated on input change | See "Approval Invalidation" — new schema modeled on `attestation.schema.json`'s shape + `golden_runner/approve.py`'s refuse-by-default CLI pattern |
| ADOPT-07 | Thin `/adopt` command + `brownfield-adoption` skill compose deterministic tools + existing explorer/fan-out/orchestrator/task gates + promotion + runbook; 3 fixtures prove idempotence/no-arbitrary-exec/constitution-refusal/emitter-closure/GEN-04, ≥1 fixture CRLF/BOM | See "The Three Fixtures" + "Command/Skill Authoring Pattern" — reuses `harness/commands/golden-approve.md` and `harness/commands/pipeline.md` as direct structural templates, `tools/harness_lint/tests/test_commands.py`/`test_skills.py` as the structural gate |

</phase_requirements>

## Standard Stack

### Core (all already present in this repo — no new installs)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `os`/`tempfile`/`hashlib`/`fcntl` | 3.11 (this repo's interpreter) | Atomic file create/replace, sha256 hashing, advisory locking | Already the exact toolset `tools/task_control/manager.py` and `tools/handoff/handoff.py` use for their own atomic writes — `apply.py` reuses the identical idiom, verified live in this session (see "Atomic Apply Mechanism") |
| `jsonschema` (Draft202012Validator) | already a workspace dependency (`tools/task_control/manager.py` imports it) `[VERIFIED: codebase grep]` | Validate the new approval record + reused adoption schemas | Same validator already used for every other task-control/adoption schema in this repo — no second JSON Schema library |
| pytest `>=8.4,<9` + syrupy 5.2.0 | pinned in root `pyproject.toml` (per CLAUDE.md Technology Stack) | Test framework, golden/snapshot fixtures for the 3 adoption fixtures | Repo-wide standard, already used by `tools/adoption_scan/tests/` |

**No new external package is required for this phase.** Everything ADOPT-04..07 needs is either
already a workspace member (`tools/task_control`, `tools/evidence`, `tools/handoff`,
`tools/harness_emit`, `tools/hooks`) or stdlib. This significantly lowers Phase 27's risk profile
relative to Phase 26 (which introduced the `tools/adoption_scan` package from scratch).

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `subprocess` (git plumbing) | stdlib | Resolve `git rev-parse HEAD`, `git diff --name-only` for ref/revision binding | Reuse the EXACT pattern already in `manager.py::refresh_ref`/`handoff.py::_git`, not a new git wrapper |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reusing `manager.py`'s atomic-create idiom (temp+`os.link`, `FileExistsError` on collision) | `os.open(path, O_CREAT\|O_EXCL)` directly | Both are POSIX-atomic and behave identically for collision detection (verified live, see below); `os.link` is preferred here ONLY because it is the idiom already audited/tested in this repo (`manager.py::_atomic_create`, `handoff.py::_atomic_write_once`) — introducing `O_EXCL` as a second idiom for the same problem is unnecessary divergence, not a correctness improvement |
| A brand-new `approval.schema.json` | Extending `attestation.schema.json` with adoption-specific fields | `attestation.schema.json` is `additionalProperties: false` and its shape (`constraints[]` with `constraint_id`/`source_path`/`source_sha256`/`applies_to_phases`/...) is *semantically* about constraint-source binding at CLARIFY/SPEC time, not draft-hash+revision+git-ref binding for a promotion decision — a new schema keeps D-11's "no cross-file $ref, duplicate the shape if reused" convention honest rather than overloading an unrelated contract |

**Installation:** none required.

**Version verification:** N/A — no new package. `jsonschema` and `pytest`/`syrupy` versions are
pinned at the workspace root and already verified current by Phase 24/25/26 research (see CLAUDE.md
Technology Stack table).

## Package Legitimacy Audit

**Not applicable — this phase installs no external packages.** All functionality is built from
this repo's own existing workspace members (`tools/task_control`, `tools/evidence`,
`tools/handoff`, `tools/harness_emit`, `tools/hooks`, `tools/adoption_scan`) plus Python stdlib.
The planner does not need a `checkpoint:human-verify` gate for package installation in this phase.

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│  /adopt command (harness/commands/adopt.md, agent: orchestrator)        │
│  thin macro — no business logic, argument-routed sub-verbs              │
└───────────────┬───────────────────────────────────────────────────────┬─┘
                 │ discover/draft                                        │ apply/promote
                 ▼                                                       ▼
┌───────────────────────────────┐                        ┌──────────────────────────────┐
│ tools/adoption_scan (Phase26) │                        │ tools/adoption_apply (NEW)    │
│  scan → plan → destinations   │──inventory/plan/manifest│  batch.py: create/resume batch│
│  (read-only, target untouched)│─────────────────────────▶  under .workflow/tasks/<id>/  │
└───────────────────────────────┘                        │  artifacts/adoption/<batch>/  │
                                                            │                              │
                                                            │  approval.py: hash+revision+ │
                                                            │  ref-bound human gate         │
                                                            │  (refuse-by-default, exit 3) │
                                                            │                              │
                                                            │  apply.py:                   │
                                                            │   1. structural constitution │
                                                            │      refusal (CONSTITUTION_  │
                                                            │      GLOBS, BEFORE any write)│
                                                            │   2. atomic create (temp +   │
                                                            │      os.link, FileExistsError│
                                                            │      = collision)            │
                                                            │   3. marker-merge (reuses    │
                                                            │      harness_emit/merge.py)  │
                                                            │   4. drift detect (re-hash   │
                                                            │      target at apply time vs │
                                                            │      draft-time hash)        │
                                                            └───────────────┬──────────────┘
                                                                            │ binds into
                                                                            ▼
                                            ┌───────────────────────────────────────────────┐
                                            │ EXISTING task control plane (v2.2, unmodified) │
                                            │  tools/task_control/manager.py — CAS state,    │
                                            │  transition()/attest()                         │
                                            │  tools/evidence/capture.py — gate_runs,         │
                                            │  redaction                                     │
                                            │  tools/handoff/handoff.py — generate/validate/  │
                                            │  fresh_session/resume                          │
                                            └─────────────────────────────────────────────────┘
```

### Recommended Project Structure

```
tools/adoption_apply/
├── __init__.py
├── __main__.py           # CLI: discover / draft / apply / promote sub-verbs (thin argparse over the modules below)
├── batch.py               # .workflow/tasks/<id>/artifacts/adoption/<batch-id>/ layout: create, resume, list draft tree
├── apply.py                # structural constitution refusal + atomic create + marker-merge + collision/drift detection
├── approval.py             # approval record: draft-hash + task-revision + git-ref binding, invalidation check, refuse-by-default gate
├── tests/
│   ├── conftest.py
│   ├── fixtures/
│   │   ├── polyglot-single/         # SC-3 fixture 1: single-repo polyglot target
│   │   ├── client-server/           # SC-3 fixture 2: 2-repo — REUSE tests/fixtures/workspace/{member-a,member-b} idiom (Phase 11/25's existing 2-member workspace fixture)
│   │   └── partial-collision-crlf/  # SC-3 fixture 3: partial-adoption/collision, MUST include a CRLF/BOM input file
│   ├── test_batch_layout.py
│   ├── test_atomic_apply.py         # collision, idempotence, concurrent-drift detection
│   ├── test_constitution_refusal.py # structural refusal BEFORE mutation, independent of the Claude hook
│   └── test_approval_invalidation.py

harness/commands/adopt.md            # thin macro, agent: orchestrator, models golden-approve.md/pipeline.md
harness/skills/brownfield-adoption/SKILL.md  # runbook: discover → draft → human review → promote → apply
contracts/harness/adoption/approval.schema.json  # NEW — draft-hash + task-revision + git-ref bound approval record
```

### Pattern 1: Task-Local Batch as a New Artifact Kind (ADOPT-04)

**What:** An adoption batch is NOT a new task-control concept — it is a new *artifact kind* under
the existing `artifacts/<kind>/<run-id>/` convention `manager.py::missing_artifacts()` already
enforces (`present = artifact_root.is_dir() and any(child.is_dir() and any(child.iterdir()) for
child in artifact_root.iterdir())`).

**When to use:** Any time a phase needs a new class of task-local, immutable, run-ID-addressed
output (this repo already does this for gate-run evidence artifacts — adoption batches are the
same shape: `artifacts/adoption/<batch-id>/{inventory.json, plan.json, manifest.json, draft/,
approval.json}`).

**Example:**
```python
# Source: tools/task_control/manager.py:223-235 (missing_artifacts), read directly this session
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
An adoption batch directory is `artifacts/adoption/<batch-id>/` — `<batch-id>` plays the role of
`<run-id>`. Nothing in `manager.py` needs to change; a batch simply satisfies this existing
convention. **Do not add `"adoption"` to `transitions.json`'s `required_artifacts_by_target_phase`
unless the planner deliberately decides adoption should gate a phase transition** — ADOPT-04's text
says batches "bind into" CAS/evidence/HANDOFF/resume, not that they become a hard phase-transition
prerequisite. This is a real open design choice the planner must make explicitly (see Open
Questions).

### Pattern 2: Atomic Create + Collision Detection (ADOPT-05)

**What:** `manager.py::_atomic_create` and `handoff.py::_atomic_write_once` already implement
exactly the primitive ADOPT-05 needs for a NEW file: write to a same-directory temp file, fsync,
then publish via `os.link(temporary, path)` — which raises `FileExistsError` if `path` already
exists, giving atomic "create, never silently overwrite" semantics for free. This was
independently re-verified live in this research session (not cited from training data):

```python
# Verified live in this session (scratchpad snippet), mirrors manager.py::_atomic_create
import os, tempfile
fd, tmp = tempfile.mkstemp(dir=parent, prefix=f".{path.name}.", suffix=".tmp")
with os.fdopen(fd, "wb") as h:
    h.write(payload); h.flush(); os.fsync(h.fileno())
try:
    os.link(tmp, path)          # raises FileExistsError if path already exists — this IS the
except FileExistsError:         # collision check; no separate os.path.exists() race window
    raise CollisionError(...)
finally:
    os.unlink(tmp)               # always clean up the temp link name
directory_fd = os.open(parent, os.O_RDONLY)
os.fsync(directory_fd); os.close(directory_fd)   # best-effort directory durability (not F_FULLFSYNC on macOS)
```
Independently confirmed both `os.open(path, O_CREAT|O_EXCL|O_WRONLY)` and this `os.link` pattern
raise `FileExistsError` identically on a pre-existing target — either is correct; **use the
`os.link` idiom because it is the one already tested and audited in this repo** (consistency > a
second correct-but-novel primitive).

**When to use:** Every `create` disposition from `manifest.schema.json`. For `preserve`/`conflict`
dispositions, apply must be a no-op (idempotent re-run) — the manifest already encodes hash-equal
= preserve, hash-different = conflict (see `destinations.py::disposition` steps 6/7), so `apply.py`
only needs to re-read the *current* target hash at apply time and compare against the hash
recorded in the manifest at draft time — if they differ, that is "concurrent target drift" (ADOPT-05's
explicit "동시 target drift를 거부"), and apply MUST refuse rather than either silently overwrite
or silently proceed on stale assumptions.

### Pattern 3: Structural Constitution Refusal, Independent of the Claude Hook (ADOPT-05)

**What:** `tools/hooks/contract_guard.py::decide(file_path, content, approved)` is the existing
constitution-plane deny logic — but it is wired as a Claude Code `PreToolUse(Write|Edit)` hook. It
fires ONLY when Claude's own Write/Edit tool is invoked with a target path; a Python script calling
`os.replace()`/`open(..., "w")` directly (which is exactly what `apply.py` must do to write files
under program control) **never triggers this hook**. Confirmed by reading `contract_guard.py`'s
`main()`: it parses a Claude tool-call event from stdin (`parse_event(read_stdin())`) — there is no
code path that inspects an arbitrary filesystem write made outside that hook's process invocation.

**Structural fix:** `apply.py` must import and call the SAME predicate the hook uses —
`tools.hooks.contract_guard.CONSTITUTION_GLOBS` (the raw glob list: `["contracts/**",
"docs/adr/**", "golden/**"]`) via `tools.harness_perms.resolve_path` — as an explicit precondition
BEFORE any write attempt, exactly the same way `destinations.py::disposition` step 2 already does
for CLASSIFICATION (`resolve_path(CONSTITUTION_GLOBS, rel) == "deny"` → `human-ratification-
required`). The manifest ALREADY marks every constitution-plane destination
`human-ratification-required` (never `create`/`marker-merge`) — so a correctly-implemented
`apply.py` that only ever executes `create`/`marker-merge` dispositions and REFUSES to execute
`human-ratification-required` (raising, not silently skipping) satisfies ADOPT-05 by construction,
with the glob check as a second, redundant, defense-in-depth assertion (never trust the manifest
alone — re-check the destination path itself, in case a manifest was hand-edited or is stale).

```python
# Reuse, don't re-derive — same idiom as destinations.py::disposition step 2
from tools.hooks.contract_guard import CONSTITUTION_GLOBS
from tools.harness_perms import resolve_path

def refuse_if_constitution(destination: str) -> None:
    if resolve_path(CONSTITUTION_GLOBS, destination) == "deny":
        raise ConstitutionRefusal(
            f"apply refused: '{destination}' is on the constitution plane "
            "(contracts/·docs/adr/·golden/) — human-ratification-required only, never auto-applied"
        )
```

**When to use:** Called at the START of every apply-mode file operation, before any `open()`/
`os.link()`/`os.replace()` call for that destination — not just once per batch, so a single
malformed/edited manifest row can never slip a constitution write through.

### Pattern 4: Marker-Merge Reuse for the 3 Marker-Capable Destinations (ADOPT-05)

**What:** `destinations.py::MARKER_CAPABLE = frozenset({"AGENTS.md", "CLAUDE.md",
".claude/settings.json"})` already names the exact 3 destinations that get `marker-merge`
disposition. `tools/harness_emit/merge.py::splice_managed_block` (for the two Markdown files) and
`merge_settings` (for the JSON file) are the ALREADY-SHIPPED, already-tested merge implementations
— confirmed idempotent (`splice_managed_block` docstring: "markers PRESENT → replace ONLY the
content between them... a second call is byte-identical"). `apply.py` must call these two functions
verbatim for the 3 marker-capable destinations, not write a third merge implementation.

**Anti-pattern to avoid:** Writing a new "adoption-specific" managed-block fence
(`<!-- BEGIN ADOPTION-MANAGED -->`) instead of reusing `harness_emit.merge`'s existing
`BEGIN_MARKER`/`END_MARKER`. That would create TWO fenced regions in the same file with different
semantics and no coordination — a maintenance and drift hazard the "don't hand-roll" section below
calls out explicitly.

### Anti-Patterns to Avoid

- **Re-deriving the constitution glob list.** `CONSTITUTION_GLOBS` is defined once, in
  `tools/hooks/contract_guard.py`. Both `destinations.py` (Phase 26) and the new `apply.py` (Phase
  27) must import it, never copy the literal `["contracts/**", "docs/adr/**", "golden/**"]` a
  second time — a copy that drifts is a silent security regression.
- **Relying on the Claude PreToolUse hook as the sole ADOPT-05 control.** It is a real, valuable
  second layer for interactive Claude sessions, but `apply.py` must be independently safe when
  invoked as a bare CLI/subprocess (e.g. from CI, or from a non-Claude-Code automation) — see
  Pattern 3.
- **Skipping the draft-time-hash vs. apply-time-hash re-check.** The manifest is generated once, at
  draft time. Time passes between draft and apply (a human reviews it). If the TARGET tree changed
  in that window (a real concurrent-drift scenario, not hypothetical — this is exactly what ADOPT-05
  names), applying against a stale manifest can silently overwrite a file the manifest never saw.
  `apply.py` must re-hash the current on-disk target immediately before each write and compare
  against the hash the manifest recorded, refusing on mismatch (same idiom `destinations.py`
  already uses for draft-time hash comparison, applied a second time at apply time).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Atomic create-once-never-overwrite | A new temp-file+rename scheme | `manager.py::_atomic_create`/`handoff.py::_atomic_write_once`'s `tempfile.mkstemp` + `os.link` + directory fsync idiom (copy the function, don't import it across package boundaries if that creates an awkward dependency — but copy the EXACT sequence, verified live this session) | Already audited, already has a documented fault-injection test path (`TASK_CONTROL_FAULT_AFTER_FSYNC`) proving crash-safety; a second hand-rolled atomic-write primitive is an unaudited copy of subtle POSIX semantics |
| CAS revision-guarded state mutation | A new lock/version scheme for adoption batch state | `tools/task_control/manager.py::_cas_write`'s `fcntl.flock` + explicit `expected_revision` check | This is literally what the task control plane already is; an adoption batch does not need its OWN CAS — it lives inside the SAME task packet's transaction boundary |
| Marker-fenced merge into shared files | A new fence/marker scheme for adoption-touched `AGENTS.md`/`CLAUDE.md`/settings | `tools/harness_emit/merge.py::splice_managed_block`/`merge_settings` | Already shipped, already idempotent-proven, already the ONLY 3 marker-capable destinations named in `destinations.py::MARKER_CAPABLE` — a second fence scheme fragments ownership of the same file |
| Human-ratification refuse-by-default gate | A new "are you sure" prompt pattern | `tools.golden_runner.approve`'s `GoldenApprovalRefused` (exit 3) pattern: explicit `--approve` flag + a reference (ADR id there, draft-hash+revision+ref here) + a confirmation value matching an env var an agent is instructed never to fabricate | Exact same trust model already proven in production for golden promotion; ADOPT-06 is structurally identical to `/golden-approve`'s problem, just with a different binding tuple |
| git ref / HEAD resolution | A new git wrapper | `manager.py::refresh_ref`'s and `handoff.py::_git`'s `subprocess.run(["git", "-C", str(root), ...], text=True, capture_output=True, check=False)` pattern | Same idiom, already handles non-repo/failure cases the same way everywhere else in this codebase |
| Command/skill authoring shape | A new frontmatter convention | `harness/commands/golden-approve.md`/`harness/commands/pipeline.md` (frontmatter: `description`, `agent: orchestrator`, optional `subtask: true`) validated structurally by `tools/harness_lint/tests/test_commands.py`/`test_skills.py` | These ARE the CMD-01..09 structural gate's expected shape; a new command that doesn't match this frontmatter shape fails the existing lint test, not a new one |

**Key insight:** Phase 27's entire risk surface is in the ~4% that is genuinely new (the atomic
apply + structural constitution refusal + approval-invalidation logic) — everything else is
composition of already-shipped, already-tested primitives. The planner should budget task/plan
effort accordingly: most of the plan is "wire A to B, write the new schema, write the new apply.py
with its own focused test suite," not "design a new subsystem."

## Common Pitfalls

### Pitfall 1: Treating the Claude hook as sufficient for ADOPT-05

**What goes wrong:** A plan implements `apply.py` as a pure Python writer and assumes
`contract_guard.py`'s PreToolUse hook will "catch" a constitution-plane write, because that's how
every OTHER constitution-plane write in this repo is protected.
**Why it happens:** Every existing constitution-plane protection in this codebase (contract_guard)
IS a Claude hook, so it's an easy pattern-match to assume the same mechanism covers a new Python
tool.
**How to avoid:** `apply.py` must carry its OWN structural refusal (Pattern 3 above), independent of
whether it's invoked by Claude, a human CLI, or CI.
**Warning signs:** A test suite for `apply.py` that only exercises the tool via a simulated Claude
tool-call event, never a bare CLI/subprocess invocation.

### Pitfall 2: Approval binding that doesn't actually invalidate on ref change

**What goes wrong:** An approval record stores `draft_hash` and `task_revision` but the "git ref"
binding is checked loosely (e.g., "ref starts with the same prefix" or "ref is any descendant") —
this defeats ADOPT-06's "입력 변경 시 승인이 무효화된다" (approval is invalidated by ANY input
change).
**Why it happens:** `handoff.py::validate()` DOES do a strict, exact-match ref check
(`handoff["current_ref"] not in {head, publication_parent}` — note even here there are exactly TWO
accepted values, not a fuzzy match), which is the right model to copy; a lazier implementation might
be tempted to accept "close enough."
**How to avoid:** Approval validity must be `draft_hash == recomputed_draft_hash AND task_revision
== current_state_revision AND git_ref == current_HEAD` — all three exact-equal, computed fresh at
apply time, never cached from approval time.
**Warning signs:** A test that only proves approval is REJECTED when task_revision changes, but
never independently proves it's ALSO rejected when only the draft content changes (same revision,
same ref, different draft bytes) or only the git ref changes (same revision, same draft, repo
advanced).

### Pitfall 3: Conflating "excluded" (GSD-owned) with "refused" (constitution) in apply.py

**What goes wrong:** `manifest.schema.json`'s `excluded[]` array (GSD-owned lanes,
`reason: "gsd-owned"`) and its `dispositions[]` array's `human-ratification-required` entries
(constitution plane) are structurally different — `excluded` items are never in `dispositions` at
all. A naive `apply.py` that iterates `dispositions` and applies everything not `human-ratification-
required` is correct; a naive `apply.py` that iterates the RAW destination catalog and checks a
disposition lookup dict defensively is more error-prone (a KeyError or default-to-create bug for an
excluded destination that never got a disposition entry).
**Why it happens:** The manifest's two-array shape (`dispositions` + `excluded`) is a deliberate
26-REVIEW.md design choice ("so a reviewer can tell 'excluded' apart from 'missed'") that a
downstream consumer must respect, not flatten.
**How to avoid:** `apply.py` iterates `manifest["dispositions"]` ONLY; it must never synthesize a
disposition for anything in `manifest["excluded"]` or absent from both arrays.
**Warning signs:** Apply-time code that does `dispositions.get(destination, "create")` (a silent
default) instead of failing loud on an unknown destination.

### Pitfall 4: Building a second glob-resolution engine for the apply-time drift check

**What goes wrong:** Re-hashing the target at apply time needs to walk the SAME destination the
manifest names, but a plan might introduce a fresh path-matching/globbing utility for "does this
destination still exist / what's its current hash" instead of reusing `hashlib.sha256` directly on
the resolved `Path`.
**Why it happens:** Overzealous abstraction — "I need a re-usable target-state-checker" when the
actual need is a single `Path(target_root) / destination` + `hashlib.sha256(...).hexdigest()`, the
exact one-liner `destinations.py::_existing_hash` already is.
**How to avoid:** Import and reuse `tools.adoption_scan.destinations._existing_hash` (or promote it
to a shared location if that private-name import is deemed too tight a coupling — the planner's
call, but the FUNCTION should not be reimplemented).
**Warning signs:** A new `_hash_file`/`compute_hash` helper appearing in `apply.py` that is
byte-for-byte the same 5 lines as `destinations.py::_existing_hash`.

## Code Examples

### Structural constitution refusal before any write (ADOPT-05)
```python
# Source: composed from tools/hooks/contract_guard.py (CONSTITUTION_GLOBS, read directly this
# session) + tools/adoption_scan/destinations.py::disposition step 2 (same predicate, different call site)
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

### Atomic, collision-safe, idempotent create (ADOPT-05) — verified live this session
```python
# Source: mirrors tools/task_control/manager.py::_atomic_create (read directly, then independently
# re-verified: os.link raises FileExistsError on an existing target — confirmed via a live snippet
# in this research session, not cited from memory)
import os, tempfile
from pathlib import Path

class CollisionError(ValueError):
    """The target already exists; apply refuses to silently overwrite (idempotent create only)."""

def atomic_create(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(tmp, path)
        except FileExistsError as exc:
            raise CollisionError(f"target already exists: {path}") from exc
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
```
Re-running `atomic_create` a second time with the SAME payload against the SAME (now-existing)
`path` raises `CollisionError` — this is deliberately NOT "idempotent" at the `atomic_create`
primitive level. Idempotence at the `apply.py` level comes from the manifest's own
`disposition` value: a re-run against an unchanged target re-resolves to `preserve` (hash-equal,
verified in "Pattern 2"), so `apply.py` never calls `atomic_create` a second time for that
destination — it's a no-op at the disposition-check layer, which IS how `destinations.py::disposition`
already models "create only when no existing file."

### Marker-merge reuse (ADOPT-05)
```python
# Source: tools/harness_emit/merge.py — read directly this session, already-shipped functions
from tools.harness_emit.merge import splice_managed_block, merge_settings
import json

# For AGENTS.md / CLAUDE.md:
existing_text = target_path.read_text(encoding="utf-8")
merged_text = splice_managed_block(existing_text, adoption_block_body)
# then atomic_replace(target_path, merged_text.encode())  -- reuse manager.py::_atomic_replace idiom

# For .claude/settings.json:
existing_settings = json.loads(target_path.read_bytes())
merged_settings = merge_settings(existing_settings)
# then atomic_replace(target_path, json.dumps(merged_settings, indent=2).encode() + b"\n")
```

### Refuse-by-default approval gate (ADOPT-06), modeled directly on `/golden-approve`
```python
# Source: pattern mirrors tools/golden_runner/approve.py::promote (read directly this session)
import os

APPROVAL_ENV_VAR_NAME = "GOLDEN_APPROVE_HUMAN"  # reuse the SAME env var name/precedent as /golden-approve

class AdoptionApprovalRefused(Exception):
    """CLI exit 3 — approval refused; the human-ratification path was not satisfied."""

def promote(batch_dir, *, approve: bool, draft_hash: str, task_revision: int, git_ref: str,
            confirmation: str | None) -> dict:
    if not approve:
        raise AdoptionApprovalRefused("REFUSED: promotion requires an explicit human --approve flag")
    reference_value = os.environ.get(APPROVAL_ENV_VAR_NAME)
    if not reference_value or confirmation != reference_value:
        raise AdoptionApprovalRefused("REFUSED: promotion requires the human confirmation value")
    # binding recomputed FRESH at promotion time, never trusted from a cached earlier call:
    current_draft_hash = _recompute_draft_hash(batch_dir)
    current_revision = _read_task_state_revision(batch_dir)
    current_ref = _git_head(batch_dir)
    if (draft_hash, task_revision, git_ref) != (current_draft_hash, current_revision, current_ref):
        raise AdoptionApprovalRefused(
            "REFUSED: draft hash / task revision / git ref changed since approval was recorded — "
            "approval invalidated, re-approve against the current state"
        )
    return _write_approval_record(batch_dir, draft_hash, task_revision, git_ref)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|---------------|--------|
| Phase 26: read-only inventory/plan/manifest, target tree never touched | Phase 27: the SAME manifest becomes the input to a real, mutating apply — but only after a human-ratified approval record binds it | Phase 27 (this phase) | The read-only/mutating boundary is now explicit and gated, not implicit; the manifest's `dispositionEnum` (already 6 values, already total) does not need to change — Phase 27 consumes it as-is |

**Deprecated/outdated:** None — this is the first phase to build the apply side; there is no prior
adoption-apply implementation to deprecate.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A new `contracts/harness/adoption/approval.schema.json` is the right call vs. extending `attestation.schema.json` | Alternatives Considered / Architectural Responsibility Map | If wrong, the planner wires ADOPT-06's approval into the wrong contract, requiring a hash rebaseline rework; LOW risk — both schemas are additive and the distinction (constraint-source binding vs. draft/revision/ref binding) is structurally clear from reading both schemas directly |
| A2 | `.workflow/tasks/<id>/artifacts/adoption/<batch-id>/` should NOT be added to `transitions.json`'s `required_artifacts_by_target_phase` (i.e., adoption is not itself a phase-gating artifact) | Pattern 1 / Open Questions | If wrong, some lane's phase transition should require an adoption batch before EXECUTE/VERIFY, which is a `contracts/harness/task-control/transitions.json` change (constitution-plane, human-ratified) the planner would need to schedule as a locked decision, not assume — flagged explicitly as an Open Question below, not silently decided |
| A3 | The 2-repo client/server fixture should reuse the existing `tests/fixtures/workspace/{member-a,member-b}` two-member layout (built for Phase 11/25) rather than a net-new fixture tree | The Three Fixtures | LOW risk if wrong — worst case is fixture duplication, not a correctness bug; but reusing an audited fixture is strictly safer than inventing file-tree shape assumptions from scratch |
| A4 | `/adopt` should be a single command with argument-routed sub-verbs rather than 3-4 separate commands (`/adopt-discover`, `/adopt-apply`, ...) | Claude's Discretion | If wrong, the planner needs 3-4 thin command files instead of 1 — mechanically equivalent effort, does not change any correctness property, purely a UX/composition-count judgment call not pinned by ROADMAP text |

## Open Questions (RESOLVED)

**RESOLVED (all three) — 2026-07-21, during `/gsd:plan-phase 27`.** Q1 and Q2 were put to the
human operator and decided; Q3 was closed by the pattern-mapping pass reading the fixture tree
file-by-file. No open question remains for execution. Note: no `CONTEXT.md` exists for this phase —
the decisions below were supplied directly to the planner as locked decisions D-01..D-08, and that
decision list (not a CONTEXT.md) is the provenance for any "locked" citation in the plans.

1. **Does an adoption batch gate any task-control phase transition, or is it purely additive
   evidence?**
   - What we know: ADOPT-04's text says a batch "binds into" (결합한다) the existing CAS/evidence/
     HANDOFF/resume lifecycle — it does NOT say a phase transition requires an adoption artifact.
     `transitions.json`'s `required_artifacts_by_target_phase` currently has no `"adoption"` entry
     for any lane.
   - What's unclear: whether the planner should treat "binds into" as "batch state changes flow
     through the SAME CAS/evidence/HANDOFF mechanics used by every other artifact kind" (no
     `transitions.json` change) or "adoption becomes a required gate for some lane" (a
     constitution-plane `transitions.json` edit, needing its own human-ratification checkpoint).
   - Recommendation: default to NO `transitions.json` change — ADOPT-04..07's text never mentions
     phase-gating, and `transitions.json` is constitution-plane (human-ratified); adding a
     requirement there is a separate, larger decision the planner should surface to the user
     explicitly rather than infer.
   - **RESOLVED:** recommendation adopted (locked decision **D-01**, human-decided). An adoption
     batch is purely additive evidence. `contracts/harness/task-control/transitions.json` is NOT
     edited by any plan in this phase. Gating adoption on a phase transition is deliberately
     deferred as a separate, larger decision.

2. **What exactly identifies a "batch"?** (`<batch-id>` format)
   - What we know: `task.json`'s `task_id` pattern is `^T-[0-9]{14}-[a-z0-9]+(?:-[a-z0-9]+)*$`
     (UTC timestamp + kebab slug). `evidence.json`'s artifact paths use `run-id` directories under
     `artifacts/<kind>/`.
   - What's unclear: whether `<batch-id>` should mirror the task-id shape (`B-<timestamp>-<slug>`)
     or be content-derived (e.g., a hash of the target ref + scan time), and whether re-running
     `discover` against the SAME target/ref should reuse an existing batch (resume) or always mint a
     new one.
   - Recommendation: content-derive `<batch-id>` from `(target_ref, discover-time UTC date)` so a
     same-day re-discover against an unchanged ref resumes the same batch directory (satisfying
     SC-1's "안전하게 재개" / "resumes safely"), and a materially different target/ref mints a new
     batch — but this needs explicit planner/user confirmation since it directly shapes the resume
     UX.
   - **RESOLVED:** recommendation adopted (locked decision **D-02**, human-decided). `<batch-id>` is
     content-derived from `(target_ref, discover-time UTC date)`, implemented in `batch.py` via
     `batch_id_for`. No `--batch-id` override in this phase — keeps the test surface small.

3. **Fixture domain-neutrality for the polyglot single-repo fixture.**
   - What we know: GEN-04 (`tools/harness_lint/tests/test_core_no_example_dep.py`) forbids core
     code/fixtures from depending on or naming the `examples/` instance content; Phase 26's own
     `minirepo` fixture already proved this pattern is achievable (domain-neutral vocabulary only).
   - What's unclear: what "polyglot" needs to mean for a domain-neutral fixture — Phase 26's
     `minirepo` fixture content wasn't read file-by-file in this research pass; the planner's Wave 0
     should re-verify its exact shape (language markers, manifest files) before deciding whether
     Phase 27's "polyglot single-repo" fixture is a NEW fixture or an EXTENSION of Phase 26's
     `minirepo` (adding a second language's manifest file, e.g. a `pyproject.toml` alongside a
     `package.json`, both empty/synthetic).
   - Recommendation: Wave 0 should read `tools/adoption_scan/tests/fixtures/minirepo/**` in full
     before deciding reuse-vs-new; this research pass did not exhaustively enumerate its contents.
   - **RESOLVED:** closed by the pattern-mapping pass (`27-PATTERNS.md`), which read the fixture
     tree file-by-file. Findings (locked decision **D-07**): `tools/adoption_scan/tests/conftest.py::tmp_minirepo`
     is a **programmatic** fixture (19 embedded cases, domain-neutral vocabulary) with **no CRLF/BOM
     file today**; `tests/fixtures/workspace/{member-a,member-b}/` (repo root) is a real static
     2-member fixture. Therefore: `polyglot-single` = new static fixture following the `tmp_minirepo`
     pattern, `client-server` = extends `tests/fixtures/workspace/`, `partial-collision-crlf` = built
     NEW because it carries the mandatory CRLF/BOM input. All domain-neutral per GEN-04.

## Environment Availability

Skipped — this phase has no external tool/service/runtime dependency beyond what's already
verified present for every other phase in this repo (Python 3.11 + the workspace's own
`uv`-managed dependencies, git, pytest). No new probe is needed.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest `>=8.4,<9` (uv workspace) + syrupy 5.2.0, same as Phase 26 |
| Config file | root `pyproject.toml` `[tool.pytest.ini_options]` (`testpaths` already includes `tools`) — plus a new `tools/adoption_apply/tests/conftest.py` for `sys.path` wiring (Wave 0), copying `tools/adoption_scan/tests/conftest.py`'s pattern |
| Quick run command | `uv run pytest tools/adoption_apply -q` |
| Full suite command | `uv run pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ADOPT-04 | Batch created under `.workflow/tasks/<id>/artifacts/adoption/<batch>/`; resumes safely across two `discover` invocations against an unchanged ref | unit | `uv run pytest tools/adoption_apply/tests/test_batch_layout.py::test_resume_safely -x` | ❌ Wave 0 |
| ADOPT-04 | Batch state changes flow through the existing CAS `_cas_write` (a stale `expected_revision` is rejected the same way any other task mutation is) | unit | `…test_batch_layout.py::test_batch_uses_existing_cas` | ❌ Wave 0 |
| ADOPT-05 | Discovery/draft mode never writes outside the task artifact root (path-confinement proof against an attempted escape) | unit | `…test_atomic_apply.py::test_draft_confined_to_artifact_root` | ❌ Wave 0 |
| ADOPT-05 | `apply.py` refuses every `contracts/`/`docs/adr/`/`golden/` destination BEFORE any filesystem write (mock/spy proves zero `open()`/`os.link()` calls for a refused destination) | unit | `…test_constitution_refusal.py::test_refuses_before_mutation` | ❌ Wave 0 |
| ADOPT-05 | A second `apply` run against an unchanged target is a no-op (idempotent) — target bytes identical before/after | unit | `…test_atomic_apply.py::test_idempotent_reapply` | ❌ Wave 0 |
| ADOPT-05 | A `create` disposition whose target was modified AFTER draft-time (concurrent drift) is refused, not silently applied | unit | `…test_atomic_apply.py::test_concurrent_drift_refused` | ❌ Wave 0 |
| ADOPT-05 | Marker-merge for the 3 `MARKER_CAPABLE` destinations reuses `harness_emit.merge` and is idempotent on re-apply | unit | `…test_atomic_apply.py::test_marker_merge_idempotent` | ❌ Wave 0 |
| ADOPT-06 | Approval refused (exit 3 / raises) without explicit `--approve` + human confirmation value, mirroring `/golden-approve` | unit | `…test_approval_invalidation.py::test_refused_without_human_confirmation` | ❌ Wave 0 |
| ADOPT-06 | Approval invalidated when ONLY draft hash changes (revision/ref unchanged) | unit | `…::test_invalidated_on_draft_change` | ❌ Wave 0 |
| ADOPT-06 | Approval invalidated when ONLY task revision changes | unit | `…::test_invalidated_on_revision_change` | ❌ Wave 0 |
| ADOPT-06 | Approval invalidated when ONLY git ref changes | unit | `…::test_invalidated_on_ref_change` | ❌ Wave 0 |
| **SC-1** | A batch under `.workflow/tasks/<id>/artifacts/adoption/<batch>/` resumes safely; changed draft/ref/revision invalidates approval | integration | `…test_approval_invalidation.py::test_sc1_full_resume_cycle` | ❌ Wave 0 |
| **SC-2** | Constitution destinations refused before mutation; non-constitution apply atomic/collision-safe/idempotent | integration | `…test_atomic_apply.py::test_sc2_full_apply_cycle` | ❌ Wave 0 |
| **SC-3** | 3 fixtures (polyglot single-repo, 2-repo client/server, partial/collision incl. CRLF/BOM) pass end-to-end | integration/snapshot | `uv run pytest tools/adoption_apply/tests/test_fixtures.py -q` | ❌ Wave 0 |
| ADOPT-07 | `/adopt` command + `brownfield-adoption` skill structurally valid (frontmatter, routing description) | unit | `uv run pytest tools/harness_lint/tests/test_commands.py tools/harness_lint/tests/test_skills.py -q` | ✅ exists (glob-driven, covers new files automatically) |
| ADOPT-07 | No arbitrary command execution — `apply.py`/`batch.py`/`approval.py` never `subprocess.run` an argv derived from manifest/draft content (only fixed git plumbing argv) | unit | `…test_atomic_apply.py::test_no_arbitrary_command_execution` | ❌ Wave 0 |
| **SC-4** | `/adopt` + skill round-trip byte-identical to both runtimes, no new persona, no model ID | gate | `uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude` | ✅ exists |
| ADOPT-07 | GEN-04 core→example independence still green after new fixtures/tools added | gate | `uv run pytest tools/harness_lint/tests/test_core_no_example_dep.py -q` | ✅ exists |
| D-01 (contract) | New `approval.schema.json` validates + drift gate green after rebaseline | gate | `uv run python -m tools.contract_drift.drift` | ✅ exists |
| repo invariant | Committed-derived plane fresh | gate | `uv run python -m tools.docs_sync && uv run python -m tools.memory_regen.contracts_index && git diff --exit-code -- docs/reference .memory/derived/contracts-index.md` | ✅ exists |
| repo invariant | `uv.lock` unchanged (no new package) | gate | `uv sync --all-packages && git diff --exit-code uv.lock` | ✅ exists |

### Sampling Rate

- **Per task commit:** `uv run pytest tools/adoption_apply -q`
- **Per wave merge:** `uv run pytest -q` + `uv run python -m tools.contract_drift.drift` +
  `uv run python -m tools.harness_emit.generate && git diff --exit-code -- .opencode .claude`
- **Phase gate:** Full suite green + contract-drift green + emit-drift green + GEN-04 green before
  `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tools/adoption_apply/pyproject.toml` — new workspace member (else `uv sync --all-packages` fails)
- [ ] `tools/adoption_apply/tests/__init__.py` + `conftest.py` — copy `tools/adoption_scan/tests/conftest.py`'s `sys.path` wiring pattern
- [ ] `tools/adoption_apply/tests/fixtures/{polyglot-single,client-server,partial-collision-crlf}/**`
  — the 3 SC-3 fixtures; Wave 0 must first **read `tools/adoption_scan/tests/fixtures/minirepo/**`
  in full** (not exhaustively enumerated in this research pass) and `tests/fixtures/workspace/
  {member-a,member-b}/**` before deciding new-vs-extend for each
- [ ] All `test_*.py` files marked ❌ above
- [ ] `contracts/harness/adoption/approval.schema.json` — new schema, human-ratified, paired with a
  `contracts/.hashes/manifest.json` rebaseline (constitution-plane write — needs the
  `GOLDEN_APPROVE_HUMAN` env value set in a human-run session, same as every prior contract-plane
  change in this repo's history)
- [ ] Framework install: **none** — pytest/syrupy/jsonschema already present

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-------------------|
| V2 Authentication | no | N/A — no user auth in scope |
| V3 Session Management | no | N/A |
| V4 Access Control | yes | Structural constitution-plane refusal (Pattern 3) is an access-control gate on a specific resource class (contracts/docs-adr/golden), enforced independent of caller identity — reuse `contract_guard.CONSTITUTION_GLOBS`, never re-derive |
| V5 Input Validation | yes | `jsonschema.Draft202012Validator` against `manifest.schema.json`/`plan.schema.json`/`inventory.schema.json`/new `approval.schema.json` — every document validated before use, same pattern as `manager.py::_validate_document` |
| V6 Cryptography | yes (hashing, not encryption) | `hashlib.sha256` for content-addressing/collision-detection only — never hand-roll a hash function; this repo already standardizes on sha256 hex digests everywhere (task revisions, evidence artifacts, contract-hash manifest) |
| V11 Business Logic | yes | The disposition totality rule (every destination exactly one of 6 dispositions, `test_dispositions.py::test_total`) is itself a business-logic integrity invariant `apply.py` must never violate by applying a destination absent from `dispositions[]` |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|----------------------|
| TOCTOU (time-of-check-to-time-of-use) between draft-time hash and apply-time write | Tampering | Re-hash the target immediately before each write, inside the same apply operation that performs the write — never trust a hash computed at an earlier discovery/draft phase without re-verifying at write time (Pitfall 2 pattern, generalized) |
| Silent overwrite of a human-authored file | Tampering / Repudiation | `os.link`-based atomic create (raises `FileExistsError` on an existing target) — verified live this session; never `os.replace()` for a `create` disposition (that silently overwrites, confirmed live: an `os.replace` over an existing file replaces its contents with no error) |
| Arbitrary command execution via manifest/draft content | Elevation of Privilege | `apply.py`/`batch.py`/`approval.py` must never build a `subprocess` argv from manifest/draft/inventory content — every `subprocess.run` call in this repo's task-control modules uses a FIXED argv shape (`["git", "-C", str(root), "rev-parse", "HEAD"]` etc.), never string-interpolated from scanned/proposed content; ADOPT-07 explicitly names "임의 command 미실행" (no arbitrary command execution) as a fixture-proven property |
| Approval replay across a rewound/rebased ref | Spoofing | Exact-equality binding on `(draft_hash, task_revision, git_ref)`, recomputed fresh at promotion time — never accept a "compatible" or "descendant" ref (Pitfall 2) |
| Secret leakage via a brownfield target's own tracked files reaching a committed evidence/handoff artifact | Information Disclosure | Reuse `tools.evidence.capture._refuse_if_sensitive` / `tools.handoff.handoff._refuse_handoff_pii` if adoption batch data ever flows into `evidence.json`/a HANDOFF — do not build a third redaction path; also inherit Phase 26.2's registry-driven secret classification (accepted residual gaps documented in "Deferred Ideas" above) rather than re-deriving secret detection |

## Sources

### Primary (HIGH confidence — repo code read directly this session)
- `tools/task_control/manager.py` — CAS write (`_cas_write`), atomic create/replace idioms, `transition`/`resume`/`block`/`attest`, artifact-presence convention (`missing_artifacts`)
- `tools/handoff/handoff.py` — snapshot/generate/validate/fresh_session/activate/resume/`require_resume_attestation`/`refresh_resume_attestation`
- `tools/evidence/capture.py` — evidence capture, `_refuse_if_sensitive` (partially read; redaction entrypoint confirmed)
- `tools/hooks/contract_guard.py` — `CONSTITUTION_GLOBS`, `decide()`, PreToolUse-only scope (confirmed: parses a Claude tool-call event from stdin, no generic filesystem-write coverage)
- `tools/harness_emit/merge.py` — `splice_managed_block`, `merge_settings`, `MARKER_CAPABLE`-matching `BEGIN_MARKER`/`END_MARKER`/`HARNESS_HOOK_GROUPS`
- `tools/golden_runner/approve.py` — `promote()`, `GoldenApprovalRefused`, refuse-by-default human-confirmation pattern
- `tools/adoption_scan/destinations.py` — `destination_catalog`, `disposition` (7-step chain), `MARKER_CAPABLE`, `DERIVED_GLOBS`, `_existing_hash`, `harness_proposed_hash(es)`, `build_manifest`
- `contracts/harness/adoption/{inventory,plan,manifest}.schema.json` — full schemas read
- `contracts/harness/task-control/{task,state,evidence,attestation,transitions}.schema.json` and `gate-registry.json`, `transitions.json` — full contracts read
- `tools/task_packet/transitions.py` — `is_transition_allowed`, `required_artifacts_for_phase`
- `harness/commands/golden-approve.md`, `harness/commands/pipeline.md` — direct command-authoring templates
- `tools/harness_lint/tests/test_commands.py` (partial), directory listing of `tools/harness_lint/tests/` (GEN-04 and CMD-01..09 gate locations confirmed)
- `.planning/ROADMAP.md` §Phase 24-29, `.planning/REQUIREMENTS.md` ADOPT-04..07
- `.planning/phases/26-.../26-VERIFICATION.md`, `26-VALIDATION.md` — Phase 26's actual shipped state, disclosed gaps (secret-pattern precision), Validation Architecture template this file mirrors
- `.planning/ROADMAP.md` line 594 (26.2 "Out of scope" note) — the `secret_scan.py` hardcode deferral, confirmed still-deferred (not touched by Phase 27's scope)
- Live-verified in this session (not cited from training data): `os.open(O_CREAT|O_EXCL)` and
  `os.link` both raise `FileExistsError` on an existing target; `os.replace` silently overwrites —
  three Python snippets executed via Bash, output captured

### Secondary (MEDIUM confidence)
- `docs/adr/0009-contract-relationship-graph-model.md` (grep-scoped read) — "no new graph command
  and no new persona" precedent for `/pipeline`, applied here as a pattern for `/adopt`'s
  `agent: orchestrator` choice, not independently re-derived from a fresh design discussion
- `tools/contract_graph/tests/test_cross_repo_authority.py` — confirms the existing
  `tests/fixtures/workspace/{member-a,member-b}` two-member fixture as reusable 2-repo scaffolding,
  read partially (header + fixture path constants), not its full member-a/member-b file contents

### Tertiary (LOW confidence)
- `tools/adoption_scan/tests/fixtures/minirepo/**` — referenced by name (per 26-VALIDATION.md Wave
  0 requirements text) but NOT read file-by-file in this research pass; flagged explicitly in Open
  Question 3 as a planner Wave-0 action item, not asserted as fact here

## Metadata

**Confidence breakdown:**
- Standard stack / don't-hand-roll: HIGH — every primitive is read directly from this repo's own
  committed source, not inferred from a third-party library's documentation
- Architecture / atomic-apply mechanism: HIGH — the core POSIX semantics claim (`os.link`/`O_EXCL`
  raise `FileExistsError` on collision, `os.replace` silently overwrites) was independently
  re-verified with live Python snippets in this session, not merely cited from the existing code
- Constitution-refusal gap (hook-only coverage): HIGH — confirmed by reading `contract_guard.py`'s
  `main()` end to end; this is the single most load-bearing finding in this document and is
  evidence-based, not assumed
- Fixture reuse plan (Pitfall/Open Question 3): MEDIUM — the `minirepo` fixture's exact contents
  were not read; the planner must close this gap in Wave 0
- Contract-surface question (new `approval.schema.json` vs. extending `attestation.schema.json`):
  MEDIUM — a defensible reading of both schemas' `additionalProperties: false` shapes, but not a
  question this research session put to a human; flagged in the Assumptions Log

**Research date:** 2026-07-20
**Valid until:** 30 days (this is a same-repo, same-milestone integration phase; the underlying
task-control/emitter/hook code is stable and CODEOWNERS-gated, low churn risk within that window)
