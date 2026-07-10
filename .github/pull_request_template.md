<!--
Contract-first PR checklist. "Machines gate, humans ratify" — CI (.github/workflows/ci.yml) runs
the drift / golden / contract-check gates automatically; this checklist is your self-review BEFORE
opening the PR so a red gate is never a surprise. Constitution-plane changes (contracts / ADRs /
goldens) are CODEOWNERS-gated — see .github/CODEOWNERS.
-->

## Summary

<!-- What does this PR change, and why? One or two sentences. -->

## Contract-first checklist

### Breaking change
- [ ] This PR does **not** change any `contracts/**/*.schema.json` in a breaking way (removed or
      renamed required field, narrowed `const`/`enum`, tightened type).
- [ ] If it **is** a breaking contract change, the paired ADR is linked here: <!-- docs/adr/NNNN-*.md -->

### Golden / approval update
- [ ] No `golden/` or `examples/*/golden/` baselines changed.
- [ ] If baselines **did** change, the regeneration is **intentional** and human-approved
      (CODEOWNERS review on the constitution plane), not an accidental overwrite.

### Contract drift
- [ ] I ran the root drift gate — `uv run python -m tools.contract_drift.drift` — and it is green.
- [ ] I ran the example drift gate —
      `uv run python -m tools.contract_drift.drift --contracts-dir examples/log-parser/contracts --baseline examples/log-parser/contracts/.hashes/manifest.json`
      — and it is green.
- [ ] Any intentional schema-hash move is paired with a golden update **and** an ADR (never a silent rebaseline).

## Notes

<!-- Anything reviewers should know: risk areas, follow-ups, out-of-scope items. -->
