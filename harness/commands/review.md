---
description: >-
  Use when a change is written and you want an adversarial read-only review — surfaces the working
  diff, then routes to the code-reviewer persona for severity-classified
  findings. Invoke before /verify-work or a commit, so review is an executable step, not a wish.
agent: code-reviewer
subtask: true
---

# /review — diff → read-only reviewer → classified findings

Makes the review stage executable. The `code-reviewer` persona is **read-only** in both runtime
representations (no Write/Bash/Edit); this command feeds it the diff and returns findings the scoped
engineer then fixes. The reviewer never edits — it reports.

## 1. Surface the change under review

The working diff (staged + unstaged) against HEAD, plus a name-only summary:

!`git --no-pager diff --stat HEAD; echo '---'; git --no-pager diff HEAD`

## 2. Route to the code-reviewer

Hand the diff above to the **code-reviewer** persona (read-only, adversarial). Ask for findings
**classified by severity** (blocker / major / minor / nit), each with file:line and a concrete fix
suggestion. Scope the review to:

- **Correctness** — logic, edge cases, the §4.3–4.6 boundary invariants (see `polyglot-boundary`).
- **Contract-first** — does code disagree with a `contracts/` schema? The code is wrong, not the
  contract.
- **Least privilege / gates** — any new broad permission, any attempt to write the constitution
  plane or self-bless a golden.
- **Simplicity / reuse** — re-implementation of an existing `tools/` capability (forbidden).

## 3. Return findings to the scoped engineer

The reviewer returns the classified list; the **scoped engineer** (python-engineer or an
instance-declared engineer) applies the fixes. Re-run `/review` until no blocker/major remains, then
`/verify-work`. The reviewer does not commit and does not fix — separation of duties is the point.
