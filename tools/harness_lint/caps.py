"""Shared cap constants + read-only predicate for the harness structural gates (D-04/D-07).

Single source of truth for the agent/skill caps. Extracted VERBATIM from
``tools/harness_lint/tests/{test_agents,test_skills}.py`` so BOTH the structural lints AND the
``tools/harness_emit`` emit-time validators check against ONE definition — a cap change lands in
exactly one place, never re-declared per consumer. Values are UNCHANGED from the test files they
were lifted out of; those suites import them back so the existing gates stay green.

Import path::

    from tools.harness_lint.caps import VALID_PERMISSION_KEYS, is_read_only, _DESC_MAX, ...

Import-light (stdlib ``re`` only) and free of any ``tools.harness_lint`` submodule dependency, so it
is safe to import directly without tripping the namespace-package conftest ordering hazard that the
lazy ``__init__`` re-export guards against.
"""

from __future__ import annotations

import re

# ---- agent caps (lifted from test_agents.py) ------------------------------------------------

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

# Exactly the five enumerated CORE personas — the instance-language persona
# moved to the log-parser example instance (Phase 5.5). Phase 9 (v2.0 α) adds `curator`, the
# read-mostly owner of derived freshness (MAINT-01): it writes the DERIVED plane only and
# regenerates by invoking existing generators (tools.memory_regen / tools.docs_sync), never its
# own derivation logic. No more, no less.
EXPECTED_PERSONAS = frozenset(
    {"orchestrator", "python-engineer", "code-reviewer", "explorer", "curator"}
)

# Personas that MUST be read-only in both representations (AGENT-04 reviewer, AGENT-05 explorer).
# `curator` is deliberately NOT here — it needs edit+bash to write derived + run generators, so
# is_read_only() correctly returns False for it.
READ_ONLY_PERSONAS = frozenset({"code-reviewer", "explorer"})

# The ONLY model token any persona may pin — a placeholder tier, never a real model ID (Pitfall 5).
PLACEHOLDER_MODEL = "provider/explorer-tier"

# Write/shell affordance tokens forbidden from a read-only persona's Claude tools allowlist.
_WRITE_TOOL_TOKENS = ("Write", "Bash", "Edit")


def _permission(fm: dict) -> dict:
    perm = fm.get("permission", {})
    return perm if isinstance(perm, dict) else {}


def _grants_allow(value: object) -> bool:
    """True iff an opencode permission VALUE grants ``allow``.

    A permission value is either a bare string (``"allow"``/``"deny"``) OR a per-glob mapping
    (e.g. ``{"git *": "allow", "*": "deny"}``). ``str({...}) == "allow"`` is always False, so a
    dict granting ``allow`` for any glob would slip past a naive string check — enumerate the
    mapping's values so a per-glob allow still counts as a write/shell affordance.
    """
    if isinstance(value, dict):
        return any(str(v) == "allow" for v in value.values())
    return str(value) == "allow"


def is_read_only(fm: dict) -> bool:
    """True iff the persona grants NO write/shell affordance in EITHER representation.

    Checks BOTH the opencode ``permission`` block (``edit``/``bash``/``write`` must not resolve to
    an "allow" — present-and-deny or absent are both fine, in bare-string OR per-glob-dict form)
    AND the Claude ``tools`` allowlist string (must contain none of Write/Bash/Edit).
    """
    perm = _permission(fm)
    for key in ("edit", "bash", "write"):
        if _grants_allow(perm.get(key, "deny")):
            return False
    tools = str(fm.get("tools", ""))
    return not any(tok in tools for tok in _WRITE_TOOL_TOKENS)


# ---- skill caps (lifted from test_skills.py) ------------------------------------------------

# Shared caps (BOTH runtimes — the 200-vs-1024 correction; body cap is a warn threshold).
_NAME_MAX = 64
_DESC_MAX = 1024
_BODY_WARN_LINES = 500

# name regex: lowercase alnum segments joined by single hyphens.
_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# Reserved vendor words banned from a skill name/description (Claude skill rules, T-03-19).
_RESERVED_WORDS = ("anthropic", "claude")

# Angle-bracket XML tags are forbidden in name/description (T-03-19).
_XML_CHARS = ("<", ">")

# The enumerated CORE skills — the instance's domain skills and its instance-language skill
# moved to the log-parser example instance (Phase 5.5). Phase 5.7 (Lifecycle Completeness) adds
# four domain-neutral lifecycle skills: golden-debug, polyglot-boundary, gate-model,
# two-plane-memory. Phase 8 (Pipeline Topology) adds one topology-trace skill: pipeline-map.
# Phase 10 (Context-Economy) adds two skills: fan-out-synthesize (the fan-out substrate) and
# context-budget (the delegate-vs-inline heuristic that routes into it).
# Phase 43 (Lifecycle Plane Removal, CER-07) removes the five DISCIPLINE skills Phase 36 added,
# together with the lane-discipline declarations that named them and the wiring gate that checked
# them. Phase 44 (Non-Goal Surface Removal, CER-08) removes `gate-model` together with the orphan
# migration-step command and tool package it documented. The eleven entries below are the whole set.
# No more, no fewer (anti-sprawl).
EXPECTED_SKILLS = frozenset(
    {
        "python-conventions",
        "golden-testing",
        "data-contracts",
        "skill-creator",
        "golden-debug",
        "polyglot-boundary",
        "two-plane-memory",
        "pipeline-map",
        "fan-out-synthesize",
        "context-budget",
        "brownfield-adoption",
    }
)
