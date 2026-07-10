"""HOOK-03 commit-gate — the composed, non-bypassable-by-model commit surface (D-02, D-06).

Composes THREE built-once assets over the staged tree — it re-implements none of them (D-02: no
re-hashing, no byte-diff, no re-rolled §4.3-4.6 rules):

  1. **contract-drift** — :func:`tools.contract_drift.drift.run_gate` (live JCS manifest vs the
     committed baseline). Blocks on any drift, UNLESS a human-set ``GOLDEN_APPROVE_HUMAN`` token is
     present — then the drift is a logged WARN+PASS ("machines gate, humans ratify", D-05), the
     verbatim :mod:`tools.hooks.contract_guard` precedent. The bypass is DRIFT-ONLY: polyglot and
     golden stay HARD (an approval token can never weaken §4.3-4.6 hygiene or golden equivalence).
     ALWAYS runs.
  2. **polyglot §4.3-4.6** — :func:`tools.polyglot_lint.lint.lint_file` over every staged ``*.tsv``
     (the A-model wire boundary). Blocks on any violation. ALWAYS runs.
  3. **golden-parity** — the :mod:`tools.golden_runner.runner` loop, GATED on .NET availability via
     the same explicit-path probe (:func:`resolve_dotnet`). When the dotnet binary is absent the
     component is SKIPped with a logged line and the gate still evaluates drift + polyglot — an env
     limitation can NEVER silently disable a real gate (D-06 / Pitfall 3 / T-04-13).

``main`` exits 0 iff every non-skipped component passes, else 1 (block). A ``--from-hook`` wrapper
reads the untrusted Claude Bash stdin (:mod:`tools.hooks._stdin`) and engages ONLY when the command
is a ``git commit`` — classified by a **token-walk**, never a naive regex or shell interpolation
(T-04-14, gsd-validate-commit.sh precedent) — emitting a PreToolUse block (exit 2) on failure.

Boundary: stdlib + the three reused in-repo tools. Every child process uses
``subprocess.run([list], shell=False)`` (T-04-14). Zero new packages (T-04-SC).
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

# Reused built-once assets (D-02). Imported at module level so tests can monkeypatch these names
# on THIS module to drive each composed branch without a live .NET / contract tree.
from tools.contract_drift.drift import run_gate
from tools.golden_runner.runner import GOLDEN_DIR, resolve_dotnet, run_golden_case
from tools.hooks._stdin import emit_block, parse_event, read_stdin
from tools.polyglot_lint.lint import lint_file

# commit_gate -> hooks -> tools -> repo root (parents[2]). Overridable in tests.
REPO_ROOT = Path(__file__).resolve().parents[2]

# Human ratification token; a NON-EMPTY value == human-authorized change. Verbatim mirror of the
# contract_guard precedent (contract_guard.py:46,91) — agents must never fabricate it. Scoped to
# the drift component ONLY (D-05): it turns a contract-drift FAIL into a WARN+PASS and never
# weakens polyglot (§4.3-4.6) or golden (equivalence). Empty/blank does NOT authorize.
APPROVAL_ENV = "GOLDEN_APPROVE_HUMAN"


def _human_approved() -> bool:
    """True iff a non-empty, non-blank ``GOLDEN_APPROVE_HUMAN`` is set (mirrors contract_guard:91)."""
    return bool((os.environ.get(APPROVAL_ENV) or "").strip())


@dataclass(frozen=True)
class GateResult:
    """One component's outcome: ``PASS`` | ``FAIL`` | ``SKIP`` + a human-readable detail."""

    name: str
    status: str
    detail: str

    @property
    def blocked(self) -> bool:
        return self.status == "FAIL"


# --- staged tree ---------------------------------------------------------------------------------


def staged_files() -> list[str]:
    """Repo-relative paths of files staged for commit (Added/Copied/Modified), via ``git``.

    ``subprocess.run([list], shell=False)`` — no shell interpolation (T-04-14). A git failure
    (e.g. not a repo) yields ``[]`` so the gate degrades to drift+golden rather than crashing.
    """
    try:
        proc = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            shell=False,
        )
    except OSError:
        return []
    if proc.returncode != 0:
        return []
    return [line for line in proc.stdout.splitlines() if line.strip()]


# --- git subcommand classifier (token-walk, never regex/shell) ----------------------------------

_GIT_GLOBAL_OPTS_WITH_ARG = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--exec-path",
}


