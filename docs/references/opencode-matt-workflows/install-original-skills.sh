#!/usr/bin/env bash
set -euo pipefail
TARGET="${1:-.}"; (cd "$TARGET" && npx skills@latest add mattpocock/skills)
python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/doctor.py" "$TARGET"
