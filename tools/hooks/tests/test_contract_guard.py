"""RED->GREEN proof for the HOOK-04 contract-guard PreToolUse gate.

Denies a Write/Edit to the CONSTITUTION plane (``contracts/**``, ``docs/adr/**``,
``docs/glossary.md``) unless a human-authorized ``GOLDEN_APPROVE_HUMAN`` token is present in env, and — even on an
approved constitution write — denies a payload whose bytes fail the reused POLY-01 ``lint_bytes``
(§4.3-4.6: BOM / CRLF), because the constitution plane must stay byte-pristine (D-04).

Composition invariants (04-06):
  * CONSTITUTION-ONLY subset: the gate feeds the resolver ``["contracts/**", "docs/adr/**",
    "docs/glossary.md"]``, which is now identical to the matrix ``path_deny_globs`` — the matrix
    carries no row this gate does not enforce.
  * Empty-string token does NOT bypass: ``approved`` is truthy ONLY on a non-empty, non-blank
    ``GOLDEN_APPROVE_HUMAN`` value (Q1 RESOLVED) — an agent must not fabricate it.
  * Allowed-path byte hygiene is NOT this gate's job: a BOM/CRLF payload into a non-constitution
    path yields NO decision here — format-on-write (04-04, PostToolUse) auto-fixes it. contract-
    guard must not preempt it.
"""

from __future__ import annotations

import io
import json
import subprocess
from fnmatch import fnmatchcase
from pathlib import Path

import pytest

from tools.hooks.contract_guard import decide, main

# The repo root — Claude's real hook stdin sends file_path as an ABSOLUTE path under this root.
_REPO_ROOT = Path(__file__).resolve().parents[3]

# A UTF-8 BOM as a decoded string (encodes to EF BB BF) and a CRLF-bearing payload.
BOM_CONTENT = "﻿{}"
CRLF_CONTENT = "a\r\nb\r\n"


@pytest.fixture(autouse=True)
def _no_ambient_dev_bypass(monkeypatch: pytest.MonkeyPatch) -> None:
    """Strip HARNESS_DEV_BYPASS so a dev session's own opt-out never pollutes the deny assertions."""
    monkeypatch.delenv("HARNESS_DEV_BYPASS", raising=False)


# --- decide(): constitution plane + approval (access control) -----------------------------------


def test_unapproved_contracts_write_denied() -> None:
    out = decide("contracts/x.schema.json", "{}", approved=False)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "GOLDEN_APPROVE_HUMAN" in reason
    assert "CODEOWNERS" in reason


def test_unapproved_adr_write_denied() -> None:
    out = decide("docs/adr/0002-foo.md", "# ADR\nprose\n", approved=False)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_approved_clean_constitution_write_allowed() -> None:
    # Non-empty token present + byte-pristine payload -> no access-control decision (bypass).
    assert decide("contracts/x.schema.json", "{}\n", approved=True) is None


# --- decide(): ABSOLUTE file_path (Claude's real hook input) must still be gated (H1 regression) --


def test_unapproved_absolute_constitution_write_denied() -> None:
    # Claude sends an absolute path; the prefix-anchored deny globs must still match after
    # repo-relative normalization (else the constitution gate silently no-ops in real sessions).
    abs_path = str(_REPO_ROOT / "contracts" / "x.schema.json")
    out = decide(abs_path, "{}", approved=False)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_absolute_source_path_allowed() -> None:
    abs_path = str(_REPO_ROOT / "libs" / "python" / "foo.py")
    assert decide(abs_path, "x = 1\n", approved=False) is None


def test_absolute_path_outside_repo_not_constitution() -> None:
    # A path that is not under the repo root cannot be a constitution write here.
    assert decide("/etc/passwd", "root:x:0:0", approved=False) is None


def test_main_absolute_constitution_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    abs_path = str(_REPO_ROOT / "docs" / "adr" / "0003-x.md")
    out = _run_main(monkeypatch, _write(abs_path, "# x\n"), token=None)
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


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
    out = decide("contracts/x.schema.json", CRLF_CONTENT, approved=True)
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


# --- main(): HARNESS_DEV_BYPASS local-dev opt-out (secure default, distinct from the token) ------


def _run_main_io(
    monkeypatch: pytest.MonkeyPatch, payload: dict, token: str | None, dev: str | None
) -> tuple[str, str]:
    """Drive main() toggling BOTH GOLDEN_APPROVE_HUMAN and HARNESS_DEV_BYPASS; return (stdout, stderr)."""
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(payload)))
    if token is None:
        monkeypatch.delenv("GOLDEN_APPROVE_HUMAN", raising=False)
    else:
        monkeypatch.setenv("GOLDEN_APPROVE_HUMAN", token)
    if dev is None:
        monkeypatch.delenv("HARNESS_DEV_BYPASS", raising=False)
    else:
        monkeypatch.setenv("HARNESS_DEV_BYPASS", dev)
    import sys as _sys

    out, err = io.StringIO(), io.StringIO()
    monkeypatch.setattr(_sys, "stdout", out)
    monkeypatch.setattr(_sys, "stderr", err)
    rc = main()
    assert rc == 0
    return out.getvalue(), err.getvalue()


