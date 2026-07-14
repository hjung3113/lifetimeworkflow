"""GEN-03 CONSISTENCY gate (D-03) — the permission-matrix language scopes and the engineer
personas DERIVE from harness/project.toml (config = SSOT, no codegen). See T-05-04 / T-05-05.

Per D-03 "full codegen is overkill", "derived not hardcoded" is satisfied structurally: rather than
generating the matrix / personas from the config, this test asserts the existing hardcoded values
AGREE with the config. A silent divergence — dropping `dotnet *` from the matrix, or a language from
the config, or a persona reference to a missing file — fails the suite. That makes the project.toml
authoritative: the log-parser example instance's values are the config's declared values, and the
hardcoded matrix/persona/command values are reinterpreted as consumers that must match it.

Pure structural test (no subprocess, no runtime), mirroring test_commands.py's idiom: repo-root via
parents[3], real config + real matrix loaded through the shared loaders.
"""

from __future__ import annotations

from pathlib import Path

from tools.harness_config import language_bash_scopes, languages, load_project
from tools.harness_perms import load_matrix

# test_language_config.py -> tests -> harness_lint -> tools -> repo root (parents[3]).
_REPO_ROOT = Path(__file__).resolve().parents[3]


def _matrix_language_allow_scopes() -> set[str]:
    """The permission-matrix bash allow-scopes that correspond to language toolchains.

    The `bash` object encodes last-wins glob rules; the operational rules are the catch-all `*`,
    `git push*`, and `rm -rf*` (mapped to ask/deny). The LANGUAGE scopes are exactly the keys that
    grant `allow` — `dotnet *`, `uv *`, `pytest *`. Deriving them as "the allow-decision keys" (not
    a hardcoded literal) keeps this test honest: it reads the same data the resolver enforces.
    """
    matrix = load_matrix()
    bash = matrix["bash"]
    return {pattern for pattern, decision in bash.items() if decision == "allow"}


def test_matrix_language_scopes_equal_config() -> None:
    """The matrix's language allow-scopes EQUAL the config-derived scope set (SSOT tamper-evidence).

    Divergence in EITHER direction fails: dropping `dotnet *` from the matrix, or removing a lang
    from harness/project.toml, breaks the equality — proving the config is authoritative (T-05-04).
    """
    assert _matrix_language_allow_scopes() == language_bash_scopes(load_project())


def test_each_configured_persona_exists() -> None:
    """Every language's configured `persona` file exists under harness/agents/ (T-05-05)."""
    for lang in languages():
        persona = _REPO_ROOT / lang["persona"]
        assert persona.is_file(), f"{lang['id']!r}: persona {lang['persona']} not found on disk"


def test_each_configured_language_has_id() -> None:
    """Every language declares a non-empty `id` (keyed by the CI matrix step + toolchain install).

    The Phase-6 CI `setup` job subscripts `lang["id"]` unguarded when emitting the matrix; this
    gate makes a missing/blank id fail in pytest with a clear message instead of surfacing only as
    a raw KeyError in CI (CI-01 L4).
    """
    for i, lang in enumerate(languages()):
        assert str(lang.get("id", "")).strip(), f"[[languages]] entry #{i} has empty/missing id"


def test_each_configured_language_has_test_command() -> None:
    """Every language declares a non-empty `test` command (the /test golden-path invocation)."""
    for lang in languages():
        assert str(lang.get("test", "")).strip(), f"{lang['id']!r}: empty test command"


def test_each_configured_language_has_test_paths() -> None:
    """Every language declares a non-empty `test_paths` list[str] whose entries exist on disk.

    The Phase-6 CI matrix fans out over these config-declared targets (CI-01, config-derived not
    hardcoded). Use `.exists()` (NOT `.is_file()` like the persona check): the dotnet leg names a
    `.csproj` file but the python leg names a tests directory.
    """
    for lang in languages():
        paths = lang.get("test_paths", [])
        assert isinstance(paths, list), f"{lang['id']!r}: test_paths is not a list"
        assert paths, f"{lang['id']!r}: empty test_paths"
        for p in paths:
            assert isinstance(p, str), f"{lang['id']!r}: non-str test_paths entry {p!r}"
            assert (_REPO_ROOT / p).exists(), f"{lang['id']!r}: test_paths {p} not found on disk"
