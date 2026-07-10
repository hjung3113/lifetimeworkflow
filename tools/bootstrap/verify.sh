#!/usr/bin/env bash
# Green-gate for the bootstrap toolchain (BOOT-01/02).
# Asserts: (1) a .NET 10 SDK is installed and (2) the uv workspace resolves from the lockfile.
# Exits 0 on success, non-zero with a clear message on failure. Takes no arguments.
set -uo pipefail

DOTNET_ROOT="${DOTNET_ROOT:-$HOME/.dotnet}"
export PATH="$DOTNET_ROOT:$PATH"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

fail() { echo "[verify] FAIL: $1" >&2; exit 1; }

# --- .NET 10 (BOOT-01) ---
[ -x "$DOTNET_ROOT/dotnet" ] || fail ".NET SDK not found at $DOTNET_ROOT/dotnet (run tools/bootstrap/install.sh)"
dotnet_ver="$("$DOTNET_ROOT/dotnet" --version 2>/dev/null || true)"
case "$dotnet_ver" in
    10.*) : ;;
    *) fail "dotnet --version reported '$dotnet_ver', expected 10.x" ;;
esac

# --- uv workspace (BOOT-02) ---
# --all-packages so every member's pinned deps (memory_regen's tree-sitter/networkx, etc.) are
# asserted present, not just the virtual root's — a bare frozen sync would prune them.
command -v uv >/dev/null 2>&1 || fail "uv not found on PATH"
( cd "$REPO_ROOT" && uv sync --frozen --all-packages >/dev/null 2>&1 ) || fail "uv sync --frozen failed (lockfile inconsistent?)"

echo "[verify] OK: .NET $dotnet_ver + uv workspace resolved"
exit 0
