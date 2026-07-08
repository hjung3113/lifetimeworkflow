#!/usr/bin/env bash
# Contract-drift gate CLI (CONTRACT-04, D-07).
# Recompute the live JCS SHA-256 manifest, compare it to the committed baseline
# (contracts/.hashes/manifest.json), and exit non-zero — listing drifted files + their
# breaking/non-breaking classification — on any unapproved schema change (incl. §4-5 conventions,
# PITFALLS P14). Exits 0 when the live tree matches the baseline.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

exec uv run python -m tools.contract_drift.drift "$@"
