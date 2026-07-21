# Phase 26: Deterministic Brownfield Inventory + Mapping - Pattern Map

**Mapped:** 2026-07-19
**Files analyzed:** 10 new/modified file groups
**Analogs found:** 9 / 10 (90%)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `contracts/harness/adoption/inventory.schema.json` | contract/schema | static schema | `contracts/harness/task-control/evidence.schema.json` | exact |
| `contracts/harness/adoption/plan.schema.json` | contract/schema | static schema | `contracts/harness/topology/relationship.schema.json` | exact |
| `contracts/harness/adoption/manifest.schema.json` | contract/schema | static schema | `contracts/harness/task-control/state.schema.json` | exact |
| `tools/adoption_scan/__init__.py` | module docstring | module metadata | `tools/memory_regen/__init__.py` | exact |
| `tools/adoption_scan/__main__.py` | module entry point | CLI dispatch | `tools/docs_sync/__main__.py` | exact |
| `tools/adoption_scan/scan.py` | utility/core logic | file-I/O + CRUD | `tools/memory_regen/pointer_index.py` | role-match |
| `tools/adoption_scan/detect.py` | utility/detection | transform | `tools/memory_regen/repo_map.py` | role-match |
| `tools/adoption_scan/destinations.py` | utility/resolution | CRUD | `tools/harness_emit/manifest.py` | role-match |
| `tools/adoption_scan/plan.py` | utility/classification | transform | `tools/memory_regen/pointer_index.py` | role-match |
| `tools/adoption_scan/cli.py` | utility/CLI | request-response | `tools/docs_sync/generate.py` | role-match |
| `tools/adoption_scan/pyproject.toml` | configuration | static config | `tools/docs_sync/pyproject.toml` | exact |
| `tools/adoption_scan/tests/conftest.py` | test infrastructure | environment setup | `tools/harness_config/tests/conftest.py` | exact |
| `tools/adoption_scan/tests/test_*.py` (8 test files) | test | validation | `tools/memory_regen/tests/test_pointer_index.py` | role-match |
| `docs/reference/inventory.md` | derived/reference | generated | `docs/reference/evidence.md` | exact |
| `docs/reference/plan.md` | derived/reference | generated | `docs/reference/relationship.md` | exact |
| `docs/reference/manifest.md` | derived/reference | generated | `docs/reference/state.md` | exact |
| `.memory/derived/contracts-index.md` | derived/committed-derived | regenerated | `.memory/derived/contracts-index.md` | exact (reuse) |
| `contracts/.hashes/manifest.json` | derived/constitution | regenerated | `contracts/.hashes/manifest.json` | exact (reuse) |

---

## Pattern Assignments

### JSON Schemas — CONSTITUTION PLANE (3 files)

**Analog family:** `contracts/harness/task-control/*.schema.json` (evidence, state, handoff, task, attestation)

**Schema template pattern** (applies to inventory, plan, manifest schemas):

All three adoption schemas follow the established pattern from `contracts/harness/task-control/evidence.schema.json` (lines 1-126):

**Draft and metadata** (lines 1-5):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://harness.local/contracts/harness/adoption/inventory.schema.json",
  "title": "Brownfield adoption inventory",
  "description": "…what it validates, what it does NOT validate, and schema boundaries…",
