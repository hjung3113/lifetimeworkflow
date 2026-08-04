# Phase 51 baseline evidence

## Reproducibility

Harness `723b32d960c835e81ec887ac84dcf7e070d47243`; target baseline `1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a`; target worktree `/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline`; cwd `/Users/hyojung/Desktop/2026/lifetimeworkflow`. Live versions are in `evidence/metadata/tool-versions.json`; literal argv/cwd/stdout/stderr/exit captures are under `evidence/`. Nonzero/blocked outcomes are evidence. The proof compares status, HEAD, tracked-index digest, and untracked path-set digest only; untracked content and expected `.git/worktrees/` administrative metadata are excluded.

## Isolation and external drift

`comparison.json`: `status_equal: true`, `head_equal: false`, `index_equal: false`, `untracked_set_equal: true`. The untracked-set equality compares two empty-string SHA-256 digests and therefore has low discriminating power. The false HEAD/index values are documented third-party develop drift in `evidence/isolation/external-drift.json`, not an OBS-D adoption defect; no Phase-51 adoption command targeted or mutated the original checkout.

The narrowed inline-plan secret scan misses `sk-proj-...` and `sk-ant-api03-...` forms because its key character class dropped dashes. This bounded gap is recorded only: the pattern lives in Phase-51 plan-inline checks, not a shipped gate, and is not changed here.

## Observation summary

| ID | Observation |
| --- | --- |
| OBS-D-01 | Extra non-workspace manifest is enumerated. |
| OBS-D-02 | Required workspace edges are present. |
| OBS-D-03 | JavaScript conventions lack commands. |
| OBS-D-04 | Apply leaves unlisted lock files. |

## Observations

### OBS-D-01
- **symptom:** All five required manifests are present, plus `docs/design-prototype/package.json`.
- **reproduction:** `uv run python -m tools.adoption_scan --target /Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline --out .planning/phases/51-real-target-observation-baseline/evidence/discover`; cwd `/Users/hyojung/Desktop/2026/lifetimeworkflow`; target `1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a`; harness `723b32d960c835e81ec887ac84dcf7e070d47243`; exit `0`.
- **code location:** `tools/adoption_scan/detect.py:46`.
- **purpose tag:** ② PROPOSAL ONLY.
- **proposed disposition:** repair-in-52.

### OBS-D-02
- **symptom:** Frontend/backend runtime edges to `@fops/shared` are present; no version-string defect occurs.
- **reproduction:** `uv run python -c "import json; from pathlib import Path; from tools.memory_regen.package_facts import build_facts; target=Path('/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline'); print(json.dumps({'repo_root':str(target), **build_facts(repo_root=target)}, indent=2, sort_keys=True))"`; cwd `/Users/hyojung/Desktop/2026/lifetimeworkflow`; target `1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a`; harness `723b32d960c835e81ec887ac84dcf7e070d47243`; exit `0`.
- **code location:** `tools/adoption_scan/detect.py:273`; `tools/memory_regen/package_facts.py:216`.
- **purpose tag:** ② PROPOSAL ONLY.
- **proposed disposition:** no-change-evidence-backed.

### OBS-D-03
- **symptom:** JavaScript convention `test`, `format`, and `bash_scope` are all `null`, and the convention result has no `lint` key at all despite Phase 52's lint-and-test requirement.
- **reproduction:** `uv run python -c "import json; from pathlib import Path; from tools.memory_regen.package_facts import build_facts; from tools.harness_config.loader import conventions_for, load_project; target=Path('/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline'); facts=build_facts(repo_root=target); config_path=target/'harness'/'project.toml'; cfg=load_project(config_path) if config_path.exists() else load_project(); print(json.dumps({'repo_root':str(target), 'config_source':str(config_path) if config_path.exists() else 'harness/project.toml', 'packages':[{'package':pkg['id'], 'dir':pkg['dir'], 'conventions':conventions_for(pkg['dir'], cfg=cfg, facts=facts)} for pkg in facts['packages']]}, indent=2, sort_keys=True))"`; cwd `/Users/hyojung/Desktop/2026/lifetimeworkflow`; target `1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a`; harness `723b32d960c835e81ec887ac84dcf7e070d47243`; exit `0`.
- **code location:** `harness/project.toml:26`; `tools/harness_config/loader.py:297`.
- **purpose tag:** ① PROPOSAL ONLY.
- **proposed disposition:** repair-in-52.

### OBS-D-04
- **symptom:** Apply exit `0` creates unlisted `.AGENTS.md.lock`, `.CLAUDE.md.lock`, and `.claude/.settings.json.lock`; `matches` is false.
- **reproduction:** `uv run python -m tools.adoption_apply apply --task-dir .planning/phases/51-real-target-observation-baseline/evidence/draft --batch-id a11c2d595d674f9b --target /Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline`; cwd `/Users/hyojung/Desktop/2026/lifetimeworkflow`; target `1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a`; harness `723b32d960c835e81ec887ac84dcf7e070d47243`; exit `0`.
- **code location:** `tools/adoption_apply/apply.py:306`; `tools/adoption_apply/tests/test_atomic_apply.py:267`.
- **purpose tag:** ④ PROPOSAL ONLY.
- **proposed disposition:** repair-in-52.

## OBS-03 verdict

**Refuted (PASS).** Literal deciding output:

> `{"from": "@fops/backend", "kind": "runtime", "to": "@fops/shared"}`
>
> `{"from": "@fops/frontend", "kind": "runtime", "to": "@fops/shared"}`
>
> `"result": "refuted"`

The evidence is from `evidence/downstream/workspace-edge-comparison.json`, with `tools/adoption_scan/detect.py:273` and `tools/memory_regen/package_facts.py:216` implicated.

## Pre-disposal status

The record is complete; the detached worktree will be discarded only after the human disposal checkpoint.

## Disposal result

`git -C /Users/hyojung/Desktop/2026/FeedbackOps worktree remove --force /Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline` exited `0` (see `evidence/disposal/`). The final worktree list contains no Phase-51 worktree. Post-disposal comparison remains honest: status/untracked set are equal; HEAD/index remain unequal solely due to documented external develop drift.
