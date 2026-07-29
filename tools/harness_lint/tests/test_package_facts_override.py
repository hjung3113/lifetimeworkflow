"""MONO-03 CORE-config consistency gate — [[components]] layers cleanly over derived package facts.

Mirrors test_pipeline_config.py's "load real config -> iterate -> assert agreement, fail loud"
idiom. Runs against the GENERIC core default (harness/project.toml) ONLY — the instance overlay's
own leg-appropriate gate lives under the example instance's own test tree (GEN-04: no literal
instance-path string is permitted in anything under tools/).
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import components, effective_packages, load_project

# test_package_facts_override.py -> tests -> harness_lint -> tools -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_core_config_loads_through_effective_packages_with_zero_edits() -> None:
    """The unedited core config (harness/project.toml) resolves through effective_packages()."""
    cfg = load_project()
    effective_packages(cfg)  # must not raise


def test_core_declared_components_are_either_overridden_or_declared_only() -> None:
    """Every declared component id survives into the effective output (override or declared-only)."""
    cfg = load_project()
    declared_ids = {c["id"] for c in components(cfg)}
    effective_ids = {pkg["id"] for pkg in effective_packages(cfg)}
    missing = sorted(declared_ids - effective_ids)
    assert not missing, (
        f"declared component id(s) {missing} vanished from effective_packages() output — every "
        "declared component must survive as either an override or a declared-only entry"
    )
