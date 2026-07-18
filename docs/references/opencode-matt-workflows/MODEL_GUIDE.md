# Per-agent model configuration

OpenCode accepts `model: provider/model-id` in agent and command frontmatter. When an agent has no `model` entry, a subagent inherits the invoking primary agent's model.

This bundle intentionally ships without hard-coded provider IDs. Copy `models.example.json`, fill only the tiers you use, and apply it:

```bash
cp models.example.json models.local.json
# Edit models.local.json
python3 configure-models.py models.local.json /path/to/project
```

Recommended capability tiers:

| Tier | Agents | Selection goal |
|---|---|---|
| `router` | `flow-router` | Fast, low-cost classification with reliable tool calling |
| `planning` | setup, feature, Wayfinder, architecture, triage, research-plan | Strong reasoning and long-context discipline |
| `coding` | small-change, ticket, bugfix, conflicts | Strong repository coding, tests, and debugging |
| `review` | review coordinator and hidden axis reviewers | Precise diff reading and instruction following |
| `research` | `flow-research` | Strong source evaluation and citation discipline |
| `prototype` | `flow-prototype` | Fast coding and UI/state exploration |

Use `agent_overrides` for exceptional agents. `command_overrides` is supported, but agent-level model selection is preferred so direct `@agent` invocation and slash commands behave consistently.
