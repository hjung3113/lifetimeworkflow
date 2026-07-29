---
updated: "2026-07-30"
---

# progress — terse running log (COMMITTED)

> DATA AUTHORITY — on a data conflict, `contracts/` and `docs/adr/` win over
> `.memory/state/`. This is a session progress log, not a reason to re-verify grounded work.
> No secrets/PII. Durable decisions go in append-only `docs/adr/`, not here.

## Recently done (last 5)

- v1.0 (phases 1–8), v2.0 (9–11), v2.1–v2.3 and now **v2.5**: complete + archived.
- **v2.5 De-ceremony shipped 2026-07-30** — 8 phases (39–46), 33 plans, 16/16 requirements,
  net −27,398 LOC outside `.planning/`. ADR-0012 made CI and the merge the authority; human-authored
  gates 5 kinds → 0; constitution plane 4 → 3 members; product gained 4 routes + `/flow`.
- **Milestone-close PR #5** — the first CI run on any v2.5 work (`ci.yml` is `pull_request`-only),
  all 11 jobs plus `gate` green, which finally satisfied Phase 43's SC-1.
- **PR #6 closed the four leftovers** — ADR-0013 (retires ADR-0008, ratifies "a path cited by an
  accepted ADR is corrected or marked historical, never deleted"), the two `docs/glossary.md` rows,
  the README test counts 982 → 881, and D-24 accepted as a documented residual.
- **Archived + tagged `v2.5`** (`e3b3cd2`) — two stale declarations corrected first rather than
  preserved by the archive: phases 43–46 unchecked in ROADMAP, and CER-01/02/03 reading
  `Not started`.

## Remaining

- **v2.6 Minimal Monorepo Core (phases 47–50)** — scoped, not started: package facts, convention
  profiles, contract impact, `harness-author` + managed adopt. Start with `/gsd:new-milestone`.
- Carried debt (detail in `.planning/milestones/v2.5-ROADMAP.md`): the core suite's six-test coupling
  to the reference instance (deferred whole — four of the six are ADR-0002's design); GEN-04's
  `_CORE_ROOTS` seeing neither `pyproject.toml` nor `.github/`; `ci.yml` giving no CI signal until a
  milestone's close PR; VERIFICATION.md absent for phases 40/44/45/46, recorded not backfilled.
