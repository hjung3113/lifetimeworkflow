# Phase 29 — deferred items (out of scope for the plan that found them)

- **Pre-existing `E501` in `tools/harness_emit/tests/test_coexist.py`** (the
  `test_gsd_owned_claude_files_untouched_and_unlisted` docstring, 101 > 100 chars). Present at
  `HEAD` before plan 29-03 touched the file — verified by running ruff against the committed
  revision. 29-03 edits three unrelated literals in that file and deliberately does not reflow the
  docstring: it is not caused by this task's change. Same class as the pre-existing `I001` on
  `tools/adoption_apply/cli.py` carried in 29-CONTEXT D-15. Route to the v2.3 milestone audit's
  `tech_debt`.
