"""Import-path wiring for the strangler_guard tests (CMD-06).

Mirrors tools/docs_sync/tests/conftest.py: strangler_guard is a *virtual* uv-workspace member (not
pip-installed), invoked by module path from the repo root. `tools` is a namespace package (no
tools/__init__.py), so the tests put the repo root onto sys.path themselves — letting
`import tools.strangler_guard...` resolve when pytest is pointed at this file directly.
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests -> strangler_guard -> tools -> repo root (parents[3]; mirrors golden_runner/conftest.py).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
