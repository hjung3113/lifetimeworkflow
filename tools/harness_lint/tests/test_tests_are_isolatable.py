"""Every ``tools/*/tests/`` directory must be runnable ON ITS OWN, not only inside the full suite.

This is the third appearance of one defect, so it gets a gate.

``tools`` is a namespace package and every member is a *virtual* uv-workspace member — imported by
module path from the repo root, never pip-installed. A test module that does
``from tools.<pkg> import ...`` therefore needs the repo root on ``sys.path``, and nothing puts it
there automatically. The member's own ``tests/conftest.py`` is what does it.

The failure mode is nastier than a plain missing import, because it is **invocation-dependent**:

* ``uv run pytest`` (whole repo) COLLECTS FINE. Some sibling member's conftest has already inserted
  the repo root by the time the bare member is collected, so it free-rides.
* ``uv run pytest tools/<pkg>`` (isolated) errors at collection with ``ModuleNotFoundError: No
  module named 'tools'``.

So the suite is green under the invocation developers run and red under the invocation CI runs —
and several CI jobs here DO run scoped commands (``pytest tools/golden_runner``,
``pytest tools/lifecycle_eval``, ``pytest tools/ruff_baseline``, ``pytest tools/harness_lint ...``).

History, which is why prose was not enough:

1. **v2.3** — ``tools/lifecycle_eval/tests/`` had no conftest. The CI job's step 2 was red at
   collection for an entire milestone while the full suite reported green. Repaired by ``934770e``.
2. **v2.3 closeout** — recorded as a carried red in STATE.md, still described as a one-off.
3. **v2.4 phase 36** — a module-scope ``import tools.discipline.check`` was added to the
   task_control tests, and ``uv run pytest tools/task_control`` broke. Two more members
   (``discipline``, ``evidence``) turned out to have the same hole, unnoticed because nothing had
   yet forced their isolated invocation.

The gate checks the PROPERTY, not one mechanism. What must be true is "the repo root reaches
``sys.path`` before ``tools.*`` is imported". Two idioms in this repo satisfy that and both are
accepted: a ``tests/conftest.py`` that inserts it (``lifecycle_eval``, ``harness_lint``), or each
test module inserting it itself before its imports (``contract_drift``, ``contract_hash`` — hence
their ``# noqa: E402``).

Both refinements came from being wrong first. The initial rule was "every tests dir needs a
conftest", which flagged ``contract_drift`` and ``contract_hash`` — but an isolated run of each
collects cleanly, so the rule would have forced churn to fix a defect neither had. The second rule
keyed on importing ``tools.*``, which still flagged them, because they import it *and* self-wire.
Only the property is right. Verified per member by actually running the isolated collection rather
than reasoning about it.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS = REPO_ROOT / "tools"

# Inserting the repo root is the whole job; accept either spelling of it.
_ROOT_INSERTION_MARKERS = ("sys.path.insert", "sys.path.append")


_TOOLS_IMPORT = re.compile(r"^\s*(?:from|import)\s+tools\.", re.MULTILINE)


def _unwired_modules(tests_dir: Path) -> list[str]:
    """Return test modules that import ``tools.*`` with no repo-root insertion reaching them.

    A module is satisfied when its own directory has a wiring ``conftest.py``, or when the module
    itself inserts the repo root. Anything else free-rides on a sibling member's conftest and
    breaks under an isolated invocation.
    """
    conftest = tests_dir / "conftest.py"
    if conftest.is_file() and _inserts_root(conftest.read_text(encoding="utf-8")):
        return []

    unwired: list[str] = []
    for module in sorted(tests_dir.rglob("test_*.py")):
        text = module.read_text(encoding="utf-8")
        if _TOOLS_IMPORT.search(text) and not _inserts_root(text):
            unwired.append(module.relative_to(REPO_ROOT).as_posix())
    return unwired


def _inserts_root(text: str) -> bool:
    return any(marker in text for marker in _ROOT_INSERTION_MARKERS)


def _members_needing_wiring() -> list[Path]:
    """Return every ``tools/<pkg>/tests`` dir containing modules that import ``tools.*``."""
    found: list[Path] = []
    for tests_dir in sorted(TOOLS.glob("*/tests")):
        if not tests_dir.is_dir():
            continue
        modules = list(tests_dir.rglob("test_*.py"))
        if any(_TOOLS_IMPORT.search(m.read_text(encoding="utf-8")) for m in modules):
            found.append(tests_dir)
    return found


_members_with_tests = _members_needing_wiring


def test_every_tools_test_dir_can_stand_alone() -> None:
    """Each member's tests carry their own repo-root wiring, so an isolated run collects."""
    missing: list[str] = []
    for tests_dir in _members_with_tests():
        missing.extend(_unwired_modules(tests_dir))

    assert missing == [], (
        "these test modules import `tools.*` with nothing putting the repo root on sys.path, so "
        "they collect only because a sibling member's conftest happened to run first and they "
        f"fail under an isolated `uv run pytest <that dir>`: {missing}. "
        "Fix with either idiom: add tools/<pkg>/tests/conftest.py (copy lifecycle_eval's), or "
        "insert the repo root in the module itself before its imports. "
        "The full-suite run will NOT tell you about this — that is the entire defect."
    )


def test_the_scan_finds_the_members_it_claims_to() -> None:
    """NEGATIVE CONTROL — the enumeration is live, not an empty loop passing vacuously.

    Without this, deleting the glob would leave ``test_every_tools_test_dir_can_stand_alone``
    passing over an empty list forever.
    """
    found = {p.relative_to(REPO_ROOT).as_posix() for p in _members_with_tests()}

    assert len(found) >= 10, (
        f"expected many tools/*/tests dirs, found {len(found)}: {sorted(found)}"
    )
    for expected in ("tools/harness_lint/tests", "tools/lifecycle_eval/tests"):
        assert expected in found, f"{expected} should be enumerated; scan returned {sorted(found)}"
