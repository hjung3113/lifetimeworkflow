"""Refusal-first agreement writer; CLI refusals print to stdout and exit 3."""

from __future__ import annotations

import re
from io import StringIO
from pathlib import Path

from ruamel.yaml import YAML

from tools.harness_lint.agreements import iter_agreement_files, load_agreement

AGREEMENTS_DIR = Path(__file__).resolve().parents[2] / ".memory" / "agreements"
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class AgreementRefused(Exception):
    """Agreement write refused because its explicit required signal is absent or unsafe."""


def _dump_frontmatter(frontmatter: dict) -> str:
    yaml = YAML(typ="safe")
    yaml.default_flow_style = False
    yaml.default_style = '"'
    stream = StringIO()
    yaml.dump(frontmatter, stream)
    dumped = stream.getvalue()
    if dumped.startswith("---\n"):
        dumped = dumped.removeprefix("---\n")
    return dumped.removesuffix("...\n")


def _target_for(slug: str, agreements_dir: Path) -> Path:
    if not _SLUG.fullmatch(slug) or slug.startswith("_"):
        raise AgreementRefused(
            "REFUSED: slug must be a lowercase hyphenated name without path syntax."
        )
    base = Path(agreements_dir)
    target = base / f"{slug}.md"
    try:
        target.resolve().relative_to(base.resolve())
    except (OSError, ValueError) as exc:
        raise AgreementRefused("REFUSED: slug must stay within the agreements directory.") from exc
    return target


def add(
    slug: str,
    title: str,
    rule: str,
    *,
    because: str | None = None,
    added: str,
    related: str | None = None,
    agreements_dir: Path = AGREEMENTS_DIR,
) -> Path:
    """Write one agreement only when explicit verbatim user feedback is supplied."""
    if not (because or "").strip():
        raise AgreementRefused(
            "REFUSED: an agreement is written only in response to explicit user feedback. "
            'Supply it verbatim with --because "<what the user said>"; '
            "it becomes the provenance stamp."
        )
    target = _target_for(slug, agreements_dir)
    if target.exists():
        raise AgreementRefused(
            f"REFUSED: agreement {target.name} already exists; it is never overwritten."
        )
    frontmatter = {
        "status": "active",
        "added": added,
        "provenance": f"added because {because}",
    }
    body = f"\n# {title}\n\n{rule}\n\nRelated: {related or ''}\n"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        f"---\n{_dump_frontmatter(frontmatter)}---{body}", encoding="utf-8", newline="\n"
    )
    return target


def retire(slug: str, *, agreements_dir: Path = AGREEMENTS_DIR) -> Path:
    """Retire an existing agreement in place while preserving its body byte-for-byte."""
    target = _target_for(slug, agreements_dir)
    matches = {path.name: path for path in iter_agreement_files(agreements_dir)}
    path = matches.get(target.name)
    if path is None:
        raise AgreementRefused(f"REFUSED: no agreement named {target.name} exists to retire.")
    agreement = load_agreement(path)
    if agreement is None:
        raise AgreementRefused(f"REFUSED: agreement {target.name} cannot be parsed for retirement.")
    frontmatter, body = agreement
    if frontmatter.get("status") == "retired":
        return path
    frontmatter["status"] = "retired"
    path.write_text(
        f"---\n{_dump_frontmatter(frontmatter)}---\n{body}", encoding="utf-8", newline="\n"
    )
    return path


def main(argv: list[str] | None = None) -> int:
    """CLI: refusal follows approve.py's stdout-and-exit-3 convention."""
    import argparse
    from datetime import date

    parser = argparse.ArgumentParser(description="Write or retire a working agreement")
    parser.add_argument("slug")
    parser.add_argument("--because", default=None)
    parser.add_argument("--title", default=None)
    parser.add_argument("--rule", default=None)
    parser.add_argument("--related", default=None)
    parser.add_argument("--added", default=None)
    parser.add_argument("--retire", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.retire:
            path = retire(args.slug)
        else:
            if not args.title or not args.rule:
                raise AgreementRefused(
                    "REFUSED: adding an agreement requires both --title and --rule."
                )
            path = add(
                args.slug,
                args.title,
                args.rule,
                because=args.because,
                added=args.added or date.today().isoformat(),
                related=args.related,
            )
    except AgreementRefused as exc:
        print(str(exc))
        return 3
    print(f"AGREED: {path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
