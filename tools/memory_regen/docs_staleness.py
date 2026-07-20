"""docs-staleness queue generator — REUSE the DOCSUP-03 guard → derived review queue (DOCSUP-04).

Three placement facts, in the order a future editor will need them:

**(a) Why this module lives under ``tools/memory_regen/`` and not ``tools/docs_guard/``.**
``tools/harness_lint/tests/test_derived_freshness.py:32`` pins
``_ALLOWED_TOOL_MODULES = frozenset({"memory_regen", "docs_sync"})`` for the ``/refresh-memory`` +
curator surface (D-06): those two markdown files may not name any other ``tools.<module>``
derivation path. That gate scans the markdown's TEXT, so IMPORTING ``tools.docs_guard`` here is
fine, while NAMING it in ``refresh-memory.md`` is not. Putting the generator under ``memory_regen``
is what lets the invocation be spelled legally (D-10).

**(b) The output is GITIGNORED and must stay out of the ``stale-derived`` job.**
``.gitignore:23`` (``.memory/derived/*``) already covers ``.memory/derived/docs-staleness.md`` —
ZERO ``.gitignore`` change. It must NOT be added to the ``stale-derived`` CI job's path list: the
queue's content is a function of the very files being edited, so committing it would red every
ordinary source commit (D-10).

**(c) Determinism is therefore proven by generate-twice SHA-256 plus a committed syrupy snapshot,
never by ``git diff``** — the target is gitignored, so ``git diff`` can say nothing about it
(``contracts_index.py:13-14``, Pitfall 2).

Like ``contracts_index.py``, this generator is ~all reuse: it imports
:func:`tools.docs_guard.guard.classify` and :func:`tools.docs_guard.impact.impact_ids` and NEVER
re-implements classification, hashing, or graph traversal — a second implementation could silently
disagree with the gate. The only new logic is row selection, deterministic rendering, and the write.

Rows are POINTER-ONLY: a binding id, a target path, a state, a severity, the dispositions that
would close it, and graph impact ids. Never a document excerpt, never a diff body (T-28-37).

No wall-clock, no calendar, no floating-point, and no ``set`` iteration reaching output.

Entrypoint: ``python -m tools.memory_regen.docs_staleness``.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

from tools.docs_guard.guard import DEFAULT_LEDGER_PATH, REPO_ROOT, classify
from tools.docs_guard.impact import impact_ids
from tools.docs_guard.registry import DEFAULT_REGISTRY_PATH

# --- paths (derived plane is gitignored + regenerated every session, D-03/D-10) ----------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
QUEUE_PATH = DERIVED_DIR / "docs-staleness.md"

# --- stable text (part of the derived-plane contract) -----------------------------------------
DERIVED_HEADER = "DERIVED — do not hand-edit (tools/memory_regen/docs_staleness.py)"

# Rendered when nothing qualifies, so an empty queue is still a stable NON-EMPTY file and `main()`
# stays idempotent. The injector's zero-item path keys off the ROW COUNT, not file emptiness.
EMPTY_MARKER = "(none — every binding is fresh or suppressed)"

# The states that constitute an obligation. ``FRESH`` and ``SUPPRESSED`` are deliberately absent:
# a queue of things needing nothing is not a queue, and ``SUPPRESSED`` means contract-drift is the
# leading gate for that binding (D-13) — surfacing it here would be a double report.
QUEUE_STATES: tuple[str, ...] = ("BROKEN", "STALE_REQUIRED", "STALE_ADVISORY")

# An open ADR obligation qualifies on its DISPOSITION rather than its state: it can never make a
# binding green (guard.py step 3), so it is always already in one of QUEUE_STATES — the explicit
# test keeps that coupling from being an accident.
OPEN_ADR_DISPOSITION = "SUPERSEDING_ADR_REQUIRED"

_NO_IMPACT = "(none)"


def rows(
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    root: str | Path = REPO_ROOT,
    cfg: dict | None = None,
    drift_gate: Callable[[], dict] | None = None,
) -> list[tuple[str, str, str, str, str, str]]:
    """Assemble one sorted row per qualifying binding by REUSING ``classify()`` + ``impact_ids()``.

    Each row is ``(binding_id, target, state, severity, dispositions, impact)`` — the DOCSUP-05
    grouping, pointer-only. ``classify`` already returns its bindings sorted by id, so the row
    order is deterministic without a second sort; the explicit ``sorted`` below makes that
    independent of the guard's internals rather than dependent on them.

    Every path argument is EXPLICIT (D-14, the ``load_project(path=...)`` seam) so the tests are
    hermetic and an instance-local overlay stays possible. ``cfg`` and ``drift_gate`` are the same
    injection seams ``impact_ids`` and ``classify`` already expose.
    """
    result = classify(
        registry_path=registry_path,
        ledger_path=ledger_path,
        root=root,
        drift_gate=drift_gate,
    )
    out: list[tuple[str, str, str, str, str, str]] = []
    for entry in result["bindings"]:
        if entry["state"] not in QUEUE_STATES and entry["disposition"] != OPEN_ADR_DISPOSITION:
            continue
        ids = impact_ids(entry["sources"], cfg)
        out.append(
            (
                entry["id"],
                entry["target"],
                entry["state"],
                entry["severity"],
                "/".join(entry["dispositions"]),
                ", ".join(ids) if ids else _NO_IMPACT,
            )
        )
    return sorted(out)


def render(queue_rows: list[tuple[str, str, str, str, str, str]]) -> str:
    """Render rows into the deterministic DERIVED-marked markdown queue.

    Output = the ``DERIVED — do not hand-edit`` header, then a stable markdown table (one row per
    qualifying binding, sorted by id) or :data:`EMPTY_MARKER`. Contains NO timestamp and NO raw
    float, so generating twice is byte-identical. Trailing newline for POSIX-clean text.
    """
    lines = [
        f"# {DERIVED_HEADER}",
        "",
        "Generated from docs/doc-dependencies.toml by "
        "`python -m tools.memory_regen.docs_staleness` (reuses tools.docs_guard). "
        f"{len(queue_rows)} binding(s) need review.",
        "",
    ]
    if not queue_rows:
        lines.append(EMPTY_MARKER)
        return "\n".join(lines) + "\n"
    lines.append("| binding | target | state | severity | required disposition | impact |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for binding_id, target, state, severity, dispositions, impact in queue_rows:
        lines.append(
            f"| {binding_id} | {target} | {state} | {severity} | {dispositions} | {impact} |"
        )
    return "\n".join(lines) + "\n"


def write_rows(
    queue_path: str | Path, queue_rows: list[tuple[str, str, str, str, str, str]]
) -> Path:
    """Render ``queue_rows`` to ``queue_path`` (mkdir parents), returning the path.

    Split out of :func:`write` so a caller that ALREADY holds the rows can publish them without
    re-classifying. Classification is expensive (a ``git ls-files`` subprocess, a full corpus walk
    and a whole contract-manifest rebuild) but, more importantly, it is a function of the tree at
    the moment it runs: a second run can legitimately return a DIFFERENT answer, so anything
    reported about the written file must be derived from the rows that were actually written.
    """
    out = Path(queue_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(queue_rows), encoding="utf-8")
    return out


def write(
    queue_path: str | Path | None = None,
    *,
    registry_path: str | Path = DEFAULT_REGISTRY_PATH,
    ledger_path: str | Path = DEFAULT_LEDGER_PATH,
    root: str | Path = REPO_ROOT,
    cfg: dict | None = None,
    drift_gate: Callable[[], dict] | None = None,
) -> Path:
    """Regenerate the derived queue and write it (mkdir parents), returning the path.

    ``queue_path=None`` resolves to :data:`QUEUE_PATH` at CALL time rather than binding it at
    definition time, so the module constant stays the single source of the destination.
    """
    return write_rows(
        QUEUE_PATH if queue_path is None else queue_path,
        rows(
            registry_path=registry_path,
            ledger_path=ledger_path,
            root=root,
            cfg=cfg,
            drift_gate=drift_gate,
        ),
    )


def main(argv: list[str] | None = None) -> int:
    """CLI: regenerate ``.memory/derived/docs-staleness.md`` (`python -m ...docs_staleness`).

    Classifies EXACTLY ONCE and reports from the rows it wrote (WR-04). Computing the count a
    second time would both double the cost and let the operator's number disagree with the file's.
    """
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    queue_rows = rows()
    out = write_rows(QUEUE_PATH, queue_rows)
    try:
        label: Path | str = out.relative_to(_REPO_ROOT)
    except ValueError:
        label = out
    print(f"wrote {label} ({len(queue_rows)} binding(s) needing review)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
