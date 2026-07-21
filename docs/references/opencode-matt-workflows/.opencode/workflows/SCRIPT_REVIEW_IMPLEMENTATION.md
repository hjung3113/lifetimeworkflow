# Helper Script Review and Remediation

## Changes implemented

### `repo-context.sh`
- Resolves and operates from the Git repository root, even when invoked from a nested directory.
- Supports routing, implementation, and review modes.
- Supports JSON output with a versioned schema, bounded evidence budget, focus candidates, and review file lists.

### `workflow-preflight.sh`
- Resolves the repository root.
- Supports explicit `--skills`, workflow-specific `--require`, and JSON output.
- Preserves positional skill arguments for compatibility.

### `detect-checks.sh`
- Removed the unsafe rule that treated any `tests/` directory as evidence for pytest.
- Emits command, evidence, scope, and confidence.
- Uses repository manifests and actual package scripts as evidence.

### `configure-models.py`
- Added `--dry-run` and optional backups.
- Fails on unknown agent or command names instead of silently ignoring typos.

### Installation
- Uses an install manifest with hashes.
- Removes stale files previously managed by the bundle.
- Backs up changed or user-modified managed files under a timestamped backup directory.

### Validation
- `verify-bundle.py` validates definitions and bundle contracts.
- `doctor.py` diagnoses an installed project separately.
- `verify.py` remains as a compatibility wrapper.

## Remaining limits
- OpenCode runtime resolution still requires `opencode debug config` in an environment with the CLI installed.
- Check detection intentionally provides candidates, not authoritative project commands.
- PyYAML is required by `verify-bundle.py`; normal workflow runtime scripts use only the Python standard library.
