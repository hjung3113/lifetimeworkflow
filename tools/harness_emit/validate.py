"""Emit-time loud-fail cap/shape gate (EMIT-02 criterion 3 — raise-before-write, NEVER truncate).

Runs on the AUTHORED source frontmatter AND on BOTH projected outputs before any file is written.
On a HARD violation it raises :class:`tools.harness_emit.generate.HarnessEmitError`, so the emitter
aborts having written nothing — no partial/truncated tree (mirror ``DocsSyncError``). An over-cap
description is a FAILURE, never a ``[:1024]`` slice.

Every cap comes from :mod:`tools.harness_lint.caps` — the SINGLE source of truth shared with the
structural lints (``test_agents``/``test_skills``). Nothing is re-declared here, so a cap change
lands in exactly one place.
"""

from __future__ import annotations

import re
import warnings

from tools.harness_lint.caps import (
    _BODY_WARN_LINES,
    _DESC_MAX,
    _NAME_MAX,
    _NAME_RE,
    _RESERVED_WORDS,
    _XML_CHARS,
    ALLOWED_PERMISSION_KEYS,
    EXPECTED_SKILLS,
    PLACEHOLDER_MODEL,
    READ_ONLY_PERSONAS,
    VALID_MODES,
    is_read_only,
)


def _fail(message: str) -> None:
    # Local import breaks the generate<->validate import cycle (HarnessEmitError lives in generate).
    from tools.harness_emit.generate import HarnessEmitError

    raise HarnessEmitError(message)


def _fold(text: str) -> str:
    """Collapse whitespace runs (incl. newlines from a ``>-`` block) to one space — match emit."""
    return " ".join(str(text).split())


def check_agent(name: str, fm: dict) -> None:
    """Validate one authored agent's frontmatter — raise on any HARD violation, writing nothing.

    Checks: slug-valid ``name`` that matches the file stem (path-safety, T-07-01); non-empty
    ``description`` within the ≤1024 cap (over-cap → FAIL, never truncate, T-07-05); ``mode`` within
    {primary,subagent,all}; ``permission`` keys ⊆ the 15 valid keys (+ deny-only ``write`` alias);
    ``model`` — if present — exactly the placeholder tier (no real model ID leaks, T-07-03); and the
    read-only invariant on the declared read-only personas.
    """
    fm_name = str(fm.get("name", ""))
    if not fm_name or not _NAME_RE.match(fm_name):
        _fail(f"agent {name!r}: name {fm_name!r} is not a valid slug (^[a-z0-9]+(-[a-z0-9]+)*$)")
    if len(fm_name) > _NAME_MAX:
        _fail(f"agent {name!r}: name length {len(fm_name)} exceeds {_NAME_MAX}")
    if fm_name != name:
        _fail(f"agent {name!r}: frontmatter name {fm_name!r} != file stem {name!r}")

    desc = str(fm.get("description", "")).strip()
    if not desc:
        _fail(f"agent {name!r}: description is missing or empty")
    if len(desc) > _DESC_MAX:
        _fail(
            f"agent {name!r}: description length {len(desc)} exceeds {_DESC_MAX} "
            f"— loud-fail, NEVER truncate"
        )

    mode = fm.get("mode")
    if mode is not None and mode not in VALID_MODES:
        _fail(f"agent {name!r}: invalid mode {mode!r} (not in {sorted(VALID_MODES)})")

    perm = fm.get("permission", {})
    if not isinstance(perm, dict):
        _fail(f"agent {name!r}: permission must be a mapping, got {type(perm).__name__}")
    else:
        extra = set(perm.keys()) - ALLOWED_PERMISSION_KEYS
        if extra:
            _fail(f"agent {name!r}: invalid/over-broad permission keys {sorted(extra)}")

    model = fm.get("model")
    if model is not None and str(model) != PLACEHOLDER_MODEL:
        _fail(
            f"agent {name!r}: model {model!r} is not the placeholder tier {PLACEHOLDER_MODEL!r} "
            f"— no real model identifier may leak into an emitted artifact"
        )

    if name in READ_ONLY_PERSONAS and not is_read_only(fm):
        _fail(
            f"agent {name!r}: read-only persona gained a write/shell affordance in the source "
            f"(edit/bash/write must not resolve to 'allow'; tools must exclude Write/Bash/Edit)"
        )


def check_projections(name: str, opencode_fm: dict, claude_fm: dict) -> None:
    """Assert a read-only persona stays read-only in BOTH projections (EITHER-projection guard)."""
    if name in READ_ONLY_PERSONAS:
        if not is_read_only(opencode_fm):
            _fail(f"agent {name!r}: read-only invariant broke in the opencode projection")
        if not is_read_only(claude_fm):
            _fail(f"agent {name!r}: read-only invariant broke in the Claude projection")


