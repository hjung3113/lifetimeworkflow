"""Import-path wiring and shared agreement corpus for the memory_ui tests (Phase 16, MEM2-07).

memory_ui is a *virtual* uv-workspace member (not pip-installed), invoked by module path from the
repo root, so the tests must put the repo root (and libs/python) onto sys.path themselves. `tools`
is a namespace package (no tools/__init__.py) — inserting the repo root lets
`import tools.memory_ui...`, `from tools.agree.write import ...`, and
`from tools.harness_lint.agreements import ...` resolve.

The synthetic agreements corpus is re-exported from harness_lint so the route tests exercise the
SAME fixture the injector/lint suites use — NEVER the real ``.memory/agreements/`` (its active set
is legitimately empty; writing there would violate the tier contract).
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> memory_ui -> tools -> repo root  (parents[3]; mirrors memory_regen/tests/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
_LIBS_PYTHON = _REPO_ROOT / "libs" / "python"
for _p in (str(_REPO_ROOT), str(_LIBS_PYTHON)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from tools.harness_lint.tests.conftest import (  # noqa: E402, F401
    tmp_agreements_tree,  # synthetic active+retired+_TEMPLATE+README corpus — never real agreements
)
