# DERIVED — do not hand-edit (tools/memory_regen/package_facts.py)

Every package in this checkout with its manifest path, language and package id, plus intra-repo dependency edges parsed from the manifests themselves.

## Packages

| id | manifest | dir | language |
| --- | --- | --- | --- |
| .claude | .claude/package.json | .claude | javascript |
| ToyConverter | examples/log-parser/components/toy-converter/ToyConverter.csproj | examples/log-parser/components/toy-converter | csharp |
| logparser-golden-runner | examples/log-parser/golden_runner/pyproject.toml | examples/log-parser/golden_runner | python |
| Normalize.Tests | examples/log-parser/libs/dotnet/Normalize.Tests/Normalize.Tests.csproj | examples/log-parser/libs/dotnet/Normalize.Tests | csharp |
| Normalize | examples/log-parser/libs/dotnet/Normalize/Normalize.csproj | examples/log-parser/libs/dotnet/Normalize | csharp |
| logparser-normalize | libs/python/pyproject.toml | libs/python | python |
| logparser-harness | pyproject.toml | . | python |
| logparser-adoption-apply | tools/adoption_apply/pyproject.toml | tools/adoption_apply | python |
| logparser-adoption-scan | tools/adoption_scan/pyproject.toml | tools/adoption_scan | python |
| logparser-agree | tools/agree/pyproject.toml | tools/agree | python |
| logparser-contract-drift | tools/contract_drift/pyproject.toml | tools/contract_drift | python |
| logparser-contract-graph | tools/contract_graph/pyproject.toml | tools/contract_graph | python |
| logparser-contract-hash | tools/contract_hash/pyproject.toml | tools/contract_hash | python |
| logparser-docs-sync | tools/docs_sync/pyproject.toml | tools/docs_sync | python |
| logparser-harness-config | tools/harness_config/pyproject.toml | tools/harness_config | python |
| logparser-harness-emit | tools/harness_emit/pyproject.toml | tools/harness_emit | python |
| logparser-harness-lint | tools/harness_lint/pyproject.toml | tools/harness_lint | python |
| logparser-harness-perms | tools/harness_perms/pyproject.toml | tools/harness_perms | python |
| logparser-hooks | tools/hooks/pyproject.toml | tools/hooks | python |
| logparser-memory-regen | tools/memory_regen/pyproject.toml | tools/memory_regen | python |
| logparser-polyglot-lint | tools/polyglot_lint/pyproject.toml | tools/polyglot_lint | python |
| logparser-ruff-baseline | tools/ruff_baseline/pyproject.toml | tools/ruff_baseline | python |
| logparser-workspace-config | tools/workspace_config/pyproject.toml | tools/workspace_config | python |

## Dependency Edges

| from | to | kind |
| --- | --- | --- |
| Normalize.Tests | Normalize | runtime |
| ToyConverter | Normalize | runtime |

## Convention Profiles

| package | dir | language | test | format | bash_scope | agents_md | default |
| --- | --- | --- | --- | --- | --- | --- | --- |
| .claude | .claude | javascript | (none) | (none) | (none) | AGENTS.md | false |
| Normalize | examples/log-parser/libs/dotnet/Normalize | csharp | (none) | (none) | (none) | examples/log-parser/libs/dotnet/AGENTS.md | false |
| Normalize.Tests | examples/log-parser/libs/dotnet/Normalize.Tests | csharp | (none) | (none) | (none) | examples/log-parser/libs/dotnet/AGENTS.md | false |
| ToyConverter | examples/log-parser/components/toy-converter | csharp | (none) | (none) | (none) | examples/log-parser/AGENTS.md | false |
| logparser-adoption-apply | tools/adoption_apply | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-adoption-scan | tools/adoption_scan | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-agree | tools/agree | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-contract-drift | tools/contract_drift | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-contract-graph | tools/contract_graph | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-contract-hash | tools/contract_hash | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-docs-sync | tools/docs_sync | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-golden-runner | examples/log-parser/golden_runner | python | uv run pytest | ruff format | uv * | examples/log-parser/AGENTS.md | false |
| logparser-harness | . | python | uv run pytest | ruff format | uv * | AGENTS.md | true |
| logparser-harness-config | tools/harness_config | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-harness-emit | tools/harness_emit | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-harness-lint | tools/harness_lint | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-harness-perms | tools/harness_perms | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-hooks | tools/hooks | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-memory-regen | tools/memory_regen | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-normalize | libs/python | python | uv run pytest | ruff format | uv * | libs/python/AGENTS.md | false |
| logparser-polyglot-lint | tools/polyglot_lint | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-ruff-baseline | tools/ruff_baseline | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
| logparser-workspace-config | tools/workspace_config | python | uv run pytest | ruff format | uv * | AGENTS.md | false |
