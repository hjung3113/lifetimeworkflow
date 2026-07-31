# Isolation evidence — Phase 52 Plan 05

`git worktree add --detach <path> <sha>` mutates the ORIGINAL repository's own
`.git/worktrees/**` administrative metadata (a new subdirectory registering the
linked worktree, its `HEAD`, `gitdir`, `commondir`, and `locked`/`prunable` state
files). This is expected and out of scope for the working-tree proof captured
here — the same disclosure Phase 51 made (`51-BASELINE-EVIDENCE.md` §Reproducibility).

The before/after proof in this directory deliberately covers only:
- `git status --porcelain=v2 --untracked-files=all` (working-tree content state)
- `rev-parse HEAD` + a SHA-256 digest of `git ls-files -s` (tracked-index state)
- a SHA-256 digest of the sorted untracked path set (untracked path presence, not content)

It does **not** cover `.git/worktrees/**` (administrative metadata, not working-tree
content) or the contents of untracked files (only their path set).
