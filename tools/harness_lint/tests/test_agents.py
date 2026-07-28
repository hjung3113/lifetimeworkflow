"""AGENT-01..05 structural gate (D-04) — frontmatter validation of harness/agents/*.md.

Proves success criterion 2 structurally without a runtime: each authored persona carries a
valid, least-privilege frontmatter and the read-only-reviewer invariant (T-03-09, P-perm) holds
in BOTH runtime representations — the opencode ``permission`` block AND the Claude ``tools``
allowlist. The set of personas is pinned to exactly the four enumerated core ones (no sprawl, P1/P8).

Parsing is delegated to the shared ``parse_frontmatter`` (Plan 02) — no per-test fence slicing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from tools.harness_lint import parse_frontmatter

# Cap constants + the read-only predicate now live in ONE place (tools/harness_lint/caps.py) so the
# emit-time validators (tools/harness_emit) and this gate share a single definition (07-01, D-04).
# Re-imported here so the existing assertions — and downstream importers of these names via
# ``test_agents`` (e.g. test_agent_templates) — stay green with values UNCHANGED.
from tools.harness_lint.caps import (  # noqa: F401  (re-exported for test_agent_templates)
    ALLOWED_PERMISSION_KEYS,
    EXPECTED_PERSONAS,
    READ_ONLY_PERSONAS,
    VALID_MODES,
    VALID_PERMISSION_KEYS,
    WRITE_AFFORDANCE_ALIAS,
    _permission,
    is_read_only,
)

# test_agents.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_AGENTS_DIR = _REPO_ROOT / "harness" / "agents"
_PERMISSION_MATRIX = _REPO_ROOT / "harness" / "permission-matrix.json"

# The constitution-plane globs that MUST be denied for every persona (including curator's
# derived-only write boundary — MAINT-01/D-05). opencode's `edit` key is not path-globbable, so the
# curator's "never write the constitution" boundary is a fact of this GLOBAL data + the Phase-4
# contract-guard hook, not a per-persona frontmatter list.
_CONSTITUTION_DENY_GLOBS = ("contracts/**", "docs/adr/**", "docs/glossary.md")

# A routing-signal description must carry an invocation trigger token (P7 guard).
_ROUTING_TRIGGERS = ("use", "when")

# The single primary persona is the CONDUCTOR — the evolved orchestrator that routes by pipeline
# stage/component/topology, not only by language (PIPE-02/06). Its authored body/description must
# carry at least one of these routing signals so the anti-sprawl gate also proves the conductor
# role landed on the one primary (no second primary, EXPECTED_PERSONAS stays 4).
_CONDUCTOR_SIGNAL_TOKENS = ("topology", "stage", "component", "pipeline")


def _agent_files() -> list[Path]:
    return sorted(_AGENTS_DIR.glob("*.md"))


def _load(path: Path) -> dict:
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm


def test_expected_personas_present_no_sprawl() -> None:
    """Exactly the four enumerated core personas exist — no missing, no extra (P1/P8)."""
    names = {_load(p).get("name") for p in _agent_files()}
    assert names == set(EXPECTED_PERSONAS), (
        f"persona set drift: got {sorted(str(n) for n in names)}, "
        f"expected {sorted(EXPECTED_PERSONAS)}"
    )


def test_single_primary_carries_conductor_signal() -> None:
    """Exactly one primary persona exists and it carries the conductor/topology routing signal.

    PIPE-02/06 — the conductor is the EVOLVED orchestrator (no second primary); its authored
    description/body must route by pipeline stage/component/topology, not only by language. This
    extends the persona anti-sprawl gate to the conductor role while keeping ``EXPECTED_PERSONAS``
    a 4-member set (a second ``mode: primary`` would fail ``test_expected_personas_present_no_sprawl``).
    """
    primaries = [p for p in _agent_files() if _load(p).get("mode") == "primary"]
    assert len(primaries) == 1, (
        f"expected exactly one primary persona (the conductor), got "
        f"{sorted(p.stem for p in primaries)}"
    )
    primary = primaries[0]
    fm = _load(primary)
    haystack = (str(fm.get("description", "")) + "\n" + primary.read_text(encoding="utf-8")).lower()
    assert any(tok in haystack for tok in _CONDUCTOR_SIGNAL_TOKENS), (
        f"{primary.stem}: the single primary persona lacks a conductor routing signal "
        f"{_CONDUCTOR_SIGNAL_TOKENS} — the conductor must route by pipeline stage/component/topology"
    )


@pytest.mark.parametrize("path", _agent_files(), ids=lambda p: p.stem)
def test_description_is_routing_signal(path: Path) -> None:
    """description present, non-empty, carries a routing trigger token.

    P7 — not a bare label.
    """
    fm = _load(path)
    desc = str(fm.get("description", "")).strip()
    assert desc, f"{path.stem}: description missing or empty"
    lowered = desc.lower()
    assert any(tok in lowered for tok in _ROUTING_TRIGGERS), (
        f"{path.stem}: description lacks a routing trigger ({_ROUTING_TRIGGERS}) — reads as a label"
    )


@pytest.mark.parametrize("path", _agent_files(), ids=lambda p: p.stem)
def test_mode_valid_when_present(path: Path) -> None:
    """Any ``mode`` field is one of {primary, subagent, all}."""
    fm = _load(path)
    if "mode" in fm:
        assert fm["mode"] in VALID_MODES, f"{path.stem}: invalid mode {fm['mode']!r}"


@pytest.mark.parametrize("path", _agent_files(), ids=lambda p: p.stem)
def test_permission_keys_are_valid_subset(path: Path) -> None:
    """Permission keys are a subset of the 15 valid keys (+ the deny-only 'write' alias)."""
    keys = set(_permission(_load(path)).keys())
    extra = keys - ALLOWED_PERMISSION_KEYS
    assert not extra, f"{path.stem}: invalid/over-broad permission keys {sorted(extra)}"


@pytest.mark.parametrize("path", _agent_files(), ids=lambda p: p.stem)
def test_no_real_model_identifier(path: Path) -> None:
    """No persona pins a real model ID — only the placeholder tier token is allowed."""
    fm = _load(path)
    model = str(fm.get("model", "")) if "model" in fm else ""
    if model:
        assert model == "provider/explorer-tier", (
            f"{path.stem}: model {model!r} is not the placeholder tier token"
        )


@pytest.mark.parametrize("name", sorted(READ_ONLY_PERSONAS))
def test_read_only_personas_have_no_write_affordance(name: str) -> None:
    """code-reviewer AND explorer are read-only in BOTH representations (T-03-09, P-perm)."""
    fm = _load(_AGENTS_DIR / f"{name}.md")
    assert is_read_only(fm), (
        f"{name}: has a write/shell affordance — must be read-only in BOTH the opencode "
        f"permission block (no edit/bash/write allow) AND the Claude tools list "
        f"(no Write/Bash/Edit)"
    )


def test_read_only_sees_through_per_glob_permission_dict() -> None:
    """A per-glob permission dict granting ``allow`` is a write affordance — not read-only.

    opencode permission values may be a mapping (``{"git *": "allow", "*": "deny"}``), not just a
    bare string. ``str({...}) == "allow"`` is always False, so a naive check would wrongly report
    such a persona as read-only. Guard against that dict-bypass regression.
    """
    granting = {"permission": {"bash": {"git *": "allow", "*": "deny"}}}
    assert not is_read_only(granting), (
        "a per-glob permission dict granting bash 'allow' slipped past is_read_only (dict-bypass)"
    )
    # An all-deny mapping (and the string 'deny') remain genuinely read-only.
    denying = {"permission": {"bash": {"git *": "deny", "*": "deny"}, "edit": "deny"}}
    assert is_read_only(denying), "an all-deny permission mapping must still read as read-only"


def test_curator_is_admitted_persona() -> None:
    """The curator (MAINT-01) is the 5th enumerated persona and exists on disk."""
    assert "curator" in EXPECTED_PERSONAS, "curator must be an enumerated core persona"
    assert (_AGENTS_DIR / "curator.md").is_file(), "harness/agents/curator.md must exist"


def test_curator_is_not_read_only_but_denies_write() -> None:
    """Curator writes DERIVED (edit+bash allow) so is NOT read-only, yet denies the write alias.

    MAINT-01/D-05: curator needs edit+bash to write the derived plane and run generators, so it is
    deliberately excluded from READ_ONLY_PERSONAS and is_read_only() must return False. But it still
    authors an explicit ``write: deny`` — a defensive floor, distinct from the derived edits it makes.
    """
    assert "curator" not in READ_ONLY_PERSONAS, (
        "curator must stay OUT of READ_ONLY_PERSONAS — it writes the derived plane"
    )
    fm = _load(_AGENTS_DIR / "curator.md")
    assert not is_read_only(fm), "curator has edit+bash allow, so is_read_only() must be False"
    assert fm["mode"] == "subagent", "curator is a subagent — orchestrator stays the sole primary"
    perm = _permission(fm)
    assert str(perm.get("write")) == "deny", "curator must author an explicit write: deny floor"


def test_constitution_paths_denied_globally() -> None:
    """Constitution paths are denied in permission-matrix path_deny_globs (curator's write boundary).

    The curator's derived-only boundary is enforced by this GLOBAL deny + the contract-guard hook,
    not a per-persona glob (opencode's ``edit`` key is not path-globbable). Assert the constitution
    globs are present so the boundary that keeps curator out of contracts/adr/golden holds.
    """
    matrix = json.loads(_PERMISSION_MATRIX.read_text(encoding="utf-8"))
    deny = set(matrix.get("path_deny_globs", []))
    missing = set(_CONSTITUTION_DENY_GLOBS) - deny
    assert not missing, f"constitution globs missing from path_deny_globs: {sorted(missing)}"
