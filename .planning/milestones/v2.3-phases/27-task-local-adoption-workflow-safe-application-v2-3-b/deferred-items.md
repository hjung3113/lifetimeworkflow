# Deferred Items — Phase 27

Out-of-scope discoveries logged during execution, per executor scope-boundary rules
(only auto-fix issues directly caused by the current task's changes).

## 27-03: pre-existing `test_contracts_index.py` snapshot mismatch

- **Found during:** 27-03 post-task full-suite verification (`uv run pytest -q`)
- **Test:** `tools/memory_regen/tests/test_contracts_index.py::test_render_matches_committed_snapshot`
- **Symptom:** committed `.ambr` snapshot says "13 contract(s)"; live `contracts/` tree now has 14
  (the new `contracts/harness/adoption/approval.schema.json` from Plan 27-02).
- **Confirmed pre-existing:** identical failure reproduces at commit `0de779d` (27-02's completion
  commit, the last commit before 27-03 started) — `tools/memory_regen/tests/test_contracts_index.py`
  itself is byte-identical between `0de779d` and this plan's HEAD (`diff` empty).
- **Root cause:** 27-02 added a new constitution-plane contract (human-ratified, per its own
  blocking checkpoint) but the derived `.memory/derived/contracts-index.md` snapshot + its `.ambr`
  test fixture were not regenerated/rebaselined in that plan's scope.
- **Not fixed here:** out of scope for 27-03 (code-only plan; 27-03's `<critical_constraints>`
  explicitly forbid touching `contracts/` or the derived plane). Regenerating the derived plane and
  rebaselining the snapshot belongs to whichever plan owns `.memory/derived/contracts-index.md`
  maintenance next (likely folded into 27-02's own follow-up or a Wave-3/gate task before
  `/gsd:verify-work`).
