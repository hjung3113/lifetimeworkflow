"""MAINT-01/03/04 (D-06/D-09) gate — the derived-freshness boundary + hook posture.

Two structural invariants this phase must hold, proven without a runtime:

1. **Invokes-only-tools (D-06):** the `curator` persona and the `/refresh-memory` command regenerate
   the derived plane by invoking ONLY the existing generators — `tools.memory_regen.*` and
   `tools.docs_sync`. Neither may name any other `tools.<module>` derivation path (a second
   index/hash/render impl would silently diverge from the drift gate).

2. **No-on-write-regen hook posture (MAINT-03/D-09):** freshness is deferred to local
   `/refresh-memory` + the PR/CI stale-derived gate — NOT a heavy per-write hook. So no write-path
   hook (`.claude/settings.json` Pre/PostToolUse groups, or a `harness/plugins/*.ts`
   `tool.execute.before`/`tool.execute.after` hook) may invoke `memory_regen`/`docs_sync`. The
   SessionStart injector (which legitimately runs `tools.memory_regen`) is a session-open `event`
   hook, NOT a write-path hook, and is out of scope here.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# test_derived_freshness.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]
_CURATOR = _REPO_ROOT / "harness" / "agents" / "curator.md"
_REFRESH_MEMORY = _REPO_ROOT / "harness" / "commands" / "refresh-memory.md"
_PLUGINS_DIR = _REPO_ROOT / "harness" / "plugins"
_CLAUDE_SETTINGS = _REPO_ROOT / ".claude" / "settings.json"

# The ONLY tools.* modules the derived-freshness surface may invoke (D-06). Any other
# `tools.<module>` reference in curator.md / refresh-memory.md means inline/alternative derivation.
_ALLOWED_TOOL_MODULES = frozenset({"memory_regen", "docs_sync"})

# Captures the first module segment of a `tools.<module>...` reference (dotted module path).
_TOOLS_MODULE_RE = re.compile(r"tools\.([a-z0-9_]+)")

# The regen tokens that must NOT appear on any on-write hook path (MAINT-03/D-09).
_REGEN_TOKENS = ("memory_regen", "docs_sync")

# opencode write-path hook names (mutate/gate a Write/Edit) — distinct from the session-open `event`
# hook the injector uses.
_WRITE_PATH_HOOK_NAMES = ("tool.execute.before", "tool.execute.after")


def _referenced_tool_modules(text: str) -> set[str]:
    return set(_TOOLS_MODULE_RE.findall(text))


def test_curator_invokes_only_regen_tools() -> None:
    """curator.md references only tools.memory_regen / tools.docs_sync module paths (D-06)."""
    modules = _referenced_tool_modules(_CURATOR.read_text(encoding="utf-8"))
    extra = modules - _ALLOWED_TOOL_MODULES
    assert not extra, (
        f"curator.md references non-generator tools modules {sorted(extra)} — curator must "
        f"regenerate ONLY via {sorted(_ALLOWED_TOOL_MODULES)} (D-06, no inline derivation)"
    )
    # And it must actually name the generators (not a persona that invokes nothing).
    assert modules, "curator.md references no tools.* generator — it must invoke the regen tools"


def test_refresh_memory_invokes_only_regen_tools() -> None:
    """refresh-memory.md references only tools.memory_regen / tools.docs_sync module paths (D-06)."""
    modules = _referenced_tool_modules(_REFRESH_MEMORY.read_text(encoding="utf-8"))
    extra = modules - _ALLOWED_TOOL_MODULES
    assert not extra, (
        f"refresh-memory.md references non-generator tools modules {sorted(extra)} — the command "
        f"must invoke ONLY {sorted(_ALLOWED_TOOL_MODULES)} (D-06, macro-over-generators, no logic)"
    )
    assert modules, "refresh-memory.md invokes no generator — it must shell to the regen tools"


def _iter_hook_commands(node: object) -> list[str]:
    """Collect every ``command`` string reachable from a settings.json hook subtree."""
    found: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "command" and isinstance(value, str):
                found.append(value)
            else:
                found.extend(_iter_hook_commands(value))
    elif isinstance(node, list):
        for item in node:
            found.extend(_iter_hook_commands(item))
    return found


def test_no_memory_regen_on_claude_write_path() -> None:
    """No Claude PreToolUse/PostToolUse hook invokes memory_regen/docs_sync (MAINT-03/D-09).

    SessionStart is intentionally NOT scanned — the injector runs tools.memory_regen there, which is
    the sanctioned session-open refresh, not an on-write regen.
    """
    settings = json.loads(_CLAUDE_SETTINGS.read_text(encoding="utf-8"))
    hooks = settings.get("hooks", {})
    for phase in ("PreToolUse", "PostToolUse"):
        for command in _iter_hook_commands(hooks.get(phase, [])):
            for token in _REGEN_TOKENS:
                assert token not in command, (
                    f"{phase} hook invokes {token!r} on the write path — MAINT-03/D-09 forbids a "
                    f"heavy on-write memory hook; freshness is deferred to /refresh-memory + CI"
                )


def test_no_memory_regen_on_plugin_write_path() -> None:
    """No harness plugin registers memory_regen/docs_sync on a write-path hook (MAINT-03/D-09).

    A plugin may run tools.memory_regen ONLY from the session-open ``event`` hook (the injector). A
    plugin that ALSO registers a ``tool.execute.before``/``tool.execute.after`` write-path hook must
    not reference the regen tools — that would be an on-write memory regen.
    """
    for plugin in sorted(_PLUGINS_DIR.glob("*.ts")):
        text = plugin.read_text(encoding="utf-8")
        has_write_path_hook = any(name in text for name in _WRITE_PATH_HOOK_NAMES)
        references_regen = any(token in text for token in _REGEN_TOKENS)
        assert not (has_write_path_hook and references_regen), (
            f"{plugin.name}: registers a write-path hook AND references a regen tool "
            f"({_REGEN_TOKENS}) — MAINT-03/D-09 forbids on-write memory regen. The injector's "
            f"regen belongs on the session-open `event` hook only."
        )
