"""PROD-01: fixture-install test that walks every `python -m tools.X` reference emitted by
harness commands/skills and CI workflows, then asserts the concrete implementation file the
reference resolves to actually lands in a freshly-applied target tree (D-08).

RED-first (D-08): authored and run against the pre-fix catalog BEFORE `_CATEGORY_GLOBS` gains
its `tools/**` row -- see this plan's SUMMARY.md for the recorded RED output. Only Task 2 adds
the glob row that turns this GREEN.

NOTE: an earlier draft of this test asserted only `(tmp_path / "tools" / package_name).is_dir()`
and PASSED even against the pre-fix catalog -- vacuously, because every `tools/<pkg>/pyproject.toml`
already ships via the pre-existing `"**/pyproject.toml"` glob row, which creates the package
directory without shipping any of its `.py` source. That is exactly the defect PROD-01 names, so a
directory-existence check proves nothing. This version instead resolves each `python -m tools.X`
reference to the concrete `.py` file it invokes (`__main__.py`/`__init__.py` for a bare package,
`<submodule>.py` for a dotted submodule) and asserts that specific file exists post-apply.
"""

from __future__ import annotations

import re
from pathlib import Path

from tools.adoption_apply.apply import apply_manifest
from tools.adoption_apply.cli import _harness_payload
from tools.adoption_scan import destinations

# Matches `python -m tools.<dotted.module.path>`; captures the dotted path after `tools.`.
_MODULE_REF_RE = re.compile(r"python -m tools\.([a-zA-Z0-9_.]+)")


def _discover_module_refs(repo_root: Path) -> set[str]:
    """Regex-walk harness commands/skills and CI workflows for every `python -m tools.X`
    reference, returning the raw dotted paths after `tools.`
    (e.g. `{"adoption_apply", "contract_drift.drift", ...}`)."""
    search_globs = [
        "harness/commands/**/*.md",
        "harness/skills/**/*.md",
        ".github/workflows/*.yml",
    ]
    refs: set[str] = set()
    for pattern in search_globs:
        for path in sorted(repo_root.glob(pattern)):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for match in _MODULE_REF_RE.finditer(text):
                refs.add(match.group(1))
    return refs


def _resolve_module_file(repo_root: Path, dotted: str) -> Path:
    """Resolve a dotted `tools.<dotted>` reference to the concrete `.py` file `python -m` would
    execute, per this checkout's real layout: a bare package name resolves to its
    `__main__.py` (falling back to `__init__.py`), a dotted submodule resolves to
    `<submodule>.py`."""
    as_path = Path(*dotted.split("."))
    candidate = repo_root / "tools" / as_path.with_suffix(".py")
    if candidate.is_file():
        return candidate
    main_candidate = repo_root / "tools" / as_path / "__main__.py"
    if main_candidate.is_file():
        return main_candidate
    init_candidate = repo_root / "tools" / as_path / "__init__.py"
    if init_candidate.is_file():
        return init_candidate
    raise AssertionError(
        f"tools.{dotted} does not resolve to any real .py file in this checkout "
        f"(tried {candidate}, {main_candidate}, {init_candidate})"
    )


def test_discovers_at_least_twenty_modules(repo_root: Path) -> None:
    """Sanity guard: the regex-walk helper must find a substantial number of distinct
    `python -m tools.X` references -- guards against the helper silently matching nothing and
    the main test vacuously passing."""
    refs = _discover_module_refs(repo_root)
    top_level_packages = {ref.split(".")[0] for ref in refs}
    assert len(top_level_packages) >= 20, (
        f"expected at least 20 distinct top-level tools packages, found "
        f"{len(top_level_packages)}: {sorted(top_level_packages)}"
    )


def test_every_referenced_tools_module_lands_in_applied_target(
    repo_root: Path, tmp_path: Path
) -> None:
    """Every `tools.X` module referenced by an emitted command/skill or CI workflow must have
    its concrete implementation `.py` file present at the corresponding path in a target tree
    produced by a real apply_manifest() run over the live catalog -- not merely have its parent
    directory exist."""
    refs = _discover_module_refs(repo_root)
    assert refs  # non-vacuous, backstopped by test_discovers_at_least_twenty_modules above

    # Resolve every reference against THIS checkout first (fails loudly if a reference is stale).
    source_files = {ref: _resolve_module_file(repo_root, ref) for ref in refs}

    inventory = {"target_ref": "unknown", "included": [], "excluded": []}
    proposed_hashes = destinations.harness_proposed_hashes()
    manifest = destinations.build_manifest(inventory, tmp_path, proposed_hashes)

    create_destinations = {
        entry["destination"]
        for entry in manifest["dispositions"]
        if entry["disposition"] == "create"
    }
    payloads = {destination: _harness_payload(destination) for destination in create_destinations}

    apply_manifest(manifest, tmp_path, payloads=payloads)

    for ref in sorted(refs):
        relative = source_files[ref].relative_to(repo_root)
        applied_file = tmp_path / relative
        assert applied_file.is_file(), (
            f"tools.{ref} (implemented at {relative}) was referenced by an emitted "
            f"command/skill/CI workflow but is missing from the applied target tree at "
            f"{applied_file}"
        )
