# Phase 9: Self-Maintaining Derived Artifacts + Curator - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-07-13
**Phase:** 9-self-maintaining-derived-artifacts-curator-v2-0
**Areas discussed:** Committed-derived set (KEY DECISION), Curator authority & invocation, Stale-derived gate + failure UX, Hook posture (on-write vs PR/CI)

---

## Committed-derived set (KEY DECISION)

| Option | Description | Selected |
|--------|-------------|----------|
| docs/reference + contracts-index | Commit & gate contracts-index (cheap, deterministic drift signal); repo-map stays gitignored/session (PageRank churn). docs/reference already committed. | ✓ |
| docs/reference only | Status quo committed set; both .memory/derived artifacts stay session-ephemeral and ungated. | |
| All derived (incl. repo-map) | Max drift coverage; expect frequent gate trips from repo-map churn. | |

**User's choice:** docs/reference + contracts-index
**Notes:** Resolves the α open decision from PROJECT.md. contracts-index flips gitignored→committed; repo-map deliberately stays session-ephemeral (churn = noise, not signal).

---

## Curator authority & invocation

| Option | Description | Selected |
|--------|-------------|----------|
| Command + agent, derived-only writes | /refresh-memory command PLUS a read-mostly curator agent; hard-deny writes outside derived paths. | ✓ |
| Command only | Just /refresh-memory wrapping the generators; no agent persona (not conductor-delegatable). | |
| Agent only | Curator subagent, no standalone command; fewer human/CI entry points. | |

**User's choice:** Command + agent, derived-only writes
**Notes:** Curator derives from the read-only persona template; writes only derived paths, hard-deny constitution/golden/source.

---

## Stale-derived gate + failure UX

| Option | Description | Selected |
|--------|-------------|----------|
| Separate job, actionable fix message | Standalone stale-derived job mirroring emit-drift; fail-on-diff + prints exact fix command. | ✓ |
| Fold into emit-drift job | One combined freshness job for emit + memory; couples two concerns. | |
| Separate job, minimal message | Fail-on-diff only, no guidance text. | |

**User's choice:** Separate job, actionable fix message
**Notes:** Mirrors the Phase-7 re-emit-diff contributor ergonomics; message is copy-pasteable.

---

## Hook posture (on-write vs PR/CI)

| Option | Description | Selected |
|--------|-------------|----------|
| No on-write memory hook | Local /refresh-memory + PR/CI gate; format-on-write + SessionStart inject already cover cheap/session refresh. | ✓ |
| Cheap on-write touch only | On-write refresh of one cheap deterministic index; heavy regen deferred. | |
| SessionStart-only refresh | Regen on session start, nothing on-write. | |

**User's choice:** No on-write memory hook
**Notes:** MAINT-03 compliant — commits stay fast/quiet; no heavy per-commit local regeneration.

---

## Claude's Discretion

- Exact CI job wiring, command file layout, and the precise tracked path for the flipped
  `contracts-index` (plus the paired `.gitignore` amendment) — left to planner/researcher.

## Deferred Ideas

- Committing/gating `repo-map` — deferred (PageRank churn); revisit if a low-churn ranking or an
  order-insensitive diff makes it a reliable signal.
