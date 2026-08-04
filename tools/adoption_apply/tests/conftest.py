"""Import-path wiring for tools/adoption_apply tests.

adoption_apply is a virtual uv-workspace member (not pip-installed), imported by module path
from the repo root. The tests must put the repo root onto sys.path themselves so that
``from tools.adoption_apply import batch`` resolves. Mirrors
``tools/adoption_scan/tests/conftest.py``'s wiring section exactly — this file intentionally
does NOT carry a ``tmp_minirepo``-style fixture; that fixture is scoped to Phase 26's own
scan/plan/destinations tests, not apply.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# tests -> adoption_apply -> tools -> repo root (parents[3]; mirrors adoption_scan/tests/conftest)
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """The repository root."""
    return _REPO_ROOT


@pytest.fixture()
def tmp_pnpm_target(tmp_path: Path) -> Path:
    """A small synthetic pnpm workspace target (52-03's own fixture, neutral vocabulary — GEN-04):
    root + ``apps/widget-app`` + ``packages/widget-shared``, a ``pnpm-workspace.yaml`` declaring
    ``apps/*``/``packages/*``, and a root ``package.json`` with ``lint``/``test`` scripts — the
    OBS-D-03/D-12 derivation input."""
    target = tmp_path / "pnpm-target"
    target.mkdir()
    (target / "pnpm-workspace.yaml").write_text(
        "packages:\n  - 'apps/*'\n  - 'packages/*'\n", encoding="utf-8"
    )
    (target / "package.json").write_text(
        json.dumps(
            {
                "name": "widget-workspace-root",
                "private": True,
                "scripts": {"lint": "eslint .", "test": "vitest run"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    apps_dir = target / "apps" / "widget-app"
    apps_dir.mkdir(parents=True)
    (apps_dir / "package.json").write_text(
        json.dumps({"name": "widget-app", "dependencies": {"widget-shared": "workspace:*"}}) + "\n",
        encoding="utf-8",
    )
    (apps_dir / "index.js").write_text("console.log('widget-app');\n", encoding="utf-8")

    packages_dir = target / "packages" / "widget-shared"
    packages_dir.mkdir(parents=True)
    (packages_dir / "package.json").write_text(
        json.dumps({"name": "widget-shared"}) + "\n", encoding="utf-8"
    )
    (packages_dir / "index.js").write_text("module.exports = {};\n", encoding="utf-8")

    return target
