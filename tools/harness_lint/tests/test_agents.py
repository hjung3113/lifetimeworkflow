"""AGENT-01..05 structural gate (D-04) — frontmatter validation of harness/agents/*.md.

Proves success criterion 2 structurally without a runtime: each authored persona carries a
valid, least-privilege frontmatter and the read-only-reviewer invariant (T-03-09, P-perm) holds
in BOTH runtime representations — the opencode ``permission`` block AND the Claude ``tools``
allowlist. The set of personas is pinned to exactly the four enumerated core ones (no sprawl, P1/P8).

Parsing is delegated to the shared ``parse_frontmatter`` (Plan 02) — no per-test fence slicing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.harness_lint import parse_frontmatter

# test_agents.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_AGENTS_DIR = _REPO_ROOT / "harness" / "agents"

# The 15 valid opencode permission keys (CONFIG-02, mirrors harness/permission-matrix.json).
VALID_PERMISSION_KEYS = frozenset(
    {
        "read",
        "edit",
        "bash",
        "glob",
        "grep",
        "list",
        "task",
        "external_directory",
        "todowrite",
        "question",
        "webfetch",
        "websearch",
        "lsp",
        "skill",
        "doom_loop",
    }
)

# "write" is NOT a native opencode key (file writes fall under "edit"); it is tolerated ONLY as an
# explicit deny authored defensively for the read-only invariant — never as an "allow".
WRITE_AFFORDANCE_ALIAS = frozenset({"write"})
ALLOWED_PERMISSION_KEYS = VALID_PERMISSION_KEYS | WRITE_AFFORDANCE_ALIAS

VALID_MODES = frozenset({"primary", "subagent", "all"})

# Exactly the four enumerated CORE personas — the instance-language persona dotnet-engineer
# moved to examples/log-parser/agents/ (Phase 5.5). No more, no less.
EXPECTED_PERSONAS = frozenset({"orchestrator", "python-engineer", "code-reviewer", "explorer"})

# Personas that MUST be read-only in both representations (AGENT-04 reviewer, AGENT-05 explorer).
READ_ONLY_PERSONAS = frozenset({"code-reviewer", "explorer"})

# Write/shell affordance tokens forbidden from a read-only persona's Claude tools allowlist.
_WRITE_TOOL_TOKENS = ("Write", "Bash", "Edit")

# A routing-signal description must carry an invocation trigger token (P7 guard).
_ROUTING_TRIGGERS = ("use", "when")


def _agent_files() -> list[Path]:
    return sorted(_AGENTS_DIR.glob("*.md"))


def _load(path: Path) -> dict:
    fm, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    return fm


def _permission(fm: dict) -> dict:
    perm = fm.get("permission", {})
    return perm if isinstance(perm, dict) else {}


def is_read_only(fm: dict) -> bool:
    """True iff the persona grants NO write/shell affordance in EITHER representation.

    Checks BOTH the opencode ``permission`` block (``edit``/``bash``/``write`` must not resolve to
    an "allow" — present-and-deny or absent are both fine) AND the Claude ``tools`` allowlist string
    (must contain none of Write/Bash/Edit).
    """
    perm = _permission(fm)
    for key in ("edit", "bash", "write"):
        if str(perm.get(key, "deny")) == "allow":
            return False
    tools = str(fm.get("tools", ""))
    return not any(tok in tools for tok in _WRITE_TOOL_TOKENS)


def test_expected_personas_present_no_sprawl() -> None:
    """Exactly the four enumerated core personas exist — no missing, no extra (P1/P8)."""
    names = {_load(p).get("name") for p in _agent_files()}
    assert names == set(EXPECTED_PERSONAS), (
        f"persona set drift: got {sorted(str(n) for n in names)}, "
        f"expected {sorted(EXPECTED_PERSONAS)}"
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