def test_main_dev_bypass_allows_constitution_with_note(monkeypatch: pytest.MonkeyPatch) -> None:
    # SC1: dev flag waives the access-control deny; a distinct on-plane dev-note lands on stderr.
    out, err = _run_main_io(monkeypatch, _write("docs/adr/0007-x.md", "# x\n"), token=None, dev="1")
    assert out.strip() == ""  # no deny
    assert "HARNESS_DEV_BYPASS" in err
    assert "CODEOWNERS" in err
    assert "ratified" not in err.lower()  # never mislabeled human-ratified


def test_main_dev_bypass_bom_still_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    # SC2: byte-hygiene is NOT waived by the dev flag.
    out, _err = _run_main_io(
        monkeypatch, _write("contracts/x.schema.json", BOM_CONTENT), token=None, dev="1"
    )
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_dev_bypass_unset_still_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    # SC4 regression: default (flag unset, no token) still denies.
    out, _err = _run_main_io(
        monkeypatch, _write("contracts/x.schema.json", "{}"), token=None, dev=None
    )
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


@pytest.mark.parametrize("blank", ["", "   "])
def test_main_dev_bypass_blank_still_denies(monkeypatch: pytest.MonkeyPatch, blank: str) -> None:
    # SC4 blank-rule: empty/whitespace flag does NOT bypass (mirrors the token rule).
    out, _err = _run_main_io(
        monkeypatch, _write("docs/adr/0007-x.md", "# x\n"), token=None, dev=blank
    )
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_dev_bypass_source_path_no_note(monkeypatch: pytest.MonkeyPatch) -> None:
    # The dev-note is on-plane only: a source-path write under the dev flag prints nothing.
    out, err = _run_main_io(
        monkeypatch, _write("libs/python/foo.py", "x = 1\n"), token=None, dev="1"
    )
    assert out.strip() == ""
    assert err.strip() == ""


# --- docs/glossary.md: a constitution member in its own right (ADR-0001, as amended) ------------
#
# `docs/adr/0001-walking-skeleton-golden-core.md:48` declares the constitution plane; ADR-0012
# clause (d) supersedes it to the extent that `golden/**` leaves the constitution-plane core, so the
# plane is `contracts/`, `docs/adr/` AND `docs/glossary.md`. The Phase-4 gate shipped without the
# glossary; it was agent-writable in every session until that fix.
#
# Every row below names the LITERAL `docs/glossary.md`. A `docs/*.md` shaped fixture is forbidden
# here: it would pass against a broad glob that also swallowed the how-to and explanation trees,
# proving nothing about the one authoritative file. This is the repo's recurring defect — a control
# ships GREEN because the fixture used the one spelling the control already handled — so the glob
# and the fixture are deliberately the same literal string.


def test_unapproved_glossary_write_denied() -> None:
    out = decide("docs/glossary.md", "# Glossary\n", approved=False)
    assert out is not None, "docs/glossary.md is constitution plane per ADR-0001:48"
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "GOLDEN_APPROVE_HUMAN" in reason
    assert "CODEOWNERS" in reason


def test_unapproved_absolute_glossary_write_denied() -> None:
    # Claude sends an absolute path; the gate must still match after repo-relative normalization,
    # or the glossary is silently ungated in real sessions exactly as it was before this fix.
    abs_path = str(_REPO_ROOT / "docs" / "glossary.md")
    out = decide(abs_path, "# Glossary\n", approved=False)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_approved_glossary_write_allowed() -> None:
    # A human token bypasses access control on the glossary exactly as on the other three members.
    assert decide("docs/glossary.md", "# Glossary\n", approved=True) is None


def test_approved_glossary_with_bom_still_denied() -> None:
    # Byte hygiene applies to the whole plane: an approved glossary write with a BOM is still denied
    # for the polyglot reason, not the approval reason.
    out = decide("docs/glossary.md", BOM_CONTENT, approved=True)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    reason = out["hookSpecificOutput"]["permissionDecisionReason"]
    assert "R1-BOM" in reason or "§4.3" in reason


