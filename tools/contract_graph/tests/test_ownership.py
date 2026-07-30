"""MONO-04 owning_package() tests — domain-neutral synthetic fixtures throughout.

All hand-built fixtures use domain-neutral names (ids "root"/"a"/"b"/"core-pkg", folders like
"components/a", "components/a/sub") so this core-plane test stays GEN-04-clean (no instance-path
or domain-prose tokens) — mirrors test_compile.py's fixture convention.
"""

from __future__ import annotations

import pytest

from tools.contract_graph import owning_package


def test_root_package_owns_unenclosed_contract() -> None:
    """A lone root package (dir='.') encloses every path, including one with no other owner."""
    packages = [{"id": "root", "dir": "."}]
    assert owning_package(packages, "contracts/widget.schema.json") == "root"


def test_nearest_enclosing_package_wins_over_root() -> None:
    """A contract under a nested package's folder resolves to that package, not the root; a
    contract OUTSIDE that folder still resolves to root."""
    packages = [
        {"id": "root", "dir": "."},
        {"id": "a", "dir": "components/a"},
    ]
    assert owning_package(packages, "components/a/contracts/widget.schema.json") == "a"
    assert owning_package(packages, "contracts/widget.schema.json") == "root"


def test_deepest_ancestor_wins_over_shallower_ancestor() -> None:
    """Three nested enclosing packages (root -> components -> components/a) — the DEEPEST wins."""
    packages = [
        {"id": "root", "dir": "."},
        {"id": "a", "dir": "components"},
        {"id": "b", "dir": "components/a"},
    ]
    assert owning_package(packages, "components/a/contracts/widget.schema.json") == "b"


def test_synthetic_instance_style_fallback_documented() -> None:
    """THE required root-fallback proof (CONTEXT.md "Resolved after research" / Pitfall 4).

    A synthetic instance-style contract path — an instance-shaped subtree with no manifest of its
    own — falls back to the root package, exactly as the real reference instance's own contracts
    tree does today (no manifest exists at that instance's root). This assertion is deliberately
    built on SYNTHETIC data per the phase's hard constraint, never a literal live instance path.
    """
    packages = [
        {"id": "root", "dir": "."},
        {"id": "core-pkg", "dir": "components/core"},
    ]
    synthetic_instance_path = "instance/contracts/log-specs/widget.schema.json"
    assert owning_package(packages, synthetic_instance_path) == "root"


def test_no_root_package_raises_for_unenclosed_path() -> None:
    """No root package + no enclosing package -> ValueError, never a fabricated owner."""
    packages = [{"id": "a", "dir": "components/a"}]
    with pytest.raises(ValueError):
        owning_package(packages, "contracts/widget.schema.json")


def test_tie_break_is_deterministic_sorted_id() -> None:
    """Two packages sharing the identical dir (a contrived but legal input) -> the winner is the
    lexicographically smaller id, and the result is independent of input ordering."""
    packages_a_first = [
        {"id": "a", "dir": "components/shared"},
        {"id": "b", "dir": "components/shared"},
    ]
    packages_b_first = [
        {"id": "b", "dir": "components/shared"},
        {"id": "a", "dir": "components/shared"},
    ]
    contract_path = "components/shared/contracts/widget.schema.json"
    assert owning_package(packages_a_first, contract_path) == "a"
    assert owning_package(packages_b_first, contract_path) == "a"
