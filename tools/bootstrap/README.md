# tools/bootstrap — ephemeral-container toolchain bootstrap

Self-heals the polyglot toolchain so every later plan can run `dotnet` and `uv run` commands.
Wired into `.claude/settings.json` `SessionStart` (alongside — never replacing — the GSD hooks),
so a fresh ephemeral container bootstraps itself with zero manual steps (D-08/D-09).

## Scripts

| Script | Purpose | Idempotent? |
|--------|---------|-------------|
| `install.sh` | Install .NET 10 SDK (`dotnet-install.sh --channel 10.0 --install-dir $HOME/.dotnet`) if absent, then `uv sync` the workspace | Yes — cached 10.x SDK is skipped silently; `uv sync` is a no-op when already resolved |
| `verify.sh` | Green-gate: assert `$HOME/.dotnet/dotnet --version` starts with `10.` and `uv sync --frozen` succeeds | Yes — read-only assertions |

## Idempotency contract (P5)

`install.sh` is safe to run on **every** SessionStart:

- **First run** (cold container): downloads + installs .NET 10 to `$HOME/.dotnet`, then resolves the uv workspace.
- **Subsequent runs** (warm): the cache-check `test -x $HOME/.dotnet/dotnet && dotnet --version | grep '^10\.'`
  short-circuits the download — the .NET branch is silent and fast. `uv sync` re-resolves cheaply.

This keeps session startup fast and never re-downloads the SDK once cached.

## Security

- Both scripts take **no arguments** and use no string→shell concatenation (T-01-01).
- The .NET installer is fetched over HTTPS from `dot.net` only, to a temp file, then executed.
- `install.sh` never fails session startup: a transient `uv sync` error is swallowed (the golden /
  verify gates surface real breakage instead). `verify.sh` is the strict gate — it exits non-zero
  on any missing/incorrect toolchain.

## Manual use

```bash
bash tools/bootstrap/install.sh   # install (first run) or cache-hit (warm)
bash tools/bootstrap/verify.sh    # assert .NET 10 + uv workspace resolve; exit 0 = green
```

The `DOTNET_ROOT` env var (default `$HOME/.dotnet`) overrides the install/lookup location for both scripts.
