"""RED->GREEN proof for the HOOK-04 contract-guard PreToolUse gate.

Denies a Write/Edit to the CONSTITUTION plane (``contracts/**``, ``docs/adr/**``, ``golden/**``)
unless a human-authorized ``GOLDEN_APPROVE_HUMAN`` token is present in env, and — even on an
approved constitution write — denies a payload whose bytes fail the reused POLY-01 ``lint_bytes``
(§4.3-4.6: BOM / CRLF), because the constitution plane must stay byte-pristine (D-04).

Composition invariants (04-06):
  * CONSTITUTION-ONLY subset: the gate feeds the resolver ``["contracts/**", "docs/adr/**",
    "golden/**"]`` — NOT the full matrix ``path_deny_globs`` union (which also carries ``*.env``,
    secret_scan's domain). A ``*.env`` write is therefore never mislabeled "constitution plane".
  * Empty-string token does NOT bypass: ``approved`` is truthy ONLY on a non-empty, non-blank
    ``GOLDEN_APPROVE_HUMAN`` value (Q1 RESOLVED) — an agent must not fabricate it.
  * Allowed-path byte hygiene is NOT this gate's job: a BOM/CRLF payload into a non-constitution
    path yields NO decision here — format-on-write (04-04, PostToolUse) auto-fixes it. contract-
    guard must not preempt it.
"""

from __future__ import annotations

import io
import json

import pytest

from tools.hooks.contract_guard import decide, main

# A UTF-8 BOM as a decoded string (encodes to EF BB BF) and a CRLF-bearing payload.
BOM_CONTENT = "﻿{}"
CRLF_CONTENT = "a\r\nb\r\n"


# --- decide(): constitution plane + approval (access control) -----------------------------------


def test_unapproved_contracts_write_denied() -> None:
    out = decide("contracts/x.schema.json", "{}", approved=False)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "golden-approve" in reason
    assert "CODEOWNERS" in reason


def test_unapproved_adr_write_denied() -> None:
    out = decide("docs/adr/0002-foo.md", "# ADR\nprose\n", approved=False)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_unapproved_golden_write_denied() -> None:
    out = decide("golden/case/expected/x.tsv", "col1\tcol2\n", approved=False)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_approved_clean_constitution_write_allowed() -> None:
    # Non-empty token present + byte-pristine payload -> no access-control decision (bypass).
    assert decide("contracts/x.schema.json", "{}\n", approved=True) is None


# --- decide(): source paths are not this gate's plane -------------------------------------------


def test_source_path_allowed() -> None:
    assert decide("libs/python/foo.py", "x = 1\n", approved=False) is None


def test_source_path_allowed_even_when_approved() -> None:
    assert decide("libs/python/foo.py", "x = 1\n", approved=True) is None


# --- decide(): on-write polyglot enforcement on the constitution plane (even when approved) ------


def test_approved_constitution_with_bom_still_denied() -> None:
    out = decide("contracts/x.schema.json", BOM_CONTENT, approved=True)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    # Reason must name the polyglot rule, not the approval gate.
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "R1-BOM" in reason or "§4.3" in reason


def test_approved_constitution_with_crlf_still_denied() -> None:
    out = decide("golden/case/expected/x.tsv", CRLF_CONTENT, approved=True)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


# --- decide(): allowed-path byte hygiene is format-on-write's job (do NOT preempt 04-04) ---------


def test_allowed_path_with_bom_no_decision() -> None:
    assert decide("libs/python/foo.py", BOM_CONTENT, approved=False) is None


def test_allowed_path_with_crlf_no_decision() -> None:
    assert decide("libs/python/foo.py", CRLF_CONTENT, approved=False) is None


# --- main(): stdin + GOLDEN_APPROVE_HUMAN env -> deny JSON on hit, silent otherwise --------------


def _run_main(monkeypatch: pytest.MonkeyPatch, payload: dict, token: str | None) -> str:
    """Drive main() in-process: feed stdin, toggle GOLDEN_APPROVE_HUMAN, return captured stdout."""
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    if token is None:
        monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)
    else:
        monkeypatch.setenv("GOLDEN_APPROVE_HUMAN", token)
    import sys as _sys

    captured = io.StringIO()
    monkeypatch.setattr(_sys, "stdout", captured)
    rc = main()
    assert rc == 0
    return captured.getvalue()


def _write(file_path: str, content: str) -> dict:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}}


def test_main_unapproved_constitution_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_main(monkeypatch, _write("contracts/x.schema.json", "{}"), token=None)
    assert '"deny"' in out
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_nonempty_token_bypasses(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_main(monkeypatch, _write("contracts/x.schema.json", "{}\n"), token="human-ok")
    assert out.strip() == ""


def test_main_empty_token_still_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    # Empty string must NOT bypass (Q1 RESOLVED).
    out = _run_main(monkeypatch, _write("contracts/x.schema.json", "{}"), token="")
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_blank_token_still_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    # Whitespace-only value is not a real authorization either.
    out = _run_main(monkeypatch, _write("docs/adr/0003-x.md", "# x\n"), token="   ")
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_source_path_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_main(monkeypatch, _write("libs/python/foo.py", "x = 1\n"), token=None)
    assert out.strip() == ""


def test_main_approved_constitution_bom_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_main(monkeypatch, _write("contracts/x.schema.json", BOM_CONTENT), token="human-ok")
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_allowed_path_bom_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_main(monkeypatch, _write("libs/python/foo.py", BOM_CONTENT), token=None)
    assert out.strip() == ""
