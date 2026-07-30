"""MONO-03 INSTANCE-config consistency gate (example leg) — mirrors the core
`test_package_facts_override.py` (`tools/harness_lint/tests/`), but proves the instance overlay's
own `[[components]]` declarations (`parser`/`converter`/`scheduler`/`collector`) layer cleanly
over derived package facts with zero edits.

This runs ONLY in the example leg: the root pytest `testpaths` excludes `examples/`, so this file
is invisible to the core suite (`uv run pytest`) and runs only under
`uv run pytest examples/log-parser/tests`. Placed here (not under `tools/harness_lint/tests/`) so
the literal `examples/` path segment this file's own location requires never appears inside
`tools/` (GEN-04), mirroring `test_pipeline_topology.py`'s exact placement/precedent.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import components, effective_packages, load_project

# test_package_facts_override_instance.py -> tests -> log-parser (the instance root).
_EXAMPLE_ROOT = Path(__file__).resolve().parents[1]
_OVERLAY = _EXAMPLE_ROOT / "project.toml"


def _overlay() -> dict:
    return load_project(_OVERLAY)


def test_instance_config_loads_through_effective_packages_with_zero_edits() -> None:
    """The unedited instance overlay config resolves through effective_packages()."""
    cfg = _overlay()
    effective_packages(cfg)  # must not raise


def test_instance_declared_components_are_either_overridden_or_declared_only() -> None:
    """Every declared instance component id survives into the effective output."""
    cfg = _overlay()
    declared_ids = {c["id"] for c in components(cfg)}
    effective_ids = {pkg["id"] for pkg in effective_packages(cfg)}
    missing = sorted(declared_ids - effective_ids)
    assert not missing, (
        f"declared component id(s) {missing} vanished from effective_packages() output — every "
        "declared component must survive as either an override or a declared-only entry"
    )
