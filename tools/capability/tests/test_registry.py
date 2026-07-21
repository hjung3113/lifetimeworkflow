"""LANE-03: the capability registry loads fail-closed, and a route is either allowed or REFUSED."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.capability.__main__ import EXIT_MALFORMED, EXIT_OK, EXIT_REFUSED, main
from tools.capability.registry import (
    DEFAULT_REGISTRY,
    CapabilityError,
    load_capabilities,
    providers_for,
    route_defects,
)

_VALID = """
version = 1

[capability.adversarial-review]
description = "read-only review"
providers = ["code-reviewer", "explorer"]
read_only = true

[capability.implementation]
description = "write code"
providers = ["python-engineer"]
"""


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "capabilities.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_the_shipped_registry_loads() -> None:
    registry = load_capabilities(DEFAULT_REGISTRY)
    assert "adversarial-review" in registry
    assert registry["adversarial-review"].read_only is True
    assert registry["implementation"].read_only is False


def test_providers_are_a_tuple_in_declared_order(tmp_path: Path) -> None:
    registry = load_capabilities(_write(tmp_path, _VALID))
    assert registry["adversarial-review"].providers == ("code-reviewer", "explorer")


@pytest.mark.parametrize(
    "body",
    [
        pytest.param(
            'version = 2\n[capability.x]\ndescription = "d"\nproviders = ["a"]\n', id="version"
        ),
        pytest.param("version = 1\n", id="no-table"),
        pytest.param("version = 1\n[capability]\n", id="empty-table"),
        pytest.param('version = 1\n[capability.x]\nproviders = ["a"]\n', id="no-description"),
        pytest.param('version = 1\n[capability.x]\ndescription = "d"\n', id="no-providers"),
        pytest.param(
            'version = 1\n[capability.x]\ndescription = "d"\nproviders = []\n', id="empty-allowlist"
        ),
        pytest.param(
            'version = 1\n[capability.x]\ndescription = "d"\nproviders = ["a", "a"]\n',
            id="duplicate",
        ),
        pytest.param(
            'version = 1\n[capability.x]\ndescription = "d"\nproviders = ["a"]\nprovider = "b"\n',
            id="unknown-key",
        ),
        pytest.param(
            'version = 1\n[capability.x]\ndescription = "d"\nproviders = ["a"]\nread_only = "yes"\n',
            id="non-boolean-read-only",
        ),
        pytest.param(
            'version = 1\n[capability.x]\ndescription = " "\nproviders = ["a"]\n',
            id="blank-description",
        ),
    ],
)
def test_a_malformed_registry_is_refused_not_ignored(tmp_path: Path, body: str) -> None:
    """Fail-closed: a typo'd key must raise, never silently declare an allowlist nobody checked."""
    with pytest.raises(CapabilityError):
        load_capabilities(_write(tmp_path, body))


def test_a_missing_registry_raises(tmp_path: Path) -> None:
    with pytest.raises(CapabilityError):
        load_capabilities(tmp_path / "absent.toml")


def test_an_allowlisted_agent_is_allowed(tmp_path: Path) -> None:
    registry = load_capabilities(_write(tmp_path, _VALID))
    assert route_defects("adversarial-review", "code-reviewer", registry=registry) == []


def test_an_out_of_allowlist_agent_is_refused(tmp_path: Path) -> None:
    registry = load_capabilities(_write(tmp_path, _VALID))
    defects = route_defects("adversarial-review", "python-engineer", registry=registry)
    assert len(defects) == 1
    assert "python-engineer" in defects[0] and "adversarial-review" in defects[0]
    # The refusal names the allowlist, so the reader learns who WOULD have been permitted.
    assert "code-reviewer" in defects[0]


def test_an_absent_agent_is_a_distinct_refusal(tmp_path: Path) -> None:
    """An unrecorded route must not read the same as a permitted one, nor as a refused one."""
    registry = load_capabilities(_write(tmp_path, _VALID))
    assert route_defects("implementation", None, registry=registry) == [
        "capability implementation requires a named agent, none given"
    ]


def test_an_unknown_capability_is_refused(tmp_path: Path) -> None:
    registry = load_capabilities(_write(tmp_path, _VALID))
    assert route_defects("no-such-capability", "explorer", registry=registry) == [
        "unknown capability: no-such-capability"
    ]
    with pytest.raises(CapabilityError):
        providers_for("no-such-capability", registry=registry)


def test_cli_list_prints_every_capability(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["list"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "adversarial-review" in out and "[read-only]" in out
    assert "implementation" in out


def test_cli_route_exits_zero_when_allowed(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["route", "adversarial-review", "code-reviewer"]) == EXIT_OK
    assert "allowed" in capsys.readouterr().out


def test_cli_route_exits_three_when_refused(capsys: pytest.CaptureFixture[str]) -> None:
    """THE demonstration: an out-of-allowlist route is refused, not merely reported."""
    assert main(["route", "adversarial-review", "python-engineer"]) == EXIT_REFUSED
    assert "REFUSED" in capsys.readouterr().err


def test_cli_reports_a_malformed_registry_distinctly(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    import tools.capability.__main__ as cli

    broken = _write(tmp_path, "version = 9\n")

    def _boom(path: Path = broken) -> dict:
        return load_capabilities(broken)

    monkeypatch.setattr(cli, "load_capabilities", _boom)
    assert main(["list"]) == EXIT_MALFORMED
    assert "malformed" in capsys.readouterr().err
