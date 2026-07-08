"""Import-path wiring for the harness_perms tests (CONFIG-02, D-03).

Mirrors tools/memory_regen/tests/conftest.py exactly: harness_perms is a *virtual* uv-workspace
member (not pip-installed), imported by module path from the repo root, so the tests must put the
repo root onto sys.path themselves. `tools` is a namespace package (no tools/__init__.py) — inserting
the repo root lets `from tools.harness_perms import ...` resolve.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> harness_perms -> tools -> repo root  (parents[3]; mirrors memory_regen/conftest.py)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
