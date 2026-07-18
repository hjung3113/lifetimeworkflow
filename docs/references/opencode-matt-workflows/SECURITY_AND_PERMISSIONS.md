# Security and permission design

All workflow agents begin with `permission: "*": deny` and opt into only the tools they need.

Key boundaries:

- `flow-router` can read/search a bounded amount and invoke an explicit allowlist of workflow agents. It cannot edit, run shell commands, load skills, access the web, or call itself.
- Review agents are read-only. Standards and Spec reviews run in separate hidden subagents.
- Research can access the web but can write only under `docs/research/**` or `.scratch/research/**`.
- Prototype writes are automatically allowed only under `.scratch/prototypes/**`; edits elsewhere require approval.
- Architecture scanning cannot edit production code.
- Implementing agents can edit the worktree and run common test/typecheck/lint commands. `git push`, `git reset --hard`, `git clean`, destructive recursive deletion, privilege escalation, PR merge, and repository deletion are explicitly denied.
- External-directory access is denied for every agent.

`ask` is an interaction boundary, not a security boundary when OpenCode runs with `--auto`. Destructive operations therefore use explicit `deny` rules.

## Custom tracker and MCP permissions

The default bundle does not guess MCP tool names. If a repository uses Linear, Jira, GitLab MCP, or another custom tracker instead of local files or `gh`, add only that connector's exact read/write tools to the agents that need them—typically setup, feature, ticket, triage, Wayfinder, and architecture planning.

Example pattern:

```yaml
permission:
  "linear_get_*": allow
  "linear_search_*": allow
  "linear_create_issue": ask
  "linear_update_issue": ask
```

Keep the global `"*": deny` rule first. Avoid broad patterns such as `linear_*: allow` when the connector includes destructive operations.

## Sensitive files

All agents deny reads of common local secret files such as `.env`, `.env.local`, nested `.env`, and environment-specific local variants. Agents with write access also deny edits under `.git/**`, `.opencode/**`, and those secret-file patterns.
