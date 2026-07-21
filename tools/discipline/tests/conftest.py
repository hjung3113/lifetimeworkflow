"""Import-path wiring for discipline tests.

Mirrors tools/lifecycle_eval/tests/conftest.py: discipline is a *virtual* uv-workspace member (not
pip-installed), imported by module path from the repo root, so the tests must put the repo root
onto sys.path themselves. `tools` is a namespace package (no tools/__init__.py) — inserting the
repo root lets `from tools.discipline import ...` resolve.

Without this, the whole-repo `uv run pytest` still collects, because a sibling member's conftest
has already inserted the root by then — but an isolated `uv run pytest tools/discipline` errors at
collection. Green under one invocation, red under the one that matters. That exact split cost a
red CI job in v2.3 (lifecycle_eval) and was rediscovered here when phase 36 added a module-scope
`import tools.discipline.check` to the task_control tests.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> discipline -> tools -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
