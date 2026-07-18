# Adversarial Multi-Expert Review — Implementation Design

## Product brief

### Problem
High-risk work can pass a single reviewer because one perspective misses product misalignment, architectural coupling, weak evidence, migration hazards, or blast radius. All-to-all debate is expensive and amplifies correlated opinions.

### Goal
Provide an evidence-grounded review gate that runs independent role reviews, challenges only important findings, adjudicates conflicts, and produces case-specific reinforcement guidance without implementing the target.

### Success criteria
- Select 3–6 independent experts based on the review case.
- Give every critical/high finding evidence, a falsification condition, and one adversarial challenge.
- Classify final findings as accepted, narrowed, rejected, or deferred.
- Never modify the reviewed source.
- Keep review artifacts separate from durable ADR/CONTEXT knowledge.

### Non-goals
- Replacing normal Standards/Spec code review.
- Diagnosing bugs without a red-capable reproduction loop.
- Blocking delivery based on reviewer vote count.
- Running all-to-all reviewer debates.

## Eligibility decision

The workflow runs when explicitly requested, or when the orchestrator records high/critical risk for C3/C4 work, cross-cutting changes, auth/security/data/API changes, difficult-to-reverse decisions, or material operational/user impact. Otherwise the router selects a narrower flow.

## Workflow

1. Review charter and observed Evidence Pack.
2. Independent first-pass expert reviews.
3. Finding normalization and duplicate grouping.
4. Finding-centric challenge for critical/high and disputed medium findings.
5. Conflict adjudication only where findings materially disagree.
6. Independent synthesis with explicit dispositions.
7. Validation and progress update.

## Expert matrix

| Case | Required experts |
|---|---|
| Design | Alignment, Architecture, Verification, Impact |
| Code/document | Alignment, Architecture, Verification |
| Debug | Diagnosis, Verification, Impact, Architecture |
| Refactor | Migration, Architecture, Verification, Impact |
| API/data | Alignment, Architecture, Verification, Impact |

The coordinator may add at most two experts. Different models are recommended but not required; isolation and role-specific prompts are the primary independence mechanisms.

## Finding contract

Each finding contains Claim, Severity, Confidence, Evidence, Affected area, Failure scenario, Recommended action, Falsification condition, and Disposition. Vote count is never evidence.

## Challenge contract

Each challenged finding receives Verdict (`uphold`, `narrow`, `reject`, `needs-evidence`), strongest counterargument, checked evidence, hidden assumption, severity correction, and required revision.

## Storage and continuity

Artifacts live under `.workflow/reviews/<review-id>/`. The orchestrator records only review status, FINAL.md, accepted high-level decisions, residual risk, and next action in `.workflow/PROGRESS.md`. Durable knowledge promotion remains a separate decision.

## Permissions

Experts are hidden subagents, read-only against source, and can write only under `.workflow/reviews/**`. The coordinator can invoke only the explicit expert allowlist. Web access is denied; external research must be produced by the research flow first.

## Verification plan

- Parse every agent and command frontmatter.
- Assert default-deny and source-write denial.
- Assert hidden experts have no public commands.
- Assert coordinator expert allowlist.
- Fixture-test workspace init/status/validation.
- Fixture-test helper scripts from nested directories.
- Verify Rust `tests/` does not imply pytest.
- Verify installer removes stale managed files using a manifest.
