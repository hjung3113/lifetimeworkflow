"""Shared agreement-file selection and loading helpers.

These helpers own L1-L4 of agreement identity: deterministic discovery,
exclusion, confinement, and fail-closed parsing. The injector's active-status
render policy is deliberately excluded so lint can examine every entry.
They do not compute wall-clock values.
"""

from __future__ import annotations

from pathlib import Path

from ruamel.yaml.error import YAMLError

from tools.harness_lint.frontmatter import parse_frontmatter


def iter_agreement_files(agreements_dir: Path) -> list[Path]:
    """Return sorted, confined agreement markdown files or an empty list."""
    base = Path(agreements_dir)
    try:
        resolved_base = base.resolve()
    except OSError:
        return []

    paths: list[Path] = []
    for path in sorted(base.glob("*.md")):
        if path.name.startswith("_") or path.name == "README.md" or path.is_symlink():
            continue
        try:
            path.resolve().relative_to(resolved_base)
        except (OSError, ValueError):
            continue
        paths.append(path)
    return paths


def load_agreement(path: Path) -> tuple[dict, str] | None:
    """Load an agreement's frontmatter and body, failing closed on bad input."""
    try:
        return parse_frontmatter(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, YAMLError):
        return None
