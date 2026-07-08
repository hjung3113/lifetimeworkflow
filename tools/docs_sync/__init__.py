"""docs_sync — the DOCS-03 contracts→reference generator (`/docs-sync`, CMD-08).

A virtual uv-workspace member (sibling of contract_hash/, golden_runner/, memory_regen/),
invoked by module path (`python -m tools.docs_sync`). It regenerates the Diátaxis **reference**
quadrant (``docs/reference/*.md``) MECHANICALLY from the contract schemas
(``contracts/**/*.schema.json``) so reference never drifts from the single source of truth and
is never hand-authored (DOCS-03 anti-feature). Only ``docs/reference/`` is generated — tutorials,
how-to and explanation stay human-authored.

Determinism discipline is cloned from ``tools/memory_regen/contracts_index.py``: rows→render→
write→main, a DERIVED "do not hand-edit" header, no ``datetime.now()`` and no raw floats, so
delete + regenerate is byte-identical (proven by a committed syrupy snapshot). Schemas are read
via the stdlib ``json`` module on the same path as ``tools.contract_hash`` — zero new deps and no
second hash/read implementation that could disagree with the drift gate.

The public API lives in :mod:`tools.docs_sync.generate` (``rows`` / ``render`` / ``write`` /
``main``); this package stays import-light so the test conftest can wire ``sys.path`` first.
"""
