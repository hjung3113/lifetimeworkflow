"""contracts→reference generator — scan contracts/ → derived Diátaxis reference pages (DOCS-03).

Clone of ``tools/memory_regen/contracts_index.py`` (RESEARCH §"/docs-sync Generator" / D-06):
``rows`` → ``render`` → ``write`` → ``main``, a DERIVED "do not hand-edit" header, sorted keys,
NO ``datetime.now()`` and NO raw floats, so generating twice — or delete + regenerate — is
byte-for-byte identical (success criterion 4, proven by a committed syrupy snapshot, NOT git diff).

Input:  ``contracts/**/*.schema.json`` read with the stdlib ``json`` module — the SAME read path
        as :mod:`tools.contract_hash` (T-03-23: no second hash/read impl that could disagree with
        the drift gate; T-03-SC: zero new deps).
Output: one ``docs/reference/<name>.md`` per schema (5 seed schemas → 5 pages). Every write is
        CONFINED under ``docs/reference/`` (mirrors ``tools/golden_runner/runner.py::_confine``,
        T-03-21): a schema name that would traverse outside the reference dir is refused. ONLY
        the reference quadrant is generated — tutorials/how-to/explanation stay human-authored
        (DOCS-03 anti-feature), and ``docs/reference/README.md`` is left intact.

Entrypoint: ``python -m tools.docs_sync``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# --- paths (tools/docs_sync/generate.py → parents[2] == repo root) ----------------------------
REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_DIR = REPO_ROOT / "contracts"
REFERENCE_DIR = REPO_ROOT / "docs" / "reference"

# Schemas are named ``<name>.schema.json``; the reference page is ``<name>.md``. ``Path.stem`` only
# strips the last suffix (``foo.schema``), so slice the full compound suffix explicitly.
_SCHEMA_SUFFIX = ".schema.json"

# --- stable text (part of the derived-plane contract) -----------------------------------------
# The DERIVED marker is the FIRST line of every generated page (D-06 / T-03-22). "do not hand-edit"
# is the human-visible + machine-checked signal that this quadrant is regenerated, never authored.
DERIVED_HEADER = "DERIVED — do not hand-edit — generated from contracts/ by tools.docs_sync"

# The format-conventions schema materializes the §4.3–4.6 cross-cutting canonicalization rules as
# const fields; its page carries an extra conventions block (BOM/LF/decimal/TZ/null).
_CONVENTIONS_SCHEMA = "format-conventions"


class DocsSyncError(RuntimeError):
    """A generated path escaped the docs/reference/ confinement (T-03-21)."""


# --- scalar / cell formatting (deterministic, markdown-safe) ----------------------------------


def _scalar(value: object) -> str:
    """Render a JSON scalar deterministically (bool→true/false, None→null, str verbatim, else JSON).

    ``json.dumps`` gives a stable serialization for numbers so there is no locale/repr drift; the
    seed schemas carry no raw float at the top level, but this keeps the render total either way.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True)


def _cell(text: str) -> str:
    """Escape a value for a markdown table cell — pipes escaped, newlines flattened to spaces."""
    return text.replace("|", r"\|").replace("\n", " ").strip()


def _type(prop: dict) -> str:
    """A property's declared type (or const/enum/ref/— when ``type`` is absent)."""
    declared = prop.get("type")
    if isinstance(declared, str):
        return declared
    if isinstance(declared, list):
        return "|".join(str(t) for t in declared)
    if "const" in prop:
        return "const"
    if "enum" in prop:
        return "enum"
    if "$ref" in prop:
        return "ref"
    return "—"


def _enum_const(prop: dict) -> str:
    """The fixed value(s) a property is pinned to.

    ``const`` verbatim, ``enum`` comma-joined, else ''.
    """
    if "const" in prop:
        return _scalar(prop["const"])
    if "enum" in prop:
        return ", ".join(_scalar(v) for v in prop["enum"])
    return ""


def _source(schema: dict, name: str) -> str:
    """The ``contracts/...`` provenance path, derived from ``$id`` (schema-content only, no cwd)."""
    sid = str(schema.get("$id", ""))
    idx = sid.find("contracts/")
    if idx != -1:
        return sid[idx:]
    return f"contracts/**/{name}{_SCHEMA_SUFFIX}"


# --- rows → render (deterministic; no timestamp, no raw float) ---------------------------------


def rows(schema: dict) -> list[tuple[str, str, bool, str, str]]:
    """Assemble one sorted row per top-level property — deterministic, no timestamps/floats.

    Each row is ``(name, type, required, enum_or_const, description)`` with properties sorted by
    name so the render is byte-stable (Pitfall P12). Nested object shapes (columns/entities/…) are
    intentionally summarized as their top-level type — structure-only tables are still valid (A4).
    """
    props: dict = schema.get("properties", {})
    required = set(schema.get("required", []))
    return [
        (name, _type(prop), name in required, _enum_const(prop), str(prop.get("description", "")))
        for name, prop in sorted(props.items())
    ]


