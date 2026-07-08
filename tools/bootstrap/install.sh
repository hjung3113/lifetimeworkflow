#!/usr/bin/env bash
# Idempotent toolchain bootstrap for the ephemeral container (BOOT-01/02, D-08/D-09).
#
# Contract: safe to run on EVERY SessionStart.
#   - .NET 10 SDK already present  -> silent skip (P5: keep SessionStart fast/quiet)
#   - .NET 10 SDK absent           -> install via dotnet-install.sh --channel 10.0
#   - uv workspace                 -> resolve (idempotent)
#
# Security (T-01-01): takes NO arguments; no string+shell concatenation; the .NET installer is
# fetched over HTTPS from dot.net only. Never pass untrusted input to a shell.
set -euo pipefail

DOTNET_ROOT="${DOTNET_ROOT:-$HOME/.dotnet}"
export DOTNET_ROOT
export PATH="$DOTNET_ROOT:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# --- .NET 10 SDK (BOOT-01) -------------------------------------------------
# Cache-check: an installed 10.x SDK short-circuits the (slow) download branch.
if [ -x "$DOTNET_ROOT/dotnet" ] && "$DOTNET_ROOT/dotnet" --version 2>/dev/null | grep -q '^10\.'; then
    :  # cached hit — nothing to do (quiet path)
else
    echo "[bootstrap] .NET 10 SDK not found; installing to $DOTNET_ROOT"
    install_script="$(mktemp)"
    curl -fsSL https://dot.net/v1/dotnet-install.sh -o "$install_script"
    bash "$install_script" --channel 10.0 --install-dir "$DOTNET_ROOT"
    rm -f "$install_script"
    echo "[bootstrap] .NET installed: $("$DOTNET_ROOT/dotnet" --version 2>/dev/null || echo '?')"
fi

# --- Python workspace (BOOT-02 / D-09) -------------------------------------
# Resolve the uv workspace from the repo root. Idempotent and non-fatal: a transient failure
# here must not break session startup (the golden/verify gates surface real breakage instead).
if command -v uv >/dev/null 2>&1; then
    ( cd "$REPO_ROOT" && uv sync >/dev/null 2>&1 ) || true
fi

exit 0