def test_approved_glossary_with_crlf_still_denied() -> None:
    out = decide("docs/glossary.md", CRLF_CONTENT, approved=True)
    assert out is not None
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_neighbouring_docs_paths_are_not_constitution() -> None:
    # The negative control that keeps the fix honest: the plane gained ONE literal file, not the
    # docs tree. If someone "fixes" this with `docs/**` or `docs/*.md`, these rows go red.
    for path in (
        "docs/how-to/task-lifecycle.md",
        "docs/explanation/template-and-instances.md",
        "docs/tutorials/README.md",
        "docs/glossary-notes.md",
        "docs/reference/deny-domains.md",
    ):
        assert decide(path, "# doc\n", approved=False) is None, (
            f"{path} is human-authored docs, NOT constitution plane"
        )


def test_main_glossary_denies(monkeypatch: pytest.MonkeyPatch) -> None:
    out = _run_main(monkeypatch, _write("docs/glossary.md", "# Glossary\n"), token=None)
    assert json.loads(out)["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_main_dev_bypass_allows_glossary(monkeypatch: pytest.MonkeyPatch) -> None:
    # ADR-0007: the dev bypass covers the whole constitution plane, so it must reach the glossary
    # too — otherwise the fourth member behaves differently from the other three.
    out, err = _run_main_io(
        monkeypatch, _write("docs/glossary.md", "# Glossary\n"), token=None, dev="1"
    )
    assert out.strip() == ""
    assert err.strip() != ""


def test_every_declared_plane_member_is_independently_enforced() -> None:
    # Mutation proof, in-suite: deleting ANY single member from CONSTITUTION_GLOBS must make its own
    # path allowed. Without this, a member can be dropped while the suite stays green because some
    # other member's row still covers the "constitution is enforced" claim.
    import tools.hooks.contract_guard as cg

    probes = {
        "contracts/**": "contracts/x.schema.json",
        "docs/adr/**": "docs/adr/0002-foo.md",
        "docs/glossary.md": "docs/glossary.md",
    }
    assert set(cg.CONSTITUTION_GLOBS) == set(probes), (
        "CONSTITUTION_GLOBS changed — ADR-0001:48 as superseded by ADR-0012 clause (d) declares "
        "exactly these three members; adding or removing one requires a superseding ADR, and this "
        "table must move with it"
    )
    original = list(cg.CONSTITUTION_GLOBS)
    try:
        for glob, probe in probes.items():
            cg.CONSTITUTION_GLOBS[:] = [g for g in original if g != glob]
            assert decide(probe, "x\n", approved=False) is None, (
                f"deleting {glob!r} did not stop denying {probe!r} — another glob is covering it, "
                "so this member is not independently enforced"
            )
            cg.CONSTITUTION_GLOBS[:] = original
            assert decide(probe, "x\n", approved=False) is not None, (
                f"restoring {glob!r} did not re-deny {probe!r}"
            )
    finally:
        cg.CONSTITUTION_GLOBS[:] = original


def _tracked_paths() -> list[str]:
    """Every git-tracked path in this repo (``git ls-files``, ``shell=False``).

    Same subprocess idiom as ``tools/harness_lint/tests/test_core_no_example_dep.py`` — the
    established way to ground an assertion in the real index rather than a hand-kept list.
    """
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return [line.strip() for line in completed.stdout.splitlines() if line.strip()]


def test_every_constitution_glob_matches_a_tracked_file() -> None:
    """No ``CONSTITUTION_GLOBS`` member may match ZERO tracked files (ROADMAP SC-1, glob clause).

    The sibling mutation proof above shows each member is INDEPENDENTLY enforced; it cannot show
    that the member still has a subject. A glob whose tree is gone denies nothing while still
    advertising a plane — the ``golden/**`` defect Phase 44 left behind, caught then by reading and
    asserted here mechanically.

    Matched with ``fnmatch.fnmatchcase``, the SAME matcher ``resolve_path`` (and therefore this
    gate) uses at runtime, so a member that passes here is one the gate could actually act on.

    SCOPE — deliberately NOT extended to ``tools/adoption_scan/scan.py``'s ``SECRET_PATH_GLOBS`` or
    ``tools/adoption_scan/destinations.py``'s ``_CATEGORY_GLOBS``: their subject is a SCANNED
    brownfield TARGET repository, not this checkout, so a zero-match there is correct behaviour and
    asserting otherwise would be a false failure. Do not widen this test to them.
    """
    import tools.hooks.contract_guard as cg

    globs = list(cg.CONSTITUTION_GLOBS)
    assert globs, "CONSTITUTION_GLOBS is empty — the plane declaration itself is gone"
    tracked = _tracked_paths()
    dead = [g for g in globs if not any(fnmatchcase(p, g) for p in tracked)]
    assert not dead, (
        f"CONSTITUTION_GLOBS members matching ZERO git-tracked files: {dead} — a plane member with "
        "no subject is a dead control; remove it (with a superseding ADR) or repoint it"
    )
