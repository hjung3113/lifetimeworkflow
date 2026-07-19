"""detect.py — language/manifest/documentation/CI/test-surface/candidate-process-boundary
detection feeding :func:`tools.adoption_scan.scan.build_inventory` (ADOPT-01).

Every detection rule is EXTENSION/FILENAME/STRUCTURE-based only — no tree-sitter, no symbol
parsing (26-RESEARCH.md: D-02's conservative bias makes symbol-level inference ``unknown`` anyway).
Operates purely on the ``included`` list already assembled by ``scan.py`` (each entry already
carries ``path``/``size``/``sha256``) — no filesystem access here, so detection can never diverge
from what was actually hashed as an evidence pointer.

D-02 evidence classification ladder, enforced structurally by every function below:
- ``observed`` — direct evidence only: a file/extension is literally present (languages,
  manifests, documentation/CI/test surfaces when the recognized path exists).
- ``inferred`` — strong *structural* signals only: a directory containing a recognized manifest is
  a candidate component root. ``candidate_process_boundaries`` is ALWAYS ``inferred`` — component
  existence is inherently inferred (never ``observed``), per D-02.

Ownership/authority classification (who OWNS a component, contract, or CODEOWNERS path) is out of
scope here — that evidence ladder step belongs to Plan 03's ``plan.py``.
"""

from __future__ import annotations

from pathlib import PurePosixPath

# Extension -> language slug (observed on extension presence, D-02).
_LANGUAGE_BY_EXTENSION: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".cs": "csharp",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".rs": "rust",
    ".sh": "shell",
    ".rb": "ruby",
    ".java": "java",
}

# Manifest filename -> kind (observed on literal file existence, D-02).
_MANIFEST_KIND_BY_NAME: dict[str, str] = {
    "pyproject.toml": "pyproject.toml",
    "package.json": "package.json",
    "go.mod": "go.mod",
    "Cargo.toml": "Cargo.toml",
}


def _evidence(entries: list[dict]) -> list[dict]:
    """Build a sorted evidenceRef list from already-hashed ``included`` entries."""
    return [
        {"path": entry["path"], "sha256": entry["sha256"], "size": entry["size"]}
        for entry in sorted(entries, key=lambda item: item["path"])
    ]


def _surface(
    target: str, entries: list[dict], classification: str, rationale: str | None = None
) -> dict:
    record = {
        "target": target,
        "classification": classification,
        "evidence": _evidence(entries),
    }
    if rationale is not None:
        record["rationale"] = rationale
    return record


def detect_languages(included: list[dict]) -> list[dict]:
    """One ``languageRecord`` per distinct extension found among ``included`` entries.

    ``classification: "observed"`` — extension presence is direct evidence (D-02).
    """
    by_language: dict[str, list[dict]] = {}
    for entry in included:
        suffix = PurePosixPath(entry["path"]).suffix.lower()
        language = _LANGUAGE_BY_EXTENSION.get(suffix)
        if language is None:
            continue
        by_language.setdefault(language, []).append(entry)

    return [
        {
            "name": language,
            "classification": "observed",
            "evidence": _evidence(by_language[language]),
        }
        for language in sorted(by_language)
    ]


def detect_manifests(included: list[dict]) -> list[dict]:
    """One ``manifestRecord`` per recognized manifest file present in ``included``.

    ``classification: "observed"`` — literal file existence (D-02).
    """
    records: list[dict] = []
    for entry in sorted(included, key=lambda item: item["path"]):
        name = PurePosixPath(entry["path"]).name
        kind = _MANIFEST_KIND_BY_NAME.get(name)
        if kind is None and name.endswith(".csproj"):
            kind = "*.csproj"
        if kind is None:
            continue
        records.append(
            {
                "path": entry["path"],
                "kind": kind,
                "classification": "observed",
                "evidence": _evidence([entry]),
            }
        )
    return records


def detect_documentation_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for recognized documentation surfaces (ADR / README / AGENTS.md).

    ``classification: "observed"`` when the recognized path exists (D-02).
    """
    records: list[dict] = []

    adr_entries = [
        entry for entry in included if PurePosixPath(entry["path"]).parts[:2] == ("docs", "adr")
    ]
    if adr_entries:
        records.append(_surface("docs/adr", adr_entries, "observed"))

    readme_entries = [
        entry for entry in included if PurePosixPath(entry["path"]).name in {"README", "README.md"}
    ]
    if readme_entries:
        records.append(_surface("README", readme_entries, "observed"))

    agents_entries = [
        entry for entry in included if PurePosixPath(entry["path"]).name == "AGENTS.md"
    ]
    if agents_entries:
        records.append(_surface("AGENTS.md", agents_entries, "observed"))

    return sorted(records, key=lambda record: record["target"])


def detect_ci_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for CI surfaces (``.github/workflows/*.yml``).

    ``classification: "observed"`` when the recognized path exists (D-02).
    """
    ci_entries = [
        entry
        for entry in included
        if PurePosixPath(entry["path"]).parts[:2] == (".github", "workflows")
    ]
    if not ci_entries:
        return []
    return [_surface(".github/workflows", ci_entries, "observed")]


def detect_test_surfaces(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for test surfaces (a ``tests/`` dir containing ``test_*.py``).

    ``classification: "observed"`` when the recognized path exists (D-02).
    """
    test_entries = [
        entry
        for entry in included
        if PurePosixPath(entry["path"]).parts[:1] == ("tests",)
        and PurePosixPath(entry["path"]).name.startswith("test_")
    ]
    if not test_entries:
        return []
    return [_surface("tests", test_entries, "observed")]


def detect_candidate_process_boundaries(included: list[dict]) -> list[dict]:
    """``surfaceRecord``s for candidate component/process boundaries.

    A directory containing a recognized manifest is a candidate component root.
    ``classification: "inferred"`` ALWAYS — component/member existence is inherently inferred
    (D-02); never ``observed`` for a candidate process boundary.
    """
    manifests = detect_manifests(included)
    records: list[dict] = []
    for manifest in sorted(manifests, key=lambda item: item["path"]):
        directory = str(PurePosixPath(manifest["path"]).parent)
        records.append(
            {
                "target": directory,
                "classification": "inferred",
                "evidence": manifest["evidence"],
                "rationale": "manifest-directory",
            }
        )
    return records