def _conventions_block(schema: dict) -> list[str]:
    """The §4.3–4.6 canonicalization block for format-conventions (each const field, sorted)."""
    props: dict = schema.get("properties", {})
    lines = ["## Canonicalization conventions (§4.3–4.6)", ""]
    for name, prop in sorted(props.items()):
        if "const" in prop:
            desc = _cell(str(prop.get("description", "")))
            lines.append(f"- **{_cell(name)}** = `{_scalar(prop['const'])}` — {desc}")
    lines.append("")
    return lines


def render(name: str, schema: dict) -> str:
    """Render one schema into a deterministic DERIVED-marked reference page.

    Layout: the DERIVED marker (first line), the schema title, a "regenerated from contracts/"
    provenance note, the schema description, a stable property table
    ``(Property | Type | Required | Enum / Const | Description)``, and — for the format-conventions
    schema — the §4.3–4.6 canonicalization block. No timestamp, no raw float → rendering twice is
    byte-identical. Trailing newline for POSIX-clean text.
    """
    title = schema.get("title") or schema.get("$id") or name
    source = _source(schema, name)
    lines = [
        f"<!-- {DERIVED_HEADER} -->",
        "",
        f"# {title}",
        "",
        f"> DERIVED reference — regenerated from `{source}` by `python -m tools.docs_sync`. "
        f"Do not hand-edit; change the contract and re-run `/docs-sync`.",
        "",
    ]
    description = str(schema.get("description", "")).strip()
    if description:
        lines += [description, ""]

    table = rows(schema)
    if table:
        lines += [
            "| Property | Type | Required | Enum / Const | Description |",
            "| --- | --- | --- | --- | --- |",
        ]
        for prop_name, prop_type, required, enum_const, prop_desc in table:
            lines.append(
                f"| {_cell(prop_name)} | {_cell(prop_type)} | {'yes' if required else 'no'} "
                f"| {_cell(enum_const)} | {_cell(prop_desc)} |"
            )
        lines.append("")
    else:
        lines += ["_No top-level properties defined in this schema._", ""]

    if name == _CONVENTIONS_SCHEMA:
        lines += _conventions_block(schema)

    return "\n".join(lines).rstrip("\n") + "\n"


# --- path confinement (mirror golden_runner._confine, T-03-21) --------------------------------


def _confine(path: Path, base: Path) -> Path:
    """Resolve ``path`` and refuse it unless it stays under ``base`` (no traversal outside)."""
    resolved = path.resolve()
    base_resolved = Path(base).resolve()
    if base_resolved != resolved and base_resolved not in resolved.parents:
        raise DocsSyncError(f"generated path escapes docs/reference confinement: {resolved}")
    return resolved


# --- schema discovery + write -----------------------------------------------------------------


def _resolve(path: str | Path, default_relative_to: Path = REPO_ROOT) -> Path:
    p = Path(path)
    return p.resolve() if p.is_absolute() else (default_relative_to / p).resolve()


def iter_schemas(contracts: str | Path = CONTRACTS_DIR) -> list[tuple[str, dict]]:
    """Yield ``(name, schema)`` for every ``contracts/**/*.schema.json``, sorted by path.

    The glob is confined to the contracts subtree (defense-in-depth against a symlink pointing
    out), exactly like ``tools.contract_hash.build_manifest``. Read via stdlib ``json`` only.
    """
    root = _resolve(contracts)
    result: list[tuple[str, dict]] = []
    for p in sorted(root.glob(f"**/*{_SCHEMA_SUFFIX}")):
        resolved = p.resolve()
        if root != resolved and root not in resolved.parents:
            continue
        name = p.name[: -len(_SCHEMA_SUFFIX)]
        schema = json.loads(p.read_text(encoding="utf-8"))
        result.append((name, schema))
    return result


def write(
    contracts: str | Path = CONTRACTS_DIR,
    out: str | Path = REFERENCE_DIR,
) -> list[Path]:
    """Regenerate one ``<out>/<name>.md`` per schema; return the written paths (all confined).

    Every target is confined under ``out`` (T-03-21) BEFORE writing, so a traversal-shaped schema
    name is refused rather than escaping the reference quadrant. ``README.md`` and the other
    Diátaxis quadrants are never touched — only ``<name>.md`` pages are written.
    """
    out_dir = _resolve(out)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for name, schema in iter_schemas(contracts):
        target = _confine(out_dir / f"{name}.md", out_dir)
        target.write_text(render(name, schema), encoding="utf-8")
        written.append(target)
    return written


def main(argv: list[str] | None = None) -> int:
    """CLI: regenerate ``docs/reference/*.md`` from ``contracts/`` (`python -m tools.docs_sync`)."""
    argv = sys.argv[1:] if argv is None else argv  # noqa: F841 (reserved for future flags)
    written = write()
    for path in written:
        try:
            rel = path.relative_to(REPO_ROOT)
        except ValueError:
            rel = path
        print(f"wrote {rel}")
    print(f"docs-sync: {len(written)} reference page(s) regenerated from contracts/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
