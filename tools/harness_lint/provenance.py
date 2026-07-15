"""Agreement provenance lint: validates shape, not truth.

A well-formed but fabricated provenance can pass; this is accident prevention,
not a sandbox. Omitted or malformed stamps fail loud, making a fabricated user
quote a visible, auditable diff. This tier is never regenerated, so it is
validated in place rather than using a regenerate-and-verify workflow.

Failures use stderr like the polyglot lint. The /agree refusal path uses stdout
because each follows its named precedent.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from tools.harness_lint.agreements import iter_agreement_files, load_agreement

AGREEMENTS_DIR = Path(__file__).resolve().parents[2] / ".memory" / "agreements"
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_PROVENANCE = re.compile(r"^added because \S")
_STATUS = frozenset({"active", "retired"})


@dataclass(frozen=True)
class Violation:
    """One agreement provenance breach: a stable rule plus human-readable detail."""

    rule: str
    detail: str


def check_agreement(frontmatter: dict) -> list[Violation]:
    """Return every structural provenance violation without raising."""
    violations: list[Violation] = []
    status = str(frontmatter.get("status", "")).strip()
    if status not in _STATUS:
        violations.append(Violation("PROV-status", "status must be active or retired"))

    added = frontmatter.get("added")
    if not isinstance(added, str):
        violations.append(
            Violation(
                "PROV-added-type",
                f"added must be a quoted string (received {type(added).__name__}); "
                'use added: "YYYY-MM-DD"',
            )
        )
    elif not _ISO_DATE.match(added):
        violations.append(
            Violation("PROV-added-format", "added must match YYYY-MM-DD"),
        )

    provenance = frontmatter.get("provenance")
    if not isinstance(provenance, str) or not _PROVENANCE.match(provenance):
        violations.append(
            Violation(
                "PROV-provenance",
                "provenance must start with added because and a non-empty tail",
            )
        )
    return violations


def lint_file(path: str | Path) -> list[Violation]:
    """Lint one agreement, reporting malformed frontmatter rather than skipping it."""
    agreement = load_agreement(Path(path))
    if agreement is None:
        return [Violation("PROV-unparseable", "frontmatter could not be read or parsed")]
    frontmatter, _ = agreement
    return check_agreement(frontmatter)


def lint_dir(agreements_dir: Path = AGREEMENTS_DIR) -> list[tuple[Path, Violation]]:
    """Lint every selected agreement file, including retired entries."""
    return [
        (path, violation)
        for path in iter_agreement_files(agreements_dir)
        for violation in lint_file(path)
    ]


def main(argv: list[str] | None = None) -> int:
    """CLI: lint an agreements directory and exit 0 clean or 1 dirty."""
    import argparse

    parser = argparse.ArgumentParser(description="Agreement provenance shape lint")
    parser.add_argument("agreements_dir", nargs="?", type=Path, default=AGREEMENTS_DIR)
    args = parser.parse_args(argv)
    violations = lint_dir(args.agreements_dir)
    if not violations:
        count = len(iter_agreement_files(args.agreements_dir))
        print(f"provenance-lint: OK — {count} agreement(s)")
        return 0
    for path, violation in violations:
        print(
            f"provenance-lint: FAIL [{violation.rule}] {path.name}: {violation.detail}",
            file=sys.stderr,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
