# Phase 1 — .NET Resume Checklist

**Why this exists:** Phase 1 is fully built and Python-verified (34 pass / 2 skip, ruff clean, drift gate PASS). The ONLY outstanding work is 3 verifications that require the .NET 10 SDK, which this container's egress policy hard-blocks (403 CONNECT on all Microsoft/.NET/NuGet hosts). No code changes are needed — only a reachable .NET SDK.

## 1. Fix the network policy (user action — cannot be done from inside the container)

The environment's network policy is chosen when the environment is created (claude.ai/code → environment settings). Docs: https://code.claude.com/docs/en/claude-code-on-the-web

Allow (or switch to a policy that permits) these hosts:

```
dot.net
aka.ms
builds.dotnet.microsoft.com
dotnetcli.azureedge.net
dotnetcli.blob.core.windows.net
packages.microsoft.com
api.nuget.org
*.nuget.org
```

(The first four are needed for `dotnet-install.sh`; `packages.microsoft.com` + nuget hosts are needed for later .NET package restores in Phases 4–6.)

Then start a **fresh session** on the updated environment (the policy change does not apply to this already-running container).

## 2. Resume — one sequence closes Phase 1

The SessionStart hook auto-installs .NET 10 on the fresh session (self-healing bootstrap). Then:

```bash
# a) confirm bootstrap self-healed
bash tools/bootstrap/verify.sh                 # BOOT-01: asserts dotnet 10 + uv resolve

# b) .NET normalization parity (CONTRACT-02 .NET half)
dotnet test libs/dotnet/Normalize.Tests        # must match the shared (raw,canonical) corpus

# c) walking-skeleton end-to-end golden demo (CONTRACT-03)
uv run pytest                                  # the 2 currently-skipped tests now RUN:
                                               #   test_repr_only.py  → PASS (repr-only diff normalized away)
                                               #   test_value_regression.py → FAIL-as-expected (real regression caught)
```

Expected after (a)–(c): full green, zero code changes. Then:

```bash
# d) mark BOOT-01/02/03 complete + close phase
#    (update REQUIREMENTS traceability BOOT-* → Complete, then)
/gsd:verify-work 1          # or /gsd:plan-phase 2 to continue the chain
```

## 3. State at pause (commit-accurate)

- **Complete + verified (Python):** CONTRACT-01, CONTRACT-02 (py), CONTRACT-03 (approve-gate + recorded-diff), CONTRACT-04 (drift gate, P14 proven), DOCS-01, DOCS-02, BOOT-02, BOOT-03.
- **Authored, verification deferred to .NET:** BOOT-01 runtime install; CONTRACT-02 .NET parity (`dotnet test`); CONTRACT-03 end-to-end golden demo (`dotnet build/run`, 2 skipped tests).
- **Repo tree built:** `contracts/ golden/ libs/{python,dotnet}/ tools/{bootstrap,contract_hash,contract_drift,golden_runner}/ components/toy-converter/ docs/{tutorials,how-to,reference,explanation,adr}/`.

*Branch: `claude/data-pipeline-harness-8aypct` — all work committed + pushed.*