def is_git_subcommand(command: str, subcommand: str) -> bool:
    """True iff ``command`` invokes ``git <subcommand>`` — classified by token-walk (T-04-14).

    Handles leading ``VAR=value`` env prefixes, a full-path ``git`` binary, and global options
    (``-C <path>``, ``-c k=v``, ``--git-dir``, …) BEFORE the subcommand — the three cases a naive
    ``^git\\s+commit`` regex misses (gsd-validate-commit.sh #3129 precedent). No shell involved.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return False
    i = 0
    # Skip leading env assignments: NAME=value (not a flag, LHS is an identifier).
    while (
        i < len(tokens)
        and "=" in tokens[i]
        and not tokens[i].startswith("-")
        and tokens[i].split("=", 1)[0].isidentifier()
    ):
        i += 1
    if i >= len(tokens):
        return False
    # The git binary: bare `git` or any path ending in `/git`.
    if tokens[i].rsplit("/", 1)[-1] != "git":
        return False
    i += 1
    # Skip git global options (consuming an argument for the arg-taking ones).
    while i < len(tokens):
        tok = tokens[i]
        if tok in _GIT_GLOBAL_OPTS_WITH_ARG:
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        return tok == subcommand  # first non-option token is the subcommand
    return False


# --- composed components -------------------------------------------------------------------------


def check_drift() -> GateResult:
    """contract-drift component — reuse ``run_gate`` (D-02). Blocks on any drift.

    D-05: when drift is present AND a human ``GOLDEN_APPROVE_HUMAN`` token is set, the FAIL becomes
    a logged WARN+PASS (ratified intentional change) — the verbatim contract_guard precedent. An
    absent/empty/blank token still BLOCKS. The bypass is confined here; polyglot/golden stay hard.
    """
    result = run_gate()
    if result["ok"]:
        return GateResult("contract-drift", "PASS", "live manifest matches the committed baseline")
    listed = ", ".join(f"{rel} ({kind}/{cls})" for rel, kind, cls in result["drifted"])
    if _human_approved():
        return GateResult(
            "contract-drift",
            "PASS",
            f"WARN (ratified) — GOLDEN_APPROVE_HUMAN set, drift accepted: {listed}",
        )
    return GateResult("contract-drift", "FAIL", f"unapproved schema change(s): {listed}")


def check_polyglot(files: list[str]) -> GateResult:
    """polyglot §4.3-4.6 component — reuse ``lint_file`` over staged ``*.tsv`` wire files (D-02)."""
    hits: list[str] = []
    for rel in files:
        if not rel.endswith(".tsv"):
            continue
        path = REPO_ROOT / rel
        if not path.is_file():
            continue
        for v in lint_file(path):
            hits.append(f"{rel}: [{v.rule}] {v.detail}")
    if not hits:
        return GateResult("polyglot", "PASS", "no §4.3-4.6 violations in staged TSV")
    return GateResult("polyglot", "FAIL", "; ".join(hits))


def discover_golden_cases() -> list[str]:
    """Golden case ids = ``golden/*`` subdirs carrying a ``meta.yaml`` (skip README etc.)."""
    if not GOLDEN_DIR.is_dir():
        return []
    return sorted(p.name for p in GOLDEN_DIR.iterdir() if (p / "meta.yaml").is_file())


def check_golden(cases: list[str] | None = None) -> GateResult:
    """golden-parity component — GATED on .NET (D-06).

    Probe ``resolve_dotnet()``; if the binary is not a file, SKIP (logged) so the missing .NET
    runtime can never suppress the drift/polyglot components. Otherwise run each case and block on
    any FAIL.
    """
    dotnet = resolve_dotnet()
    if not os.path.isfile(dotnet):
        return GateResult("golden-parity", "SKIP", f"dotnet absent ({dotnet}) — not run")

    cases = discover_golden_cases() if cases is None else cases
    failed: list[str] = []
    for case in cases:
        out = Path(tempfile.mkstemp(suffix=".tsv")[1])
        try:
            if not run_golden_case(case, out).passed:
                failed.append(case)
        finally:
            out.unlink(missing_ok=True)
    if failed:
        return GateResult("golden-parity", "FAIL", f"golden mismatch: {', '.join(failed)}")
    return GateResult("golden-parity", "PASS", f"{len(cases)} case(s) at parity")


# --- composition ---------------------------------------------------------------------------------


def run_composition() -> int:
    """Run drift + polyglot ALWAYS and golden GATED; return 0 (allow) / 1 (block).

    A SKIP never blocks and never suppresses a sibling FAIL (T-04-13). Every component's line is
    logged; FAIL/BLOCK lines go to stderr so a human/hook sees the reason.
    """
    results = [check_drift(), check_polyglot(staged_files()), check_golden()]
    blocked = False
    for r in results:
        stream = sys.stderr if r.blocked else sys.stdout
        print(f"commit-gate: {r.status:4} [{r.name}] {r.detail}", file=stream)
        blocked = blocked or r.blocked
    if blocked:
        print("commit-gate: BLOCKED — resolve the above before committing.", file=sys.stderr)
        return 1
    print("commit-gate: OK — all active gates pass.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI + hook entrypoint. ``--from-hook`` engages only on a ``git commit`` (token-walk)."""
    argv = sys.argv[1:] if argv is None else argv

    if "--from-hook" in argv:
        event = parse_event(read_stdin())
        if not is_git_subcommand(event.command, "commit"):
            return 0  # not a commit — nothing to gate on the Bash matcher
        if run_composition() != 0:
            print(json.dumps(emit_block("commit-gate blocked this commit (see stderr).")))
            return 2  # Claude PreToolUse block exit code
        return 0

    return run_composition()


if __name__ == "__main__":
    raise SystemExit(main())