def check_command(name: str, fm: dict) -> None:
    """Validate one authored command's frontmatter — raise on any HARD violation, writing nothing.

    Mirrors ``tools.harness_lint.tests.test_commands``: a non-empty ``description`` within the ≤1024
    cap (over-cap → FAIL, never truncate, T-07-05), a well-formed ``agent`` slug, and — when present
    — a boolean ``subtask``. STRUCTURAL only (no cross-file agent-existence check).
    """
    desc = _fold(fm.get("description", ""))
    if not desc:
        _fail(f"command {name!r}: description is missing or empty")
    if len(desc) > _DESC_MAX:
        _fail(
            f"command {name!r}: description length {len(desc)} exceeds {_DESC_MAX} "
            f"— loud-fail, NEVER truncate"
        )

    agent = fm.get("agent")
    if not isinstance(agent, str) or not agent.strip() or not _NAME_RE.match(agent.strip()):
        _fail(
            f"command {name!r}: agent {agent!r} is not a well-formed slug "
            f"(^[a-z0-9]+(-[a-z0-9]+)*$)"
        )

    if "subtask" in fm and not isinstance(fm["subtask"], bool):
        _fail(f"command {name!r}: subtask must be a boolean, got {type(fm['subtask']).__name__}")


def check_skill(name: str, fm: dict, body: str = "") -> None:
    """Validate one authored skill's frontmatter — HARD caps on name/description, body-cap WARNS.

    Mirrors ``tools.harness_lint.tests.test_skills`` (the caps are IDENTICAL for both runtimes, the
    200-vs-1024 correction): ``name`` ≤64 + slug + == dir + no reserved/XML; ``description`` ≤1024
    non-empty + no reserved/XML. Over-cap name/description raise (T-07-05, NEVER truncate). A body
    over ~500 lines only ``warnings.warn`` (D-07) — it MUST still emit, never a hard fail.
    """
    fm_name = str(fm.get("name", ""))
    if not fm_name:
        _fail(f"skill {name!r}: name is missing or empty")
    if len(fm_name) > _NAME_MAX:
        _fail(f"skill {name!r}: name length {len(fm_name)} exceeds {_NAME_MAX} — NEVER truncate")
    if not _NAME_RE.match(fm_name):
        _fail(f"skill {name!r}: name {fm_name!r} is not a valid slug (^[a-z0-9]+(-[a-z0-9]+)*$)")
    if fm_name != name:
        _fail(f"skill {name!r}: frontmatter name {fm_name!r} != directory {name!r}")
    lowered_name = fm_name.lower()
    if any(w in lowered_name for w in _RESERVED_WORDS):
        _fail(f"skill {name!r}: name contains a reserved vendor word {_RESERVED_WORDS}")
    if any(c in fm_name for c in _XML_CHARS):
        _fail(f"skill {name!r}: name contains an angle-bracket/XML char")

    desc = _fold(fm.get("description", ""))
    if not desc:
        _fail(f"skill {name!r}: description is missing or empty")
    if len(desc) > _DESC_MAX:
        _fail(
            f"skill {name!r}: description length {len(desc)} exceeds {_DESC_MAX} "
            f"— loud-fail, NEVER truncate"
        )
    lowered_desc = desc.lower()
    if any(w in lowered_desc for w in _RESERVED_WORDS):
        _fail(f"skill {name!r}: description contains a reserved vendor word {_RESERVED_WORDS}")
    if any(c in desc for c in _XML_CHARS):
        _fail(f"skill {name!r}: description contains an angle-bracket/XML char")

    line_count = len(body.splitlines())
    if line_count > _BODY_WARN_LINES:
        warnings.warn(
            f"skill {name!r}: SKILL.md body is {line_count} lines "
            f"(> {_BODY_WARN_LINES} recommended) — consider moving depth into references/ "
            f"(advisory, still emits)",
            stacklevel=2,
        )


def check_skill_set(names: set[str]) -> None:
    """Assert the discovered skill set equals ``EXPECTED_SKILLS`` exactly (anti-drift/no-sprawl)."""
    expected = set(EXPECTED_SKILLS)
    if set(names) != expected:
        missing = sorted(expected - set(names))
        extra = sorted(set(names) - expected)
        _fail(f"skill set drift — missing {missing}, unexpected {extra}")


# A placeholder model tier token — the ONLY shape a ``model``/``*_model`` value may take, so no real
# provider model identifier can leak into an emitted artifact (model-identity constraint, T-07-03).
_PLACEHOLDER_MODEL_RE = re.compile(r"^provider/[a-z0-9]+(-[a-z0-9]+)*-tier$")


def check_opencode_config(config: dict, schema: dict) -> None:
    """Validate the emitted ``opencode.json`` — schema conformance + no real model identifier.

    Two HARD gates, both raising :class:`HarnessEmitError` BEFORE any write (loud-fail, no partial
    tree):
      * ``jsonschema.validate`` against the vendored subset schema
        (``harness/opencode.config.schema.json``) — a malformed/typo'd config fails here (T-07-07),
        never silently emitted;
      * every ``model``/``*_model`` value MUST be a placeholder tier token
        (``provider/<...>-tier``) — a real provider model identifier is refused (T-07-03).

    jsonschema is imported locally (already a workspace dependency) to keep the module import-light.
    """
    import jsonschema

    try:
        jsonschema.validate(config, schema)
    except jsonschema.ValidationError as exc:
        _fail(f"opencode.json fails the vendored subset schema: {exc.message}")

    for key, value in config.items():
        if key == "model" or key.endswith("_model"):
            if not _PLACEHOLDER_MODEL_RE.match(str(value)):
                _fail(
                    f"opencode.json {key}={value!r} is not a placeholder tier token "
                    f"(provider/<tier>-tier) — no real model identifier may leak into an "
                    f"emitted artifact"
                )
