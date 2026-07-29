"""adoption_scan — deterministic read-only brownfield inventory + mapping (ADOPT-01/02/03).

A virtual uv-workspace member (sibling of contract_hash/, docs_sync/, memory_regen/), assembled
from four existing repo primitives rather than a fresh scanning engine (D-07): the confined +
symlink-guarded walk idiom (``tools/memory_regen/repo_map.py``), the locally-owned
``SECRET_CONTENT_PATTERNS`` tuple (inlined byte-identical from the Phase-42 task-control
registry contract's ``secret_patterns`` array, Phase 42 Plan 03; no runtime read of that contract,
which Phase 44 (CER-08) deleted), the repo's last-wins glob resolver
(``tools.harness_perms.resolve_path``), and stdlib ``hashlib.sha256`` content hashing.

This plan (26-02) ships the read-only enumeration + exclusion-classification + detection core:

1. ``scan.py`` — ``enumerate_target()`` / ``classify_exclusions()`` / ``build_inventory()``:
   confined, read-only, size-capped enumeration with recorded (never silently dropped)
   exclusions, and full ``inventory.json``-shaped assembly (ADOPT-01).
2. ``detect.py`` — language / manifest / documentation / CI / test-surface / candidate-process-
   boundary detection, wired into ``build_inventory()``'s four detection arrays, following D-02's
   conservative observed/inferred bias (never ``observed`` for an inferred component boundary).

Determinism discipline (delete + regenerate byte-identical): sorted walk, sorted emission,
repo-relative POSIX paths, no timestamps, canonical JSON writer
(``sort_keys=True, indent=2, ensure_ascii=True``). Read-only w.r.t. the scanned target: the
target tree's every file is byte-identical before and after any scan (proven by
``tests/test_readonly.py``).

Plan 03 layers ``plan.py`` (evidence-classified mapping plan) and ``destinations.py`` +
``cli.py`` (total disposition manifest + module entrypoint) on top of this core.
"""
