"""DOCSUP-05 — the stable grouped report and the pinned 0/1/3 exit mapping.

The report is an INSTRUCTION SURFACE, not a log. Naming the wrong remediation is itself a defect,
independent of whatever the write-side gates deny, so the assertions below are mostly about what
the text TEACHES:

* ``test_report_never_suggests_adr_edit`` — asserted across ALL reachable ADR states, not one
  sampled state, because the wrong-action risk is per-state (D-09).
* ``test_report_distinguishes_three_ledger_reasons`` — the three ledger reasons share the symptom
  "digests disagree" and carry three DIFFERENT fixes. Collapsing them sends the operator down the
  wrong path; in particular ``first_seen-unratified`` is remedied by a human review commit landing
  the row, NOT by re-recording digests.
* ``test_report_does_not_restate_drift`` — contract-drift stays leading and authoritative (D-13).

Exit codes are pinned HERE because Phase 29's ``/docs-update`` binds to them: 0 clean, 1
broken/stale-required/uncovered-regression, 3 registry-or-ledger INVALID. 2 is argparse's stdlib
usage error and is never reused.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from tools.docs_guard import cli
from tools.docs_guard.tests.conftest import git
from tools.docs_guard.tests.test_guard import (
    LED_REL,
    REG_REL,
    _binding_toml,
    _commit,
    _digests,
    _ledger_toml,
    _write,
)

_ONE = ("src/one.py",)

# Words a report must never carry about an ACCEPTED ADR. Append-only / supersede-don't-edit is a
# standing rule; `contract_guard` would deny the write anyway, but a report that teaches the wrong
# action is the defect this row exists to catch.
FORBIDDEN_ADR_IMPERATIVES = (
    "edit the ADR",
    "update the ADR",
    "modify",
    "edit docs/adr",
    "change the ADR",
    "rewrite the ADR",
)

_ADR_PAIR = ("REVIEWED_STILL_CURRENT", "SUPERSEDING_ADR_REQUIRED")


def _render_text(result: dict, impact: dict | None = None) -> str:
    out, err = cli.render(result, impact=impact)
    return "\n".join([*out, *err])


# ── synthetic result helpers (render must work on a plain dict, no live tree needed) ────────────


def _binding_entry(**overrides) -> dict:
    entry = {
        "id": "how-to-one",
        "state": "STALE_REQUIRED",
        "severity": "required",
        "target": "docs/how-to/one.md",
        "sources": ["src/one.py"],
        "dispositions": ["updated", "reviewed-no-change"],
        "disposition": "reviewed-no-change",
        "source_digest": "a" * 64,
        "target_digest": "b" * 64,
        "live_source_digest": "c" * 64,
        "live_target_digest": "b" * 64,
        "reasons": ["reviewed digests no longer match the working tree"],
    }
    entry.update(overrides)
    return entry


def _result(*, bindings=(), findings=(), ok=False, uncovered=None) -> dict:
    return {
        "ok": ok,
        "bindings": list(bindings),
        "uncovered": uncovered or {"live": 0, "max": None, "paths": []},
        "coverage": {"uncovered_max": None, "binding_min": None},
        "findings": list(findings),
    }


def _finding(binding_id: str, reason: str, level: str, message: str) -> dict:
    return {"binding_id": binding_id, "reason": reason, "level": level, "message": message}


# ── the leading-gates header ────────────────────────────────────────────────────────────────────


def test_report_first_line_names_the_leading_gates() -> None:
    out, _err = cli.render(_result(bindings=[_binding_entry()]))
    assert "contract-drift and golden are leading" in out[0]


# ── ADR: never an in-place edit, in ANY reachable state ─────────────────────────────────────────


def _seed_adr_registry(repo: Path) -> None:
    """Three accepted-ADR bindings, one per reachable ADR state: FRESH, STALE_REQUIRED, and the
    open SUPERSEDING_ADR_REQUIRED obligation."""
    targets = {
        "adr-fresh": "docs/adr/0001-fresh.md",
        "adr-stale": "docs/adr/0002-stale.md",
        "adr-open": "docs/adr/0003-open.md",
    }
    for path in targets.values():
        _write(repo, path, f"# {path}\n\n- **Status:** accepted\n")
    _commit(repo, "seed accepted adrs")

    registry = "".join(
        _binding_toml(id=bid, sources=_ONE, target=target, dispositions=_ADR_PAIR)
        for bid, target in targets.items()
    )
    _write(repo, REG_REL, registry)

    rows = []
    for bid, target in targets.items():
        source_digest, target_digest = _digests(repo, _ONE, target)
        if bid == "adr-stale":
            source_digest = "0" * 64  # a digest that cannot match, so the row is genuinely stale
        disposition = "SUPERSEDING_ADR_REQUIRED" if bid == "adr-open" else "REVIEWED_STILL_CURRENT"
        rows.append((bid, source_digest, target_digest, disposition))
    _write(repo, LED_REL, _ledger_toml(tuple(rows)))


def test_report_never_suggests_adr_edit(docs_repo: Path) -> None:
    _seed_adr_registry(docs_repo)
    code = cli.main(
        [
            "--registry",
            str(docs_repo / REG_REL),
            "--ledger",
            str(docs_repo / LED_REL),
            "--root",
            str(docs_repo),
        ]
    )
    assert code == 1  # a stale + an open-obligation ADR binding both fail

    from tools.docs_guard import guard

    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=lambda: {"ok": True, "drifted": []},
    )
    states = {entry["id"]: entry["state"] for entry in result["bindings"]}
    assert states["adr-fresh"] == "FRESH"
    assert states["adr-stale"] == "STALE_REQUIRED"
    assert states["adr-open"] == "STALE_REQUIRED"  # an open obligation can never be green

    text = _render_text(result)
    for forbidden in FORBIDDEN_ADR_IMPERATIVES:
        assert forbidden.lower() not in text.lower(), f"the report suggests {forbidden!r}"
    assert "/adr" in text, "the report must name the supersede path"
    assert "superseding" in text.lower()


# ── the three ledger reasons, three distinct remediations ───────────────────────────────────────


def test_report_distinguishes_three_ledger_reasons() -> None:
    findings = [
        _finding("b-one", "disposition-incoherent", "fail", "disposition-incoherent: b-one ..."),
        _finding("b-two", "first_seen-unratified", "fail", "first_seen-unratified: b-two ..."),
        _finding(
            "b-three", "unverified-disposition", "fail", "unverified-disposition: b-three ..."
        ),
    ]
    bindings = [
        _binding_entry(id="b-one", reasons=["disposition-incoherent"]),
        _binding_entry(id="b-two", reasons=["first_seen-unratified"]),
        _binding_entry(id="b-three", reasons=["unverified-disposition"]),
    ]
    text = _render_text(_result(bindings=bindings, findings=findings))

    remediations = {
        reason: cli.REMEDIATION[reason]
        for reason in ("disposition-incoherent", "first_seen-unratified", "unverified-disposition")
    }
    assert len(set(remediations.values())) == 3, "the three reasons share a remediation line"
    for line in remediations.values():
        assert line in text

    first_seen = remediations["first_seen-unratified"]
    assert "ratif" in first_seen.lower(), "the first_seen remedy is a human ratification commit"
    assert "commit" in first_seen.lower()
    # The remedy for STALENESS is re-recording the digests. Saying that here would send the
    # operator to change a digest that is already correct.
    assert "re-record" not in first_seen.lower()


# ── drift is never restated ─────────────────────────────────────────────────────────────────────


def test_report_does_not_restate_drift(docs_repo: Path) -> None:
    contract = "contracts/sample/greeting.schema.json"
    target = "docs/how-to/one.md"
    _write(docs_repo, contract, '{"title": "greeting"}\n')
    _write(docs_repo, target, "v1\n")
    _commit(docs_repo, "seed")
    source_digest, target_digest = _digests(docs_repo, (contract,), target)
    _write(docs_repo, REG_REL, _binding_toml(id="greeting-doc", sources=(contract,), target=target))
    _write(
        docs_repo,
        LED_REL,
        _ledger_toml((("greeting-doc", source_digest, target_digest, "reviewed-no-change"),)),
    )
    _write(docs_repo, contract, '{"title": "greeting", "type": "object"}\n')

    from tools.docs_guard import guard

    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=lambda: {"ok": False, "drifted": [(contract, "changed", "breaking")]},
    )
    text = _render_text(result)
    assert "SUPPRESSED (contract-drift leading)" in text
    assert "breaking" not in text, "a run_gate classification leaked into the report"


# ── determinism ─────────────────────────────────────────────────────────────────────────────────


def test_report_is_byte_identical() -> None:
    result = _result(
        bindings=[_binding_entry(id="b-two"), _binding_entry(id="b-one")],
        findings=[_finding("b-one", "stale-digest", "fail", "stale-digest: b-one ...")],
        uncovered={"live": 3, "max": 4, "paths": ["docs/how-to/a.md", "docs/how-to/b.md"]},
    )
    assert _render_text(result) == _render_text(json.loads(json.dumps(result)))


def test_report_column_order_is_fixed() -> None:
    """DOCSUP-05's grouping: changed source path + hash prefix, graph impact ids, target doc,
    severity, required disposition — in that order, one stable block per binding."""
    text = _render_text(
        _result(bindings=[_binding_entry()]), impact={"how-to-one": ["converter", "loader"]}
    )
    order = ["sources", "impact", "target", "severity", "dispositions"]
    positions = [text.index(f"{label}") for label in order]
    assert positions == sorted(positions), f"column order drifted: {order}"
    assert "converter, loader" in text
    assert "c" * 12 in text, "the source hash prefix is part of the source column"


def test_report_shows_no_impact_marker_rather_than_an_empty_column() -> None:
    text = _render_text(_result(bindings=[_binding_entry()]), impact={"how-to-one": []})
    assert "(none)" in text


# ── the diff section is git-conditional ─────────────────────────────────────────────────────────


def test_report_omits_diff_when_git_unretrievable(tmp_path: Path) -> None:
    """DOCSUP-05's "diff only when retrievable from git". A repo with no ``HEAD`` cannot supply the
    previous committed ledger, so the reviewed->live delta is withheld and the distinct
    ``unverified-disposition`` reason is shown in its place (D-08)."""
    if shutil.which("git") is None:
        pytest.skip("git binary unavailable")

    repo = tmp_path / "nohead"
    (repo / "src").mkdir(parents=True)
    (repo / "docs" / "how-to").mkdir(parents=True)
    (repo / "src" / "one.py").write_text("ONE = 1\n", encoding="utf-8")
    (repo / "docs" / "how-to" / "one.md").write_text("v1\n", encoding="utf-8")
    assert git(repo, "init", "--initial-branch=main").returncode == 0  # NO commit

    target = "docs/how-to/one.md"
    source_digest, target_digest = _digests(repo, _ONE, target)
    _write(repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=target))
    _write(repo, LED_REL, _ledger_toml((("how-to-one", source_digest, target_digest, "updated"),)))

    from tools.docs_guard import guard

    result = guard.classify(
        registry_path=repo / REG_REL,
        ledger_path=repo / LED_REL,
        root=repo,
        drift_gate=lambda: {"ok": True, "drifted": []},
    )
    text = _render_text(result)
    assert "unverified-disposition" in text
    assert cli.REMEDIATION["unverified-disposition"] in text
    assert cli.DIFF_LABEL not in text, "a digest delta was rendered without retrievable history"


def test_report_shows_diff_when_history_is_retrievable(docs_repo: Path) -> None:
    """Negative control for the row above — the delta must actually appear when it can."""
    target = "docs/how-to/one.md"
    _write(docs_repo, target, "v1\n")
    _commit(docs_repo, "seed target")
    source_digest, target_digest = _digests(docs_repo, _ONE, target)
    _write(docs_repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=target))
    _write(
        docs_repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    _write(docs_repo, "src/one.py", "ONE = 2\n")

    from tools.docs_guard import guard

    result = guard.classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=lambda: {"ok": True, "drifted": []},
    )
    assert cli.DIFF_LABEL in _render_text(result)


# ── exit-code matrix ────────────────────────────────────────────────────────────────────────────


def _argv(repo: Path) -> list[str]:
    return [
        "--registry",
        str(repo / REG_REL),
        "--ledger",
        str(repo / LED_REL),
        "--root",
        str(repo),
    ]


def test_exit_zero_when_clean(docs_repo: Path) -> None:
    target = "docs/how-to/one.md"
    _write(docs_repo, target, "v1\n")
    _commit(docs_repo, "seed target")
    source_digest, target_digest = _digests(docs_repo, _ONE, target)
    _write(docs_repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=target))
    _write(
        docs_repo,
        LED_REL,
        _ledger_toml((("how-to-one", source_digest, target_digest, "reviewed-no-change"),)),
    )
    assert cli.main(_argv(docs_repo)) == 0


def test_exit_zero_with_advisory_on_stderr(docs_repo: Path, capsys) -> None:
    """``STALE_ADVISORY`` warns on stderr and leaves the exit code UNCHANGED."""
    target = "docs/how-to/one.md"
    _write(docs_repo, target, "v1\n")
    _commit(docs_repo, "seed target")
    _write(
        docs_repo,
        REG_REL,
        _binding_toml(id="how-to-one", sources=_ONE, target=target, severity="advisory"),
    )
    assert cli.main(_argv(docs_repo)) == 0
    captured = capsys.readouterr()
    assert "STALE_ADVISORY" in captured.err
    assert "STALE_ADVISORY" not in captured.out


def test_exit_one_when_stale_required(docs_repo: Path) -> None:
    target = "docs/how-to/one.md"
    _write(docs_repo, target, "v1\n")
    _commit(docs_repo, "seed target")
    _write(docs_repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=target))
    assert cli.main(_argv(docs_repo)) == 1


def test_exit_three_on_invalid_registry(docs_repo: Path, capsys) -> None:
    """Exit 3 is a DIFFERENT operator action from exit 1 — fix the registry, not the docs."""
    _write(
        docs_repo,
        REG_REL,
        _binding_toml(id="dup-id", sources=_ONE, target="docs/how-to/one.md")
        + _binding_toml(id="dup-id", sources=_ONE, target="docs/how-to/two.md"),
    )
    assert cli.main(_argv(docs_repo)) == 3
    captured = capsys.readouterr()
    assert captured.err.strip(), "exit 3 must carry a diagnostic"
    assert "Traceback" not in captured.err
    assert "dup-id" in captured.err


def test_exit_three_on_invalid_ledger(docs_repo: Path, capsys) -> None:
    _write(docs_repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target="docs/a.md"))
    _write(docs_repo, LED_REL, "[[reviewed]]\nid = 'x'\nunknown_key = 'zz-leak-canary-zz'\n")
    assert cli.main(_argv(docs_repo)) == 3
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err
    assert "zz-leak-canary-zz" not in captured.err, "ledger CONTENT leaked into the diagnostic"


def test_config_error_in_impact_cannot_escape_the_exit_contract(
    docs_repo: Path, capsys, monkeypatch
) -> None:
    """WR-03 adversarial row: the 0/1/3 contract must hold when the GRAPH config is broken.

    ``main()`` calls ``impact_map(result["bindings"])`` with ``cfg=None`` ONCE per report, which
    reaches ``effective_relationships(None)`` and ``compile_graph(None)`` — both read the live
    ``harness/project.toml`` and both raise ``ValueError`` on a malformed or self-contradictory
    config (e.g. one contract claimed by two authorities). Only ``classify()`` used to sit inside
    the try, so that raise surfaced as a raw traceback and an UNDOCUMENTED exit code out of the CI
    job. The stub reproduces exactly that raise at exactly that call site.

    ``impact.py``'s NEVER-FABRICATE posture already establishes that an EMPTY impact list is the
    correct degraded answer, so the report degrades and keeps its documented code.
    """
    target = "docs/how-to/one.md"
    _write(docs_repo, target, "v1\n")
    _commit(docs_repo, "seed target")
    _write(docs_repo, REG_REL, _binding_toml(id="how-to-one", sources=_ONE, target=target))

    def exploding_impact(bindings, cfg=None):
        raise ValueError("harness/project.toml: contract 'widget' is claimed by two authorities")

    monkeypatch.setattr(cli, "impact_map", exploding_impact)

    code = cli.main(_argv(docs_repo))

    assert code in (0, 1, 3), f"exit {code} is outside the pinned 0/1/3 contract"
    assert code == 1, "the binding is STALE_REQUIRED, so the documented code is 1"
    captured = capsys.readouterr()
    assert "Traceback" not in captured.err + captured.out
    assert "impact" in captured.err.lower(), "the degradation must be stated, not silent"
    assert cli._NO_IMPACT in captured.out + captured.err


def test_missing_registry_is_exit_zero_not_three(docs_repo: Path) -> None:
    """A MISSING registry is exit 0 with zero bindings (plan 28-07 seeds it), never invalid."""
    assert cli.main(_argv(docs_repo)) == 0


def test_help_exits_two_via_argparse_only() -> None:
    """Exit 2 is argparse's stdlib usage error and is never produced deliberately."""
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--nonexistent-flag"])
    assert excinfo.value.code == 2


