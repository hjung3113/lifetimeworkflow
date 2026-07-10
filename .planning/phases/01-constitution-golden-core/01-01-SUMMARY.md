# Plan 01-01 Summary — Bootstrap toolchain

**Status:** Complete (with documented deferral)
**Plan:** 01-01 — Bootstrap: idempotent .NET 10 install + uv workspace + SessionStart wiring
**Requirements:** BOOT-01 (deferred runtime), BOOT-02 ✅, BOOT-03 ✅

## What was built

| Task | Result | Commit |
|------|--------|--------|
| 1 — uv workspace root + pinned Python tooling | ✅ Complete — `uv sync --frozen` exit 0, pytest 8.4.2 (not 9.x), `rfc8785`/`jsonschema` import OK; uv bumped 0.8.17→0.11.27 via PyPI | 653f394 |
| 2 — idempotent bootstrap + verify scripts | ✅ Scripts written & correct (idempotent cache-check) — **runtime .NET 10 install DEFERRED** (see below) | a7eda97 |
| 3 — SessionStart wiring (coexist w/ GSD) | ✅ Complete — new entry appended to `.claude/settings.json` SessionStart array; both GSD entries survive | ff6d867 |

## Deferred (environmental policy block — NOT a code defect)

**BOOT-01 runtime install** (`dotnet --version` → `10.` green-gate) is deferred. This container's egress policy returns **403 CONNECT** for all .NET/NuGet download hosts (`builds.dotnet.microsoft.com`, `dotnetcli.azureedge.net`, `dotnetcli.blob.core.windows.net`, `aka.ms`, `*.nuget.org`). Per `/root/.ccr/README.md`, policy denials must not be routed around.

The bootstrap scripts are **self-healing**: `tools/bootstrap/install.sh` runs on every SessionStart and installs .NET 10 the moment those hosts are reachable (allowlisted policy or a pre-provisioned SDK image). Only the install in *this* container is blocked; `tools/bootstrap/verify.sh` will go green automatically once .NET 10 is present.

## Deviations (Rule 3 auto-fixes, in commits)

- `[tool.uv.workspace] exclude = ["tools/bootstrap"]` — uv errors when the `tools/*` glob matches a shell-only dir with no `pyproject.toml`.
- uv upgraded via PyPI (`pip install uv==0.11.27`) instead of `uv self update` (GitHub API rate-limited).

## key-files.created
- `pyproject.toml`, `libs/python/pyproject.toml`, `uv.lock`
- `tools/bootstrap/install.sh`, `tools/bootstrap/verify.sh`, `tools/bootstrap/README.md`
- `.claude/settings.json` (SessionStart entry appended), `.gitignore`

## Self-Check: PASSED (Python scope) · .NET runtime verification DEFERRED (policy)