```

**Top-level structure** (lines 6-9):
```json
  "type": "object",
  "additionalProperties": false,
  "required": ["field1", "field2", "field3"],
  "properties": {
    "field1": { /* type, constraints */ },
```

**Key constraints from research** (D-01, D-11):
- All three schemas are **self-contained** — no cross-file `$ref` (line 11 shows `$ref: "#/$defs/taskId"`, always local)
- `additionalProperties: false` at every object level (line 7, and repeated in nested objects)
- `required` arrays are explicit (line 8); no implicit fields
- String properties carry `minLength: 1` where applicable
- String arrays carry `uniqueItems: true`
- Shared shapes (`evidencePointer`, `classification`, `disposition`) live in `$defs` and are `$ref`'d by each schema — **duplicate across the three schemas, not shared externally**

**$defs pattern example** (from research §D-05 Question-Record Shape + §Exclusion Rules):
```json
  "$defs": {
    "evidencePointer": {
      "type": "object",
      "additionalProperties": false,
      "required": ["path"],
      "properties": {
        "path": { "type": "string", "minLength": 1, "description": "Repo-relative POSIX path" },
        "sha256": { "type": "string", "pattern": "^[0-9a-f]{64}$" },
        "size": { "type": "integer", "minimum": 0 },
        "excluded": { "type": "string", "enum": ["secret-path", "secret-content", "binary", "vendored", "generated", "source-dump", "size-capped", "symlink-escape"] }
      }
    },
    "classification": {
      "type": "string",
      "enum": ["observed", "inferred", "unknown"]
    },
    "disposition": {
      "type": "string",
      "enum": ["create", "preserve", "conflict", "marker-merge", "derived-regenerate", "human-ratification-required"]
    }
  }
```

---

### Python Tool Package Structure — `tools/adoption_scan/`

#### **`__init__.py`** — Module docstring only

**Analog:** `tools/memory_regen/__init__.py` (lines 1-11)

**Pattern:**
```python
"""adoption_scan — deterministic read-only brownfield inventory + mapping (ADOPT-01/02/03).

A virtual uv-workspace member (sibling of contract_hash/, docs_sync/, memory_regen/),
invoked by module path (`python -m tools.adoption_scan --target <path> --out <dir>`).

Owns three deterministic, determinism-proven artifacts:
1. inventory.json — enumerated paths, exclusions (with reasons), language/manifest/surface detection
2. plan.json — evidence-classified members/components/relationships/questions (observed/inferred/unknown)
3. manifest.json — disposition assignment for every harness destination (create/preserve/conflict/marker-merge/derived-regenerate/human-ratification-required)

Determinism discipline (delete + regenerate byte-identical): confined walk + symlink guards +
sorted output + canonical JSON writer (sort_keys=True, indent=2, ensure_ascii=True) +
committed syrupy snapshots.

Entrypoint: `python -m tools.adoption_scan`.
"""
```

---

#### **`__main__.py`** — CLI entry point

**Analog:** `tools/docs_sync/__main__.py` (lines 1-6)

**Pattern:**
```python
"""Package entrypoint so `python -m tools.adoption_scan` runs the scanner."""

from tools.adoption_scan.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

---

#### **`scan.py`** — Core enumeration + exclusion + hashing

**Analogs:** `tools/memory_regen/pointer_index.py` (walk/confinement idiom), `tools/memory_regen/repo_map.py` (enumeration)

**Module-level patterns** (from pointer_index.py lines 34-50, repo_map.py lines 25-54):
```python
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]  # tools/adoption_scan → tools → repo root
MAX_FILE_BYTES = 256 * 1024  # Configurable; recommend as CLI flag too

# Confinement + symlink-guard idiom (copied from repo_map.py:66-69, pointer_index.py:96-98)
def _iter_files_confined(root: Path) -> list[Path]:
    """Enumerate files under root, symlink-confined, deterministically sorted."""
    files: list[Path] = []
    root_resolved = root.resolve()
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        resolved = p.resolve()
        # Defense-in-depth: skip anything a symlink points outside the subtree.
        if root_resolved != resolved and root_resolved not in resolved.parents:
            continue
        files.append(p)
    return sorted(files, key=lambda x: x.resolve().as_posix())

# Ignore-respecting enumeration with recorded fallback (from research §Code Examples)
def _enumerate(target: Path) -> tuple[list[Path], str]:
    """Enumerate files via git ls-files (preferred) or builtin denylist walk.
    
    Returns (sorted_paths, mode) where mode is "git" or "builtin".
    Mode is recorded in the artifact so a run is self-describing.
    """
    argv = ["git", "-C", str(target), "ls-files", "-z", "--cached", "--others", "--exclude-standard"]
    try:
        proc = subprocess.run(argv, capture_output=True, check=False, shell=False)
        if proc.returncode == 0:
            names = [n for n in proc.stdout.decode("utf-8", "surrogateescape").split("\0") if n]
            return sorted(target / n for n in names), "git"
    except (OSError, FileNotFoundError, UnicodeDecodeError):
        pass
    return _builtin_walk(target), "builtin"

def _builtin_walk(target: Path) -> list[Path]:
    """Denylist walk (vendored, generated, binary, secret paths)."""
    # Implementation uses vendored/generated/binary exclusion rules from research §Exclusion Rules

# Canonical SHA256 for evidence pointers (file bytes, not JSON)
def _file_hash(path: Path, max_bytes: int) -> str | None:
    """Return sha256 hex of file bytes, or None if excluded (size-capped, binary, etc)."""
    try:
        size = path.stat().st_size
        if size > max_bytes:
            return None  # excluded, not read
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except (OSError, UnicodeDecodeError):
        return None

# Exclusion rules (from research §Exclusion Rules, A1-A7)
def classify_exclusions(path: Path, text_prefix: bytes, stat_size: int) -> dict | None:
    """Return exclusion reason (dict with path, size, reason) or None if included.
    
    Checks in order: path-segment denylist (vendored, generated) →
    suffix denylist (binary extensions) → stat size cap → NUL/decode binary detection →
    secret-path globs → secret-content patterns (bounded prefix).
    
    Returns {"path": rel_posix, "size": bytes, "reason": slug} for excluded,
    or None for included.
    """
    # Implementation uses rules from research table §Exclusion Rules
```

**Detection sub-functions** — these are typically in a separate module but can be here:
```python
# Language detection by extension (from repo_map.py)
def language_for_path(path: Path) -> str | None:
    """Detect language by file extension."""
    # Map common extensions to language slugs

# Manifest detection (from research §ADOPT-01, §Recommended structure)
def detect_manifests(root: Path) -> dict:
    """Scan for pyproject.toml, package.json, *.csproj, go.mod, Cargo.toml, etc.
    
    Return {"manifests": [{"path": rel_posix, "type": "pyproject.toml"|"package.json"|..., "evidence": "observed"}]}
    """
```

---

#### **`detect.py`** — Language + manifest + surface detection

**Analog:** `tools/memory_regen/repo_map.py` (lines 200-250, language detection)

**Pattern:**
```python
"""Detection rules for languages, manifests, documentation, ADR, AGENTS, CODEOWNERS, CI surfaces."""

from pathlib import Path

def detect_languages(files: list[Path], base: Path) -> list[dict]:
    """Detect language presence by file extension.
    
    Returns list of observed language records, e.g.
    [{"language": "python", "extensions": [".py", ".pyi"], "evidence": "observed"}]
    """

def detect_manifests(root: Path, base: Path) -> list[dict]:
    """Detect package/component manifests.
    
    Observed: file exists with known extension/name (pyproject.toml, package.json, *.csproj, go.mod).
    Return structured list with path + type + evidence classification.
    """

def detect_documentation_surfaces(root: Path, base: Path) -> list[dict]:
    """Detect docs/, adr/, AGENTS.md, README.md, etc.
    
    Evidence classification: observed (file exists) or inferred (directory structure).
    """

def detect_ci_surfaces(root: Path, base: Path) -> list[dict]:
    """Detect .github/workflows/, .gitlab-ci.yml, Jenkinsfile, etc.
    
    Evidence: observed when file exists.
    """

def detect_codeowners(root: Path, base: Path) -> dict | None:
    """Check for .github/CODEOWNERS; return evidence pointer if present (observed only)."""

def detect_test_surfaces(root: Path, base: Path) -> list[dict]:
    """Detect test roots and infer test commands.
    
    Observed: tests/ directory exists, test_*.py pattern present.
    Inferred: pytest/unittest/xunit command likely, recorded as unknown authority (D-02).
    """

def detect_candidate_process_boundaries(root: Path, base: Path) -> list[dict]:
    """Infer candidate component/module boundaries from structure.
    
    Returns list of inferred boundaries (module roots with manifests, clear directory separations).
    """
```

---

#### **`destinations.py`** — Static destination catalog + disposition rule chain

**Analog:** `tools/harness_emit/manifest.py` (lines 1-100, destination enumeration + ownership)

**Key pattern** (from research §Authoritative Harness Destination Catalog, §Disposition resolution order):

```python
"""The complete harness destination catalog and disposition resolution rules (ADOPT-03).

Disposition is exactly one of: create, preserve, conflict, marker-merge, derived-regenerate,
human-ratification-required, or GSD-excluded.
"""

from pathlib import Path
from tools.harness_emit.manifest import is_gsd_owned
from tools.harness_perms import resolve_path
from tools.hooks.contract_guard import CONSTITUTION_GLOBS
from tools.harness_emit.merge import BEGIN_MARKER, END_MARKER

# Authoritative constitution-plane globs (imported, never retyped)
_CONSTITUTION_GLOBS = CONSTITUTION_GLOBS  # ["contracts/**", "docs/adr/**", "golden/**"]

# Derived-plane globs (from research table, rows 8, 12-13, 26-28)
_DERIVED_GLOBS = [
    "docs/reference/**",
    ".memory/derived/**",
    ".memory/state/**",
    ".opencode/**",
    ".claude/agents/**",
    ".claude/commands/**",
    ".claude/skills/**",
    "opencode.json",
]

# Marker-capable files (from research §Marker-Capability, §D-03)
_MARKER_CAPABLE = {"AGENTS.md", "CLAUDE.md", ".claude/settings.json"}

def destination_catalog() -> list[dict]:
    """Return the complete 40-row harness destination catalog.
    
    Each row: {
      "num": 1,
      "destination": "contracts/**/*.schema.json",
      "plane": "constitution",
      "marker_capable": false,
      "disposition_rule": "human-ratification-required"
    }
    """
    # Rows 1-40 from research table

def disposition(rel: str, target_root: Path, proposed_sha: str | None) -> str | None:
    """Resolve disposition for ONE harness destination (ordered rule chain, total).
    
    Args:
      rel: relative POSIX path from target root (e.g., "contracts/foo/bar.schema.json")
      target_root: Path to the target repo root
      proposed_sha: sha256 hex of proposed content, or None if not yet computed
    
    Returns: disposition string or None (for GSD-excluded)
    
    Rule chain (lines 1-7 from research):
      1. is_gsd_owned(rel) → None (excluded, not a destination)
      2. resolve_path(CONSTITUTION_GLOBS, rel) == "deny" → human-ratification-required
      3. resolve_path(DERIVED_GLOBS, rel) == "deny" → derived-regenerate
      4. rel in MARKER_CAPABLE → marker-merge
      5. not (target_root / rel).exists() → create
      6. sha256(existing) == sha256(proposed) → preserve
      7. otherwise → conflict
    """
    if is_gsd_owned(rel):
        return None  # GSD lanes: excluded from destination catalog
    if resolve_path(_CONSTITUTION_GLOBS, rel) == "deny" or rel == "libs/normalize-spec.md":
        return "human-ratification-required"
    if resolve_path(_DERIVED_GLOBS, rel) == "deny":
        return "derived-regenerate"
    if rel in _MARKER_CAPABLE:
        return "marker-merge"
    existing = target_root / rel
    if not existing.exists():
        return "create"
    # Requires proposed_sha to decide between preserve/conflict
    if proposed_sha is not None:
        existing_sha = hashlib.sha256(existing.read_bytes()).hexdigest()
        return "preserve" if existing_sha == proposed_sha else "conflict"
    return None  # Caller must provide proposed_sha to resolve preserve/conflict
```

---

#### **`plan.py`** — Evidence classification + question records + TOPO candidates

**Analog:** `tools/memory_regen/pointer_index.py` (lines 111-171, build_index pattern)

**Pattern** (from research §Evidence Classification Ladder, §D-05):

```python
"""Classify inventory members as observed/inferred/unknown.

Evidence ladder:
- observed: file/directory exists, literal manifest declaration, file extension present
- inferred: strong structural signal (directory contains manifest = component root)
- unknown: everything else, becomes a question
"""

def evidence_classification(inventory: dict, target: Path, base: Path) -> list[dict]:
    """Classify every detected member/component/relationship as observed/inferred/unknown.
    
    Returns list of classification records, each with:
    {
      "item": "<description>",
      "kind": "language" | "manifest" | "component" | "relationship" | "test-command" | "docs-destination",
      "classification": "observed" | "inferred" | "unknown",
      "evidence": [{"path": rel_posix, "sha256": hex}],
      "rationale": "<human-readable why>"
    }
    """

def generate_questions(classified: list[dict]) -> list[dict]:
    """Emit unresolved items as question records (D-05 shape).
    
    Each question:
    {
      "id": "Q-<sha256(kind + null + target)[:12]>",  # content-derived, stable
      "kind": "relationship-authority" | "contract-candidate" | "component-boundary" | "member-boundary" | "test-command" | "docs-destination" | "agents-boundary" | "codeowners-ownership" | "collision" | "ambiguous-language" | "excluded-file",
      "group": "<grouping category>",
      "target": "<harness destination or topic>",
      "question": "<human question>",
      "classification": "observed" | "inferred" | "unknown",
      "evidence": [{"path": rel_posix, "sha256": hex, "size": bytes}],
      "candidate": {  # optional
        "record_kind": "relationship",
        "record": {"id": "adoption/<contract>/<auth>-><dep>", "contract": "…", "dependents": […]}
      },
      "blocking": true | false
    }
    
    Deterministic ordering: sort by (group, kind, target, id).
    """

def generate_relationship_candidates(inventory: dict, classified: list[dict]) -> list[dict]:
    """Emit relationship candidates in TOPO vocabulary (Phase 24 relationship.schema.json).
    
    Observed authority + dependents → full relationship record.
    Ambiguous authority → question (candidate nested, schema-incomplete).
    """
```

---

#### **`cli.py`** — Argument parsing + main coordination

**Analog:** `tools/docs_sync/generate.py` (main function pattern)

**Pattern:**
```python
"""CLI interface for the adoption scanner.

Usage:
  python -m tools.adoption_scan --target <path> --out <dir> [--max-file-bytes 262144] [--json]

Arguments:
  --target PATH : path to the target (brownfield) repository root (required, must be a directory)
  --out PATH    : output directory for artifacts (required, must NOT be inside --target)
  --max-file-bytes N : size cap for file content hashing (default: 262144 = 256 KiB)
  --json : emit all three artifacts to --out as .json (default); otherwise --out/<type>.json

Outputs (written to --out, never inside --target):
  - inventory.json (inventory.schema.json)
  - plan.json (plan.schema.json)
  - manifest.json (manifest.schema.json)

Exit codes:
  0 = success, all three artifacts written
  1 = validation error (artifact does not conform to schema)
  2 = usage error (invalid arguments)
"""

import argparse
import sys
from pathlib import Path

def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run scanner, write artifacts, validate schemas, return exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", type=Path, required=True, help="Target repo root")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    parser.add_argument("--max-file-bytes", type=int, default=262144, help="Size cap (bytes)")
    parser.add_argument("--json", action="store_true", default=True)
    
    args = parser.parse_args(argv)
    
    # Validation: --out must not resolve inside --target
    target_resolved = args.target.resolve()
    out_resolved = args.out.resolve()
    if target_resolved in out_resolved.parents or target_resolved == out_resolved:
        print(f"Error: --out must not be inside --target", file=sys.stderr)
        return 2
    if not target_resolved.is_dir():
        print(f"Error: --target must be a directory", file=sys.stderr)
        return 2
    
    # Run scan → plan → manifest pipeline
    try:
        inventory = scan.build_inventory(target_resolved, max_bytes=args.max_file_bytes)
        plan = plan_module.build_plan(inventory, target_resolved)
        manifest_data = destinations.build_manifest(inventory, plan, target_resolved)
        
        # Write canonical JSON
        out_resolved.mkdir(parents=True, exist_ok=True)
        inventory_path = _write_artifact(out_resolved / "inventory.json", inventory)
        plan_path = _write_artifact(out_resolved / "plan.json", plan)
        manifest_path = _write_artifact(out_resolved / "manifest.json", manifest_data)
        
        # Validate against schemas
        if not _validate_all_artifacts(inventory_path, plan_path, manifest_path):
            return 1
        
        print(f"✓ {inventory_path}", file=sys.stderr)
        print(f"✓ {plan_path}", file=sys.stderr)
        print(f"✓ {manifest_path}", file=sys.stderr)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

def _write_artifact(path: Path, obj: dict) -> Path:
    """Write canonical JSON: sort_keys=True, indent=2, ensure_ascii=True, + trailing LF."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=True) + "\n"
    path.write_text(text, encoding="utf-8")
    return path

def _validate_all_artifacts(inventory_path: Path, plan_path: Path, manifest_path: Path) -> bool:
    """Validate each artifact against its schema (Draft202012Validator)."""
    # Load schemas from contracts/harness/adoption/
    # Validate each artifact
    # Return True if all valid, False otherwise
```

---

#### **`pyproject.toml`** — Workspace configuration

**Analog:** `tools/docs_sync/pyproject.toml` (lines 1-16)

**Pattern:**
```toml
[project]
name = "logparser-adoption-scan"
version = "0.0.0"
description = "ADOPT-01/02/03 deterministic brownfield inventory + mapping — read-only scan of a target tree (enumeration, exclusion classification, surface detection, evidence ladder, disposition assignment). Zero new external deps; invoked as `python -m tools.adoption_scan --target <path> --out <dir>`."
requires-python = ">=3.11"
# Zero new external packages. All stdlib (pathlib, hashlib, json, subprocess, re, argparse).
# pytest + syrupy for determinism snapshots come from workspace dev group; nothing declared here,
# so `uv sync --all-packages` must not mutate uv.lock.
dependencies = []

[tool.uv]
# Virtual member: no build-system, nothing to package. Imported by module path from the shared
# uv workspace environment (`python -m tools.adoption_scan`); no wheel is built. Mirrors
# tools/contract_hash, tools/docs_sync, tools/memory_regen.
package = false
```

---

#### **`tests/conftest.py`** — Test infrastructure

**Analog:** `tools/harness_config/tests/conftest.py` (lines 1-17)

**Pattern:**
```python
"""Import-path wiring for adoption_scan tests.

adoption_scan is a virtual uv-workspace member (not pip-installed), imported by module path
from the repo root. The tests must put the repo root onto sys.path themselves so that
`from tools.adoption_scan import ...` and `from tools.contract_hash import ...` resolve.

Fixtures:
- repo_root: the repository root (Path)
- tmp_minirepo: THE single synthetic mini-repo tree (D-06), embedding all exclusion cases
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

# tests -> adoption_scan -> tools -> repo root (parents[3])
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """The repository root."""
    return _REPO_ROOT


@pytest.fixture()
def tmp_minirepo(tmp_path: Path) -> Path:
    """THE single synthetic mini-repo tree (D-06).
    
    Embeds (deterministically named):
    - A credentials file (.env with pattern)
    - A config file (Python with credential marker)
    - A binary file (ELF header)
    - A vendored directory (node_modules/)
    - A generated file (@generated marker)
    - An over-cap file (>256 KiB, size-capped)
    - A collision pair (two files with same name, different content)
    - An ambiguous-language file (no extension)
    - An escaping symlink (loop guard test)
    - A pyproject.toml (manifest detection)
    - A .github/workflows/ci.yml (CI surface)
    - A tests/ directory (test surface detection)
    - An ADR file (docs/adr/0001-*.md)
    - An AGENTS.md file (marker-capable)
    
    Domain-neutral vocabulary only (no log-parser, dotnet, equipment references).
    """
    minirepo = tmp_path / "minirepo"
    minirepo.mkdir()
    
    # Credentials file (path-based)
    (minirepo / ".env").write_text("DB_PASS=xyz123\n")
    
    # Config file (pattern-based)
    (minirepo / "config.py").write_text('conf_pass = "xyz123"\n')
    
    # Binary file
    bin_file = minirepo / "binary.bin"
    bin_file.write_bytes(b"\x7fELF\x02\x01\x01\x00" + b"\x00" * 100)
    
    # Vendored directory
    (minirepo / "node_modules" / "package").mkdir(parents=True)
    (minirepo / "node_modules" / "package" / "index.js").write_text("module.exports = {};")
    
    # Generated file
    (minirepo / "generated.py").write_text("# @generated DO NOT EDIT\nprint('hello')\n")
    
    # Over-cap file (300 KiB)
    (minirepo / "large.dat").write_bytes(b"x" * (300 * 1024))
    
    # Collision pair
    (minirepo / "widget_v1.py").write_text("def widget(): return 'v1'\n")
    (minirepo / "widget_v2.py").write_text("def widget(): return 'v2'\n")
    
    # Ambiguous (no extension)
    (minirepo / "README").write_text("# Mini Repo\n")
    
    # Escaping symlink
    (minirepo / "escape").symlink_to("/etc/passwd")  # Test confinement guard
    
    # Manifest
    (minirepo / "pyproject.toml").write_text("[project]\nname = \"test\"\n")
    
    # CI surface
    (minirepo / ".github" / "workflows").mkdir(parents=True)
    (minirepo / ".github" / "workflows" / "test.yml").write_text("name: test\non: [push]\njobs: {}")
    
    # Test surface
    (minirepo / "tests").mkdir()
    (minirepo / "tests" / "test_widget.py").write_text("def test_widget(): pass\n")
    
    # ADR
    (minirepo / "docs" / "adr").mkdir(parents=True)
    (minirepo / "docs" / "adr" / "0001-decision.md").write_text("# Decision\n")
    
    # Marker-capable
    (minirepo / "AGENTS.md").write_text("<!-- BEGIN HARNESS-MANAGED -->\n<!-- END HARNESS-MANAGED -->\n")
    
    return minirepo
```

---

#### **Test files** — Detection + determinism + disposition + validation

**Analogs:**
- `tools/memory_regen/tests/test_pointer_index.py` (determinism + snapshot pattern)
- `tools/harness_emit/tests/test_emit_determinism.py` (byte-identity proof)
- `tools/docs_sync/tests/` (schema validation)

**Test file listing** (from research §Validation Architecture, §Phase Requirements → Test Map):

| Test file | Tests | Analog pattern |
|---|---|---|
| `test_readonly.py` | Target tree unchanged after scan | `pointer_index.py` read-only guard |
| `test_scan_exclusions.py` | One assert per exclusion class (secret, binary, vendored, generated, size-cap, symlink-escape) | pytest parametrized + minirepo fixture |
| `test_determinism.py` | Double-run byte-identical + seeded-shuffle byte-identical | `test_emit_determinism.py` pattern |
| `test_detect.py` | Language + manifest + surface detection | assertion-per-detection rule |
| `test_plan_classification.py` | Observed/inferred/unknown classification + question records + relationship candidates | ADOPT-02 success criteria |
| `test_dispositions.py` | Disposition totality + each of 6 dispositions reachable | property test + rule-chain test |
| `test_schema_conformance.py` | All 3 artifacts validate against their schemas | `Draft202012Validator` pattern |
| `test_snapshots.py` | Committed syrupy snapshot of all 3 artifacts over minirepo | `./__snapshots__/test_snapshots.ambr` |

**Determinism proof pattern** (from research §Determinism Recipe, §Pitfall 5-6):

```python
# DO: write to two independent tmp_path directories, compare bytes
def test_double_run_byte_identical(tmp_path):
    """Two runs of build_inventory over the same tree produce identical bytes."""
    target = setup_minirepo(tmp_path)
    
    out1 = tmp_path / "run1"
    out2 = tmp_path / "run2"
    
    # Run 1
    inv1_path = scan.write(json_path=out1 / "inventory.json", base_dir=target)
    inv1_bytes = inv1_path.read_bytes()
    
    # Run 2
    inv2_path = scan.write(json_path=out2 / "inventory.json", base_dir=target)
    inv2_bytes = inv2_path.read_bytes()
    
    assert inv1_bytes == inv2_bytes, "Determinism failed: two runs produced different bytes"

# DO: shuffle enumeration order, assert output still identical
def test_shuffled_enumeration_byte_identical(tmp_path):
    """Shuffled file enumeration order produces identical output."""
    target = setup_minirepo(tmp_path)
    
    # Capture sorted walk
    normal_bytes = scan.write(json_path=tmp_path / "normal.json", base_dir=target).read_bytes()
    
    # Monkeypatch _iter_files to return shuffled order
    import random
    original_iter = scan._iter_files_confined
    
    def shuffled_iter(root):
        files = original_iter(root)
        return random.Random(1337).sample(files, len(files))  # Seeded for reproducibility
    
    scan._iter_files_confined = shuffled_iter
    shuffled_bytes = scan.write(json_path=tmp_path / "shuffled.json", base_dir=target).read_bytes()
    scan._iter_files_confined = original_iter
    
    assert normal_bytes == shuffled_bytes, "Determinism failed: shuffle produced different bytes"

# DO: committed snapshot (not git diff)
def test_snapshot(snapshot):
    """Snapshot of the minirepo inventory/plan/manifest."""
    minirepo = setup_minirepo(Path.cwd())
    inv = scan.build_inventory(minirepo)
    plan = plan_module.build_plan(inv, minirepo)
    manifest = destinations.build_manifest(inv, plan, minirepo)
    
    # syrupy snapshot: compares against ./__snapshots__/test_snapshot.ambr
    assert (inv, plan, manifest) == snapshot
```

---

### Derived/Generated Files

#### **`docs/reference/inventory.md`**, **`plan.md`**, **`manifest.md`**

**Analog:** `docs/reference/evidence.md`, `docs/reference/relationship.md`, `docs/reference/state.md`

**Generation:** `tools/docs_sync` (run: `uv run python -m tools.docs_sync`)

**Pattern:** Mechanically generated from the new schemas via `tools/docs_sync/generate.py`:
```python
# Each reference page is generated by reading contracts/harness/adoption/<name>.schema.json
# and rendering a Markdown table of properties + type + description + examples
# with a DERIVED header (do not hand-edit).
```

**CI gate:** `stale-derived` job in `.github/workflows/ci.yml` (lines 232-250):
```yaml
- name: Check reference docs are fresh
  run: |
    uv run python -m tools.docs_sync
    uv run python -m tools.memory_regen.contracts_index
    git add -A -- docs/reference .memory/derived/contracts-index.md
    git diff --cached --exit-code
```

---

#### **`.memory/derived/contracts-index.md`**

**Analog:** Existing `.memory/derived/contracts-index.md` (existing file, regenerated)

**Generation:** `tools/memory_regen.contracts_index` (run: `uv run python -m tools.memory_regen.contracts_index`)

**Pattern:** Index of all contracts under `contracts/harness/adoption/` is automatically picked up by the existing `contracts_index` generator.

---

#### **`contracts/.hashes/manifest.json`**

**Analog:** Existing `contracts/.hashes/manifest.json` (existing file, rebaselined)

**Rebaseline:** `tools/contract_hash.hash --write` (run: `uv run python -m tools.contract_hash.hash --write`)

**Pattern:** The glob `**/*.schema.json` under `contracts/` automatically discovers the new three schemas and recomputes the manifest hash.

---

## Shared Patterns (Cross-Cutting)

### Canonical JSON Writer

**Source:** Composition of `tools/memory_regen/pointer_index.py:221` + `tools/evidence/capture.py:36`

**Apply to:** All three artifacts (inventory, plan, manifest), plus any intermediate JSON (like candidates)

**Pattern:**
```python
def _dump(document: dict) -> bytes:
    """The ONE canonical serialization for adoption artifacts.
    
    sort_keys → key order independent of construction order.
    indent=2 → reviewable diffs (matches every artifact in repo).
    ensure_ascii=True → non-ASCII paths cannot vary the bytes.
    trailing "\\n" → POSIX-clean; required for byte-identical re-runs.
    """
    return (json.dumps(document, sort_keys=True, indent=2, ensure_ascii=True) + "\n").encode("utf-8")
```

---

### Confinement + Symlink-Guard Walk

**Source:** `tools/memory_regen/repo_map.py:53-71` (identical pattern in 3 other modules)

**Apply to:** The `_iter_files_confined` function in `scan.py`

**Pattern:**
```python
root_resolved = root.resolve()
for p in sorted(root.rglob("*")):
    if not p.is_file():
        continue
    resolved = p.resolve()
    # Defense-in-depth: skip anything a symlink points outside the subtree.
    if root_resolved != resolved and root_resolved not in resolved.parents:
        continue
    files.append(p)
```

---

### Determinism Discipline

**Source:** `tools/memory_regen/pointer_index.py:12-15` (module docstring)

**Apply to:** All output generation (inventory, plan, manifest)

**Seven rules** (research §Determinism Recipe):
1. Sort the walk: `sorted(root.rglob("*"))`
2. Sort every emitted list by explicit, total key
3. Repo-relative POSIX paths only: `resolved.relative_to(base).as_posix()`
4. No timestamps (never `datetime.now()`)
5. No raw floats (rank-only, not score)
6. Explicit tie-break on every sort (append stable id to tuple)
7. Sort keys must be data, not enumeration position

---

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `tools/adoption_scan/scan.py` (confinement + size-cap hybrid) | utility | file-I/O | The `tools/evidence/capture.py` gap analysis (research §D-07) shows no single module combines confined walk + size-cap + content hashing without subprocess execution. Pattern copied from fragments of four modules (`repo_map`, `pointer_index`, `harness_emit`, `contract_hash`). |

---

## Metadata

**Analog search scope:** `tools/`, `contracts/harness/`, `libs/python/`, `.github/workflows/`, `docs/reference/`, `.memory/derived/`

**Files scanned:** 40+ existing modules in tools/, contracts, and supporting infrastructure

**Pattern extraction date:** 2026-07-19

**High-confidence analogs (exact match):** 9/10
- JSON schema styling (3 files) — direct from task-control
- Module docstrings and entrypoints (2 files) — direct from docs_sync, memory_regen
- Pyproject.toml (1 file) — direct from docs_sync
- Test conftest (1 file) — direct from harness_config
- Derived docs (3 files) — reuse existing docs_sync generator + existing .memory files

**Role-match analogs (pattern, not exact code):** 5/10
- Core scan logic — hybrid of repo_map + pointer_index + evidence (no single module combines all three)
- Detection rules — repo_map language detection pattern
- Disposition resolution — harness_emit manifest ownership resolution pattern
- Evidence classification — pointer_index build_index pattern
- CLI coordination — docs_sync generate.py main() pattern

**Ready for planning:** Yes. All files have identified analogs; code excerpts are concrete with line numbers.
