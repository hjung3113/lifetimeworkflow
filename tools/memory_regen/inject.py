"""The shared deterministic SessionStart injection assembler.

Priority order: agreements directive, data-provenance banner, live drift,
contracts index, repo map, then a progress-log pointer. Agreements at priority 0
retire the banner-first invariant: directive-first, banner-second; when active
agreements are absent the directive is omitted and the banner leads again.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.contract_drift.drift import run_gate
from tools.handoff.handoff import (
    HandoffError,
    packet_root_from_handoff,
)
from tools.handoff.handoff import (
    validate as validate_handoff,
)
from tools.harness_lint import parse_frontmatter
from tools.harness_lint.agreements import iter_agreement_files, load_agreement

_REPO_ROOT = Path(__file__).resolve().parents[2]
DERIVED_DIR = _REPO_ROOT / ".memory" / "derived"
STATE_DIR = _REPO_ROOT / ".memory" / "state"
AGREEMENTS_DIR = _REPO_ROOT / ".memory" / "agreements"
_HEAD_LINES = 20
_AGREEMENTS_MAX_ENTRIES = 6
_AGREEMENTS_MAX_CHARS = 700

BANNER = (
    "DATA PROVENANCE — these summaries resolve a DATA conflict: contracts/ and docs/adr/ "
    "(ADR) determine which artifact wins a contradiction. This precedence is not a reason to "
    "distrust, retract, or re-verify grounded working context."
)
DRIFT_HEADER = "## Contract drift (live)"
CONTRACTS_HEADER = "## Contracts index (summary)"
REPO_MAP_HEADER = "## Repo map (top-N)"
DOCS_HEADER = "## Human docs needing review (pointer)"
ACTIVE_HEADER = "## Progress log (pointer)"
TASK_HEADER = "## Active task (validated HANDOFF pointer)"
AGREEMENTS_HEADER = (
    "## Working agreements\n"
    "Working-style directives never override contracts/, docs/adr/, or the gates."
)
AGREEMENTS_POINTER = AGREEMENTS_HEADER + "\nRead .memory/agreements/ before acting."


def _drift_summary() -> str:
    try:
        gate = run_gate()
    except Exception:  # pragma: no cover
        return f"{DRIFT_HEADER}\ncontract-drift: unknown (gate unavailable)"
    if gate["ok"]:
        return f"{DRIFT_HEADER}\ncontract-drift: clean (live manifest matches baseline)"
    lines = [f"- {rel} [{kind}/{cls}]" for rel, kind, cls in gate["drifted"]]
    return f"{DRIFT_HEADER}\ncontract-drift: DRIFT — {len(lines)} schema(s):\n" + "\n".join(lines)


def _read_head(path: Path) -> str:
    try:
        return "\n".join(path.read_text(encoding="utf-8").splitlines()[:_HEAD_LINES])
    except OSError:
        return ""


def _contracts_summary(derived_dir: Path = DERIVED_DIR) -> str:
    head = _read_head(Path(derived_dir) / "contracts-index.md")
    return (
        f"{CONTRACTS_HEADER}\n{head}"
        if head
        else (
            f"{CONTRACTS_HEADER}\n"
            "(contracts-index pending — run `python -m tools.memory_regen.contracts_index`)"
        )
    )


def _docs_staleness_pointer(derived_dir: Path = DERIVED_DIR) -> str:
    """At most TWO lines pointing at the derived docs-review queue, or "" (D-11).

    Reads the RENDERED queue and never recomputes the guard: classification needs a ``git``
    subprocess and a full doc-corpus walk, neither of which belongs on the session-start hot path,
    and a live recomputation would make the payload depend on state the tests cannot fixture.
    ``derived_dir`` is a PARAMETER for the same reason ``_contracts_summary`` takes one.

    Returns "" when the queue is absent or reports zero obligations, so ``assemble()`` skips the
    section at the ``if not text`` guard below and the payload stays byte-identical to a tree that
    has never run the generator. ``_read_head`` is deliberately NOT used — it returns
    :data:`_HEAD_LINES` lines and would make this section grow with the queue.
    """
    try:
        text = (Path(derived_dir) / "docs-staleness.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    # The generator's table is the stable seam: every line of it starts with "| ", and exactly two
    # of those lines are the column header and its separator.
    count = max(sum(1 for line in text.splitlines() if line.startswith("| ")) - 2, 0)
    if count == 0:
        return ""
    return (
        f"{DOCS_HEADER}\n{count} human doc(s) need review — see .memory/derived/docs-staleness.md"
    )


def _repo_map_topN(derived_dir: Path = DERIVED_DIR) -> str:
    head = _read_head(Path(derived_dir) / "repo-map.md")
    return f"{REPO_MAP_HEADER}\n{head}" if head else ""


def _render_agreement(body: str) -> str | None:
    lines = body.splitlines()
    title = next((line[2:].strip() for line in lines if line.startswith("# ")), "")
    rule = next(
        (
            line.strip()
            for line in lines
            if line.strip() and not line.startswith("#") and not line.startswith("Related:")
        ),
        "",
    )
    return f"- **{title}** — {rule}" if title and rule else None


def _agreements_block(agreements_dir: Path = AGREEMENTS_DIR) -> str:
    entries: list[str] = []
    for path in iter_agreement_files(agreements_dir):
        agreement = load_agreement(path)
        if agreement is None:
            continue
        frontmatter, body = agreement
        if str(frontmatter.get("status", "")).strip() != "active":
            continue
        rendered = _render_agreement(body)
        if rendered:
            entries.append(rendered)
    if not entries:
        return ""
    block = AGREEMENTS_HEADER + "\n" + "\n".join(entries)
    if len(entries) > _AGREEMENTS_MAX_ENTRIES or len(block) > _AGREEMENTS_MAX_CHARS:
        return AGREEMENTS_POINTER
    return block


def _active_context_pointer(state_dir: Path = STATE_DIR) -> str:
    stamp = ""
    try:
        frontmatter, _ = parse_frontmatter(
            (Path(state_dir) / "activeContext.md").read_text(encoding="utf-8")
        )
        stamp = str(frontmatter.get("updated", "")).strip()
    except (OSError, ValueError):
        pass
    suffix = f" [updated: {stamp}]" if stamp else " [updated: unknown — run /checkpoint]"
    return (
        f"{ACTIVE_HEADER}\n.memory/state/activeContext.md — session progress log; "
        "git holds the full "
        f"completed history. On a data conflict, contracts/ADR win.{suffix}"
    )


def _active_task_pointer(state_dir: Path = STATE_DIR) -> str:
    """Render only the bounded active pointer; never task/evidence/artifact bodies."""
    pointer_path = Path(state_dir) / "active-task.json"
    if not pointer_path.exists():
        return ""
    try:
        value = json.loads(pointer_path.read_bytes().removeprefix(b"\xef\xbb\xbf"))
        if not isinstance(value, dict) or set(value) != {
            "task_id",
            "handoff_path",
            "state_revision",
        }:
            raise ValueError
        root = Path(state_dir).resolve().parents[1]
        handoff_path = root / str(value["handoff_path"])
        packet = packet_root_from_handoff(handoff_path)
        handoff = validate_handoff(packet, handoff_path)
        if (
            handoff["task_id"] != value["task_id"]
            or handoff["state_revision"] != value["state_revision"]
        ):
            raise ValueError
        return (
            f"{TASK_HEADER}\n{handoff['task_id']} — phase {handoff['phase']}; lane {handoff['lane']}; "
            f"revision {handoff['state_revision']}; next action: {handoff['next_action']}.\n"
            f"Read and validate {value['handoff_path']}, then run /phase-gate before EXECUTE, REVIEW, or VERIFY."
        )
    except (OSError, ValueError, KeyError, HandoffError):
        # An active pointer is a safety boundary, not optional context.  Never hide a stale
        # pointer: the fresh session must stop and repair it before protected work proceeds.
        return f"{TASK_HEADER}\nACTIVE HANDOFF INVALID — resume is blocked; repair or remove the active pointer."


def assemble(
    budget_chars: int = 4000,
    derived_dir: Path = DERIVED_DIR,
    state_dir: Path = STATE_DIR,
    agreements_dir: Path = AGREEMENTS_DIR,
) -> str:
    """Assemble a capped payload; agreements, banner, and drift are never dropped.

    No clock is computed, so delete-and-regenerate remains byte-identical.
    """
    task = _active_task_pointer(state_dir)
    sections = [
        ("agreements", _agreements_block(agreements_dir)),
        ("banner", BANNER),
        ("drift", _drift_summary()),
        # D-05/TCP-15: this reserved slot is deliberately before all droppable summaries.
        ("task", task),
        ("contracts", _contracts_summary(derived_dir)),
        # D-11: droppable by design — deliberately absent from the never-drop tuple below.
        ("docs", _docs_staleness_pointer(derived_dir)),
        ("repomap", _repo_map_topN(derived_dir)),
        ("active", _active_context_pointer(state_dir)),
    ]
    out: list[str] = []
    used = 0
    for name, text in sections:
        if not text:
            continue
        addition = len(text) + (1 if out else 0)
        if name not in ("agreements", "banner", "drift", "task") and used + addition > budget_chars:
            continue
        out.append(text)
        used += addition
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841
    sys.stdout.write(assemble() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
