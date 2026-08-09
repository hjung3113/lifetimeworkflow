"""The shared deterministic SessionStart injection assembler.

Priority order: agreements directive, data-provenance banner, live drift,
contracts index, repo map, then a progress-log pointer. Agreements at priority 0
retire the banner-first invariant: directive-first, banner-second; when active
agreements are absent the directive is omitted and the banner leads again.
"""

from __future__ import annotations

import sys
from pathlib import Path

from tools.contract_drift.drift import run_gate
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
ACTIVE_HEADER = "## Progress log (pointer)"
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


def _fit_lines(text: str, limit: int) -> str:
    """Return the longest whole-line prefix of ``text`` that fits ``limit`` chars.

    Returns "" when not even the header line fits, so the caller drops the section rather than
    emitting a bare heading.
    """
    kept: list[str] = []
    used = 0
    for line in text.splitlines():
        addition = len(line) + (1 if kept else 0)
        if used + addition > limit:
            break
        kept.append(line)
        used += addition
    return "\n".join(kept) if len(kept) > 1 else ""


def assemble(
    budget_chars: int = 4000,
    derived_dir: Path = DERIVED_DIR,
    state_dir: Path = STATE_DIR,
    agreements_dir: Path = AGREEMENTS_DIR,
) -> str:
    """Assemble a capped payload; agreements, banner, and drift are never dropped.

    No clock is computed, so delete-and-regenerate remains byte-identical.
    """
    sections = [
        ("agreements", _agreements_block(agreements_dir)),
        ("banner", BANNER),
        ("drift", _drift_summary()),
        ("contracts", _contracts_summary(derived_dir)),
        # "active" is a fixed-size POINTER, so it is ordered AHEAD of the elastic repo map. When it
        # sat last, a repo map that grew into the budget silently dropped it — adding one public
        # symbol anywhere in the tree was enough to do that. The repo map is the derived,
        # regenerable section, so it is the one that gets squeezed out. The budget still binds
        # every section here, including this one.
        ("active", _active_context_pointer(state_dir)),
        ("repomap", _repo_map_topN(derived_dir)),
    ]
    out: list[str] = []
    used = 0
    for name, text in sections:
        if not text:
            continue
        addition = len(text) + (1 if out else 0)
        if name not in ("agreements", "banner", "drift") and used + addition > budget_chars:
            # The repo map is the one ELASTIC section: it is a ranked list, so a short one is
            # still useful. Trim it to the remaining budget on a line boundary instead of
            # dropping it whole — an all-or-nothing skip here cost the payload its entire map.
            if name != "repomap":
                continue
            text = _fit_lines(text, budget_chars - used - (1 if out else 0))
            if not text:
                continue
            addition = len(text) + (1 if out else 0)
        out.append(text)
        used += addition
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841
    sys.stdout.write(assemble() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
