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

from ruamel.yaml import YAML

from tools.adoption_apply.apply import apply_manifest
from tools.adoption_apply.cli import _harness_payload
from tools.adoption_scan import destinations

# Matches `python -m tools.<dotted.module.path>`; captures the dotted path after `tools.`.
_MODULE_REF_RE = re.compile(r"python -m tools\.([a-zA-Z0-9_.]+)")

# Shell characters that make a token something other than a literal filesystem path (expansion,
# globbing, quoting). A token carrying any of these is not resolved -- the heuristic stays
# deliberately conservative and skips rather than guesses.
_SHELL_METACHARS = frozenset("$`\"'*?[]{}()!\\~=")
# Tokens that terminate the current `pytest` invocation: everything after them belongs to a
# different command in the same `run:` line.
_COMMAND_SEPARATORS = frozenset("&|;<>")
# Flags whose following token is a value, not a path (selection expressions, plugin names,
# ini overrides, counts).
_VALUE_TAKING_FLAGS = frozenset({"-k", "-m", "-p", "-n", "-o", "--tb", "--maxfail", "--color"})


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


def _discover_ci_pytest_path_args(repo_root: Path) -> list[tuple[str, str, str]]:
    """Walk every `.github/workflows/*.yml` `jobs.*.steps[*].run` block and extract the bare
    filesystem path arguments handed to a `pytest` invocation.

    Returns `(workflow_filename, job_name, token)` triples so a failure can name exactly where an
    unresolvable path lives.

    The heuristic is deliberately conservative: a token counts as a path argument only when it is
    not a flag, is not the value of a value-taking flag, carries no shell metacharacter, and
    either contains a `/` or names an existing top-level entry in the checkout. Scanning of an
    invocation stops at the first shell command separator, so tokens belonging to a following
    command are never mistaken for pytest arguments. Anything the heuristic is unsure about is
    skipped rather than guessed at -- which is why
    `test_ci_pytest_path_arguments_are_discovered_non_vacuously` backstops it: a matcher that
    silently stops finding anything must not pass.
    """
    yaml = YAML(typ="safe")
    found: list[tuple[str, str, str]] = []
    workflows_dir = repo_root / ".github" / "workflows"
    for workflow in sorted(workflows_dir.glob("*.yml")):
        document = yaml.load(workflow.read_text(encoding="utf-8")) or {}
        jobs = document.get("jobs") or {}
        for job_name, job in jobs.items():
            for step in job.get("steps") or []:
                run = step.get("run")
                if not isinstance(run, str):
                    continue
                for line in run.splitlines():
                    tokens = line.split()
                    if "pytest" not in tokens:
                        continue
                    previous = ""
                    for token in tokens[tokens.index("pytest") + 1 :]:
                        if any(char in _COMMAND_SEPARATORS for char in token):
                            break
                        if token.startswith("-"):
                            previous = token
                            continue
                        if previous in _VALUE_TAKING_FLAGS:
                            previous = token
                            continue
                        previous = token
                        if any(char in _SHELL_METACHARS for char in token):
                            continue
                        candidate = token.split("::", 1)[0]
                        if not candidate:
                            continue
                        if "/" not in candidate and not (repo_root / candidate).exists():
                            continue
                        found.append((workflow.name, str(job_name), candidate))
    return found


def test_ci_pytest_path_arguments_are_discovered_non_vacuously(repo_root: Path) -> None:
    """Vacuity guard for `_discover_ci_pytest_path_args`. The resolution assertion below can only
    catch a broken CI path if the extractor is still finding CI paths at all -- a regex/parser that
    silently matches nothing would make it pass while proving nothing (the same defect class the
    module docstring records for the pre-fix directory-existence check)."""
    discovered = _discover_ci_pytest_path_args(repo_root)
    assert discovered, (
        "no pytest path arguments were extracted from any .github/workflows/*.yml `run:` step -- "
        "the extractor has gone vacuous (workflow restructured, or the pytest invocations moved). "
        "Fix the extractor; do not delete this guard."
    )


def test_every_ci_pytest_path_argument_resolves(repo_root: Path) -> None:
    """Every bare filesystem path argument a CI workflow hands to `pytest` must name a path that
    exists in this checkout.

    Nothing else in the repo proves this. `python -m tools.X` module references are covered by
    `test_every_referenced_tools_module_lands_in_applied_target`, but a bare path argument is
    unchecked -- so a workflow repointed at a directory that has moved (or never existed) lands
    green locally and fails only in CI, after merge. That is a repudiation surface: a job that
    cannot collect any tests is not a gate, and it is claimed as one."""
    discovered = _discover_ci_pytest_path_args(repo_root)
    assert discovered  # non-vacuous, backstopped by the guard above

    missing = [
        (workflow, job, token)
        for workflow, job, token in discovered
        if not (repo_root / token).exists()
    ]
    assert missing == [], (
        "CI hands pytest a path argument that does not exist in this checkout: "
        + "; ".join(f"{workflow} job '{job}' -> {token!r}" for workflow, job, token in missing)
        + f" (checked {len(discovered)} path argument(s))"
    )


def test_catalog_excludes_tools_tests_and_fixtures(repo_root: Path) -> None:
    """MINIMALITY (26-REVIEW.md Fix 1): the destination catalog must ship no dev-only test asset
    under `tools/**` -- no `tests` path segment at all, and specifically none of the fixture
    mini-repos or `__snapshots__` files that embed deliberately secret-shaped literals for the
    secret scanner's own red-check inputs. `test_every_referenced_tools_module_lands_in_applied_
    target` above proves SUFFICIENCY (every real reference resolves); this proves MINIMALITY
    (nothing beyond that leaks in)."""
    catalog = destinations.destination_catalog()
    leaked = [
        row["destination"]
        for row in catalog
        if row["destination"].startswith("tools/") and "tests" in row["destination"].split("/")
    ]
    assert leaked == [], (
        f"destination catalog ships {len(leaked)} dev-only test asset(s) under tools/**: "
        f"{leaked[:10]}{'...' if len(leaked) > 10 else ''}"
    )
    assert not any("fixtures/polyglot-single" in d for d in [r["destination"] for r in catalog])
    assert not any("__snapshots__" in d for d in [r["destination"] for r in catalog])


def test_discovers_at_least_eleven_modules(repo_root: Path) -> None:
    """Sanity guard: the regex-walk helper must find a substantial number of distinct
    `python -m tools.X` references -- guards against the helper silently matching nothing and
    the main test vacuously passing.

    Floor lowered 20 -> 12 in Phase 43 (CER-07): the lifecycle-plane removal deleted 8 of the 21
    top-level packages this helper discovered, taking the live count to 13. Floor lowered 12 -> 11
    in Phase 44 (CER-09): the golden runner was relocated out of the core tree into the instance
    overlay, taking the discovered count to 11. This is a vacuity guard, not a census -- do not
    raise it back toward the live value."""
    refs = _discover_module_refs(repo_root)
    top_level_packages = {ref.split(".")[0] for ref in refs}
    assert len(top_level_packages) >= 11, (
        f"expected at least 11 distinct top-level tools packages, found "
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
    assert refs  # non-vacuous, backstopped by test_discovers_at_least_eleven_modules above

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
