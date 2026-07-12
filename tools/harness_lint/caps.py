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

# Exactly the four enumerated CORE personas — the instance-language persona
# moved to the log-parser example instance (Phase 5.5). No more, no less.
EXPECTED_PERSONAS = frozenset({"orchestrator", "python-engineer", "code-reviewer", "explorer"})

# Personas that MUST be read-only in both representations (AGENT-04 reviewer, AGENT-05 explorer).
READ_ONLY_PERSONAS = frozenset({"code-reviewer", "explorer"})

# The ONLY model token any persona may pin — a placeholder tier, never a real model ID (Pitfall 5).
PLACEHOLDER_MODEL = "provider/explorer-tier"

# Write/shell affordance tokens forbidden from a read-only persona's Claude tools allowlist.
_WRITE_TOOL_TOKENS = ("Write", "Bash", "Edit")


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
# No more, no fewer (anti-sprawl).
EXPECTED_SKILLS = frozenset(
    {
        "python-conventions",
        "golden-testing",
        "data-contracts",
        "skill-creator",
        "golden-debug",
        "polyglot-boundary",
        "gate-model",
        "two-plane-memory",
        "pipeline-map",
    }
)