# ── 28 IN-03 / DEBT-03: one compile per REPORT ──────────────────────────────────────────────────


def test_report_compiles_the_graph_once_for_many_bindings(docs_repo: Path, monkeypatch) -> None:
    """A report over N bindings reads the graph config ONCE, not N times.

    This is the test that fails if `main` regresses to a per-binding `impact_ids` loop. It counts
    the live reads rather than inspecting the output, because a per-binding loop produces the
    IDENTICAL report — the defect was only ever the repeated work, so the report text cannot
    witness it.
    """
    from tools.docs_guard import impact as impact_module

    for name in ("one", "two", "three"):
        target = f"docs/how-to/{name}.md"
        _write(docs_repo, target, "v1\n")
    _commit(docs_repo, "seed targets")
    _write(
        docs_repo,
        REG_REL,
        "\n".join(
            _binding_toml(id=f"how-to-{name}", sources=_ONE, target=f"docs/how-to/{name}.md")
            for name in ("one", "two", "three")
        ),
    )

    calls: list[str] = []
    real_compile = impact_module.compile_graph
    real_relationships = impact_module.effective_relationships
    monkeypatch.setattr(
        impact_module,
        "compile_graph",
        lambda cfg: (calls.append("compile"), real_compile(cfg))[1],
    )
    monkeypatch.setattr(
        impact_module,
        "effective_relationships",
        lambda cfg: (calls.append("relationships"), real_relationships(cfg))[1],
    )

    code = cli.main(_argv(docs_repo))

    assert code in (0, 1, 3)
    assert calls.count("compile") == 1, (
        f"3 bindings compiled the graph {calls.count('compile')}x — 28 IN-03 has regressed"
    )
    assert calls.count("relationships") == 1


