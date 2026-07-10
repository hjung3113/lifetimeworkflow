"""POLY-01 polyglot-boundary linter (D-03) — the shared §4.3-4.6 rule engine.

Turns the ``integration_contracts §4.3-4.6`` checklist into a **fail-loud detector**. It does
NOT re-implement normalization: every value-level check compares a cell against the shared
``libs/python`` ``normalize.core`` output and flags the diff (detection-by-normalization,
RESEARCH Pattern 5). This is the single §4.3-4.6 rule engine HOOK-04 (on-write) and HOOK-03
(commit-gate) both call — one implementation, three call sites.

Rules (codes mirror libs/normalize-spec.md R1-R8):
  * R1-BOM   — a leading UTF-8 BOM (``EF BB BF``); §4.3 forbids BOM.
  * R2-CRLF  — any CR byte; §4.3 requires LF-only newlines.
  * R7-tsv   — inconsistent tab counts across rows (column shift); §4.3 TSV escape invariant.
  * R3-decimal / R5-datetime — a cell whose ``normalize_cell`` canonical form differs from the
    cell itself (non-canonical decimal locale / non-UTC-or-non-ISO datetime); §4.6 / §4.4.
  * R6-null  — the internal comparison sentinel ``<NULL>`` leaked into wire TSV data; the wire
    null form is the agreed null token (``\\N``), distinct from empty string (§4.3, "" != null).

The BOM/decimal/timezone/null logic lives ONCE in ``normalize.core`` (D-02/D-03 built-once) —
re-implementing any of it here is the RESEARCH anti-pattern. ``test_corpus_parity.py`` proves
this module's canonical target has zero drift from the shared core on the fixture corpus.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

# --- reuse the shared §4-5 core (libs/python is a virtual uv member, not installed) -----------
# Identical sys.path shim golden_runner.runner uses: lint.py -> polyglot_lint -> tools -> repo root.
REPO_ROOT = Path(__file__).resolve().parents[2]
_LIBS_PYTHON = REPO_ROOT / "libs" / "python"
if str(_LIBS_PYTHON) not in sys.path:
    sys.path.insert(0, str(_LIBS_PYTHON))

from normalize.core import (  # noqa: E402  (import after the sys.path shim, by design)
    DEFAULT_NULL_TOKEN,
    NULL_SENTINEL,
    normalize_cell,
    normalize_tsv,
)

# kinds whose non-canonicality is detected by diffing the cell against normalize_cell.
_CELL_RULE = {"decimal": "R3-decimal", "datetime": "R5-datetime"}


@dataclass(frozen=True)
class Violation:
    """One §4.3-4.6 boundary breach: a stable rule ``code`` + a human-readable ``detail``."""

    rule: str
    detail: str


def lint_bytes(raw: bytes) -> list[Violation]:
    """Byte-level checks on a raw TSV blob: R1 (BOM) + R2 (CR/CRLF). Clean bytes → ``[]``."""
    violations: list[Violation] = []
    if raw.startswith(b"\xef\xbb\xbf"):
        violations.append(Violation("R1-BOM", "UTF-8 BOM present; §4.3 forbids a BOM."))
    if b"\r" in raw:
        violations.append(Violation("R2-CRLF", "CR byte present; §4.3 requires LF-only newlines."))
    return violations


def lint_tsv(text: str, kinds: list[str] | None = None) -> list[Violation]:
    """Text-level checks on decoded TSV: R7 (column-shift), R6 (leaked null sentinel), and —
    when per-column ``kinds`` are supplied — R3/R5 decimal/datetime non-canonicality.

    A cell is non-canonical iff ``normalize_cell(cell, kind) != cell`` AND it is not the agreed
    wire null token (``\\N``), which is a legitimate value in any typed column (R6).
    """
    violations: list[Violation] = []
    rows = [r for r in text.split("\n") if r != ""]

    widths = {r.count("\t") for r in rows}
    if len(widths) > 1:
        violations.append(
            Violation("R7-tsv", f"inconsistent column count across rows: tab-counts {sorted(widths)}")
        )

    for row in rows:
        cells = row.split("\t")
        for index, cell in enumerate(cells):
            if cell == NULL_SENTINEL:
                violations.append(
                    Violation(
                        "R6-null",
                        f"internal null sentinel {NULL_SENTINEL!r} leaked into wire TSV; the wire "
                        f"null must be the null token {DEFAULT_NULL_TOKEN!r} (§4.3, '' != null).",
                    )
                )
            if not kinds or index >= len(kinds):
                continue
            kind = kinds[index]
            rule = _CELL_RULE.get(kind)
            if rule is None:
                continue
            canonical = normalize_cell(cell, kind, DEFAULT_NULL_TOKEN)
            if canonical != cell and cell != DEFAULT_NULL_TOKEN:
                violations.append(
                    Violation(rule, f"non-canonical {kind}: {cell!r} (canonical: {canonical!r})")
                )
    return violations


def lint_file(path: str | Path, kinds: list[str] | None = None) -> list[Violation]:
    """Lint a TSV file: byte checks on the raw bytes + text checks on the normalized text.

    ``normalize_tsv`` strips BOM/CRLF and LF-splits so the text-level checks see clean rows —
    the byte-level R1/R2 checks run on the untouched raw bytes so those breaches still surface.
    """
    raw = Path(path).read_bytes()
    violations = lint_bytes(raw)
    violations += lint_tsv(normalize_tsv(raw), kinds)
    return violations


def main(argv: list[str] | None = None) -> int:
    """CLI: ``python -m tools.polyglot_lint.lint <path> [--kinds ...]``. Exit 0 clean / 1 dirty.

    Fail loud: every violation's rule code + detail is written to **stderr**; a clean file
    prints an OK line to stdout. Exit 1 on ANY violation so on-write / commit-gate hooks block.
    """
    import argparse

    parser = argparse.ArgumentParser(description="POLY-01 polyglot §4.3-4.6 boundary linter")
    parser.add_argument("path", help="TSV file to lint")
    parser.add_argument(
        "--kinds",
        nargs="*",
        default=None,
        help="per-column kinds (decimal|datetime|string) enabling R3/R5 cell checks",
    )
    args = parser.parse_args(argv)

    violations = lint_file(args.path, args.kinds)
    if not violations:
        print(f"polyglot-lint: OK — {args.path}")
        return 0
    for v in violations:
        print(f"polyglot-lint: FAIL [{v.rule}] {v.detail}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
