"""Import-path wiring for skill_registry tests.

Mirrors tools/lifecycle_eval/tests/conftest.py: skill_registry is a *virtual* uv-workspace member
(not pip-installed), imported by module path from the repo root, so the tests must put the repo root
onto sys.path themselves. `tools` is a namespace package (no tools/__init__.py) — inserting the repo
root lets `from tools.skill_registry import ...` resolve.

Without this, the whole-repo `uv run pytest` still collects (a sibling member's conftest has already
inserted the root by then), but the isolated command `uv run pytest tools/skill_registry` errors at
collection — green under one invocation, red under the one that matters.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> skill_registry -> tools -> repo root  (parents[3]; mirrors harness_lint/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