def test_report_text_is_unchanged_by_the_batch_impact_path(docs_repo: Path, capsys) -> None:
    """Byte-identity: the compile-once rearrangement must not move a single character of output.

    `render` is driven twice over the same classification — once with the impact map `main` now
    builds in ONE `impact_map` call, once with the per-binding `impact_ids` map it replaced — and
    the two renderings are compared as whole strings.
    """
    from tools.docs_guard.guard import classify
    from tools.docs_guard.impact import impact_ids, impact_map

    for name in ("one", "two"):
        _write(docs_repo, f"docs/how-to/{name}.md", "v1\n")
    _commit(docs_repo, "seed targets")
    _write(
        docs_repo,
        REG_REL,
        "\n".join(
            _binding_toml(id=f"how-to-{name}", sources=_ONE, target=f"docs/how-to/{name}.md")
            for name in ("one", "two")
        ),
    )

    result = classify(
        registry_path=docs_repo / REG_REL,
        ledger_path=docs_repo / LED_REL,
        root=docs_repo,
        drift_gate=lambda: {"ok": True, "drifted": []},
    )

    batched = _render_text(result, impact=impact_map(result["bindings"]))
    looped = _render_text(
        result,
        impact={entry["id"]: impact_ids(entry["sources"]) for entry in result["bindings"]},
    )

    assert batched == looped
