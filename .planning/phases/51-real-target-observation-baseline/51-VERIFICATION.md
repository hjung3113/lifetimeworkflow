---
phase: 51-real-target-observation-baseline
verified: 2026-07-31T18:40:00Z
status: passed
score: 4/4 success criteria verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  repair_commit: c0d256882ee14a3a9d275e53ff577ed6103f0871
  gaps_closed:
    - "Fabricated harness SHA `723b32d6bd4d87c68a84ad8772a7ee3d1c282d0e` removed from all five citations; the record now cites only `723b32d960c835e81ec887ac84dcf7e070d47243`, which resolves as a commit in this repo."
    - "OBS-D-04 code location re-pointed from `apply.py:246` (`_atomic_replace`) to `apply.py:306` (`_apply_marker_merge`), which is the line that actually creates the `.lock` sidecars."
    - "OBS-D-02 and OBS-D-03 `reproduction` fields now carry literal argv, byte-identical to `evidence/downstream/*.argv.txt`."
    - "OBS-D-03 symptom extended to state the missing `lint` key, without renumbering and without minting a new OBS-D id."
    - "`external-drift.json.drifting_commits` completed from 2 to all 6 commits in `1d1c8ed..4f16525`; every hash/date/subject matches the target repo's real history."
    - "Two disclosure notes added: `untracked_set_equal: true` compares two empty-string digests (low discriminating power); the narrowed secret-scan pattern misses `sk-proj-…` / `sk-ant-api03-…`."
  gaps_remaining: []
  regressions: []
deferred: []
---

# Phase 51: Real-Target Observation Baseline — Verification Report

**Phase Goal:** The current harness's behavior on the isolated FeedbackOps worktree is known from
reproducible evidence before any repair is designed.
**Verified:** 2026-07-31T18:40:00Z (re-verification), 2026-07-31T15:05:00Z (initial)
**Status:** passed (4/4 success criteria verified)
**Re-verification:** Yes — SC-2 only, after repair commit `c0d2568`. SC-1, SC-3 and SC-4 were
VERIFIED in the initial pass and were re-checked only for regression.

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Baseline discover → draft → apply runs against the isolated worktree only; before/after proof over the original `develop` checkout; leftovers discarded | VERIFIED (with recorded external drift) | Independently reproduced — see below |
| 2 | Every observed defect has symptom + reproducible path + implicated code location | VERIFIED (repaired in `c0d2568`) | Every cited SHA resolves; OBS-D-04 code location now implicates the observed behavior; all four `reproduction` fields carry literal argv |
| 3 | pnpm `workspace:*` hypothesis has a reproducible verdict | VERIFIED | Non-vacuous refutation grounded in raw captured output |
| 4 | No repair design or implementation precedes the completed baseline record | VERIFIED (re-confirmed post-repair) | Zero-byte diff across `tools/ harness/ contracts/ docs/adr/`; every changed path inside the phase directory |

**Score:** 4/4

---

## SC-1 — Baseline run + isolation

**Verdict: VERIFIED.** The isolation claim survives adversarial testing; the drift record is honest.

**The run targeted only the worktree.** Every captured argv names
`/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline`, never
`~/Desktop/2026/FeedbackOps`:

| Stage | argv target | exit |
|---|---|---|
| discover | `-m tools.adoption_scan --target …/v27-51-baseline --out …/evidence/discover` | 0 |
| draft | `-m tools.adoption_apply draft --task-dir …/evidence/draft --target …/v27-51-baseline` | 0 |
| apply | `-m tools.adoption_apply apply --task-dir …/evidence/draft --batch-id a11c2d595d674f9b --target …/v27-51-baseline` | 0 (`applied=154 skipped=86 refused=23`) |

**The comparison booleans are reported honestly, not flipped.** `evidence/isolation/comparison.json`
states `status_equal: true`, `head_equal: false`, `index_equal: false`, `untracked_set_equal: true`,
and `51-BASELINE-EVIDENCE.md` line 9 restates those four values verbatim. Nothing was rounded up to
"unchanged".

**The drift is genuinely third-party — independently proven, not merely asserted.** I did not accept
the attribution string. I reconstructed both index digests from the target's commit trees alone:

```
git ls-tree -r 1d1c8ed | awk -F'\t' '{split($1,a," "); print a[1]" "a[3]" 0\t"$2}' | shasum -a 256
  → a7a889623286fd50b6fdc071bb7750a798f2ff6688d60288bbca3b534b2b2d48   == before.index.sha256
git ls-tree -r 4f16525 | (same) | shasum -a 256
  → efb77c8f965bb285eb76357ba88e3bdff4f61e2056cfc48e568172cd70febd43   == after.index.sha256
```

Both recorded digests are byte-identical to digests derivable from the two commit trees with no
other input. Therefore **100% of the index delta is accounted for by the commit movement
`1d1c8ed → 4f16525`, and none of it by any Phase-51 write.** `git status --porcelain` is empty in
both `before.status.txt` and `after.status.txt`, so the working tree was never dirtied either. The
six intervening commits (`2a13c79`, `86e7673`, `6fae48f`, `59688d2`, `a8823f8`, `4f16525`) are PR
merges for AC-ID doc exemptions, a clean-state probe, and a `request_task` feature — all unrelated
to adoption.

**Not laundered into an OBS-D defect.** `comparison.json` and the evidence record both state the
inequality is documented external drift and explicitly *not* an OBS-D adoption defect; no OBS-D id
was minted for it, and no OBS-D id was suppressed because of it. **Re-confirmed after the repair:**
`external-drift.json.attribution` is unchanged and still reads "…observed inequality is documented
third-party external drift, not an OBS-D adoption defect," and the id set is still `OBS-D-01..04`.

**Disposal verified independently, not from the record.** `git -C ~/Desktop/2026/FeedbackOps
worktree list` now shows only the primary checkout; `/Users/hyojung/Desktop/2026/FeedbackOps-worktrees/v27-51-baseline`
does not exist on disk. Phase 52 will necessarily start from a fresh worktree.

**Caveats after repair:**
- The literal ROADMAP wording "the original `develop` checkout is byte-unchanged" is **not**
  literally satisfied (HEAD and index moved). It is satisfied in substance — no Phase-51 command
  caused any of it — and the deviation was human-directed. Still recommended (non-blocking):
  record this formally as a verification override so the wording mismatch is explicit rather than
  implicit.
- The two remaining WARNINGs from the initial pass are now **disclosed in the record itself**
  (see SC-2 item 6 below), which is the correct disposition for a phase whose deliverable is an
  observation record — the limitation is documented rather than silently carried.
- `external-drift.json.drifting_commits` is now complete at 6/6 (was 2/6). Entries carry
  `hash` / `author_date` / `subject`; none carries an `author` field, but neither did the two
  pre-existing entries, so this is the record's own consistent schema, not a regression.

---

## SC-2 — OBS-01 defect records

**Verdict: VERIFIED.** The initial pass found the structure sound but three mandated fields
factually wrong or elided. Commit `c0d2568` ("docs(51): repair verification evidence gaps",
2 files, +15/−9) corrects all of them. Each claimed fix was re-checked by execution, not by reading
the claim.

### 1. Fabricated harness SHA — CLOSED

I enumerated **every** 40-hex string in the record rather than only the five the author listed:

```
grep -oE '\b[0-9a-f]{40}\b' 51-BASELINE-EVIDENCE.md | sort -u
  → 1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a
  → 723b32d960c835e81ec887ac84dcf7e070d47243
```

Only two distinct object ids remain, each resolved against the correct repository:

| SHA | Repo checked | `git cat-file -t` |
|---|---|---|
| `723b32d960c835e81ec887ac84dcf7e070d47243` | `lifetimeworkflow` | `commit` ✓ |
| `1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a` | `~/Desktop/2026/FeedbackOps` | `commit` ✓ |

Cross-checks confirm the ids are not merely plausible: `723b32d9…` does **not** exist in FeedbackOps
and `1d1c8eda…` does **not** exist in lifetimeworkflow, so each is cited against the right repo.
The fabricated `723b32d6bd4d87c68a84ad8772a7ee3d1c282d0e` resolves in **neither** repo and no longer
appears anywhere in the record. `git diff a0de4e8 HEAD` confirms exactly five replacements: header
line 5 plus the `reproduction` field of OBS-D-01..04.

**Short-hash sweep (not covered by the previous pass):**
`grep -oE '\b[0-9a-f]{7,12}\b'` over the record returns **zero** matches — the record cites no
abbreviated hashes in prose at all, so there is no uncovered surface here. The one 16-hex-looking
token, `a11c2d595d674f9b` in OBS-D-04's argv, is the apply `--batch-id`, not a git object; it
correctly fails `cat-file` in both repos and is not a citation.

### 2. OBS-D-04 code location — CLOSED, and the symptom matches the code

The record now cites `tools/adoption_apply/apply.py:306` plus
`tools/adoption_apply/tests/test_atomic_apply.py:267`. Both resolve, and — the point the previous
pass insists on — the code at that line actually produces the recorded symptom:

```
apply.py:292  def _apply_marker_merge(destination: str, target_path: Path, block_body: str = "") -> None:
apply.py:306      lock_path = target_path.with_name(f".{target_path.name}.lock")
apply.py:307      lock_path.parent.mkdir(parents=True, exist_ok=True)
apply.py:308      with lock_path.open("a+b") as lock:
apply.py:309          fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
```

Symptom-to-code match, checked in both directions:
- The symptom names `.AGENTS.md.lock`, `.CLAUDE.md.lock`, `.claude/.settings.json.lock`. Line 306's
  f-string `f".{target_path.name}.lock"` generates exactly that naming shape, and the function's
  own docstring (296–303) names `AGENTS.md`/`CLAUDE.md` as the marker-capable destinations while
  line 310 branches on `.json` — covering `.claude/.settings.json`. All three observed artifacts are
  reachable from this one site.
- The symptom says the files are **left behind**. `grep -n 'unlink' apply.py` returns only lines 233
  and 264, both `os.unlink(temporary)` inside `_atomic_replace`. Nothing ever unlinks `lock_path`,
  so persistence is a property of this code, not an assumption.
- The secondary reference `test_atomic_apply.py:267` lands inside the comment block (265–269)
  documenting that the `.lock` sidecar "is created by `lock_path.open(\"a+b\")` alone" — corroborating,
  not padding.

The wrong `apply.py:246` (`_atomic_replace`, which creates `.tmp` and unlinks it) was dropped rather
than retained. That is acceptable: the initial pass offered retention as optional, and keeping a
citation that cannot produce the symptom would re-create the original defect.

### 3. Elided reproduction fields — CLOSED

I compared each inlined `reproduction` command against the corresponding capture programmatically
(exact string equality, not eyeball):

| Record section | Capture file | Result |
|---|---|---|
| OBS-D-02 | `evidence/downstream/package-facts.argv.txt` | **byte-identical** |
| OBS-D-03 | `evidence/downstream/conventions.argv.txt` | **byte-identical** |

The argv are not paraphrases of the captures — they are the captures. OBS-D-01 and OBS-D-04 were
never elided and remain literal.

**The one surviving `...`:** exactly one ellipsis remains in the record, at line 11:

> "The narrowed inline-plan secret scan misses `sk-proj-...` and `sk-ant-api03-...` forms…"

This is **benign prose, not a defect.** It is inside the new disclosure note, not inside any
`reproduction` field, and the ellipsis stands for the arbitrary key body of an API-key *form* — the
thing being described is a pattern class, so there is no literal value that could be inlined. No
`reproduction` field in the record contains an ellipsis.

### 4. OBS-D-03 lint scope — CLOSED, no renumbering

The symptom was extended in place:

> before: "JavaScript convention `test`, `format`, and `bash_scope` are all `null`."
> after: "…are all `null`, **and the convention result has no `lint` key at all despite Phase 52's
> lint-and-test requirement**."

Verified against the raw capture, not the claim: `evidence/downstream/conventions.json` contains
**zero** occurrences of the string `lint`, and the convention object's key set is exactly
`['agents_md', 'bash_scope', 'dir', 'format', 'is_default', 'language', 'package', 'test']`. The
extension states a fact, not a guess.

Id-set integrity after the edit:
- Summary table ids: `OBS-D-01`, `OBS-D-02`, `OBS-D-03`, `OBS-D-04`.
- Detail section ids: `OBS-D-01`, `OBS-D-02`, `OBS-D-03`, `OBS-D-04`.
- 1:1 in both directions, no orphans, no `OBS-D-05` minted, no renumbering (the diff touches only
  the symptom sentence of OBS-D-03).

**Phase 52 can now trace a lint repair to an id.** Under Phase 52's "every change traces to an
OBS-D id" rule, a change adding a `lint` convention key traces to **OBS-D-03**, whose symptom now
names the missing key explicitly and whose disposition is already `repair-in-52`.

### 5. `external-drift.json` completeness — CLOSED, and each entry matches real history

`drifting_commits` went from 2 to **6** entries. I did not accept the list — I diffed it against the
target repo's actual log:

```
git -C ~/Desktop/2026/FeedbackOps log --format='%H|%ad|%s' --date=iso 1d1c8ed..4f16525
```

| # | Recorded hash | Recorded `author_date` | Recorded subject | Matches real history |
|---|---|---|---|---|
| 1 | `2a13c79e26e5052b000e925c12d0d0970c2caedd` | `2026-07-31T07:26:50+09:00` | docs(agents): FE chunks exempt from AC-ID discovery | ✓ |
| 2 | `86e7673c8b9476c1a1a53828c0a250d5fe0d8009` | `2026-07-31T07:27:02+09:00` | Merge PR #254 chore/fe-ac-id-exemption | ✓ |
| 3 | `6fae48fadc41124f2b54cf53a136c8fbb69d4a60` | `2026-07-31T07:42:17+09:00` | chore(verify): clean-state probe | ✓ |
| 4 | `59688d25a5386676443e72fad706bd75a1a5e907` | `2026-07-31T07:42:42+09:00` | Merge PR #256 feature/255-clean-probe | ✓ |
| 5 | `a8823f8f51a5fffa9ce79da0577823d9b05ef3f5` | `2026-07-31T07:58:04+09:00` | feat(surveys): request_task permission model | ✓ |
| 6 | `4f16525478e0ddeeb10ebe90960c33beb385a942` | `2026-07-31T07:58:34+09:00` | Merge PR #257 feature/239-request-task | ✓ |

All six full hashes, dates and subjects are exact matches, in the correct order, and the set is
exactly the commit range — no phantom entries, none missing. `4f16525` now has attribution metadata
where previously it appeared only as a bare `later_captures` SHA.

**Attribution not laundered.** The `attribution` string is unchanged by the repair and still reads:
"No Phase-51 command targeted the original checkout as an adoption target or mutated it; observed
inequality is documented third-party external drift, not an OBS-D adoption defect." Completing the
commit list strengthened the third-party attribution rather than converting the drift into a defect
id — and no new OBS-D id appeared (id set is still 01..04).

### 6. Two disclosure notes — PRESENT and accurately stated

**Note A (`untracked_set_equal` discriminating power), record line 9:**
> "The untracked-set equality compares two empty-string SHA-256 digests and therefore has low
> discriminating power."

Verified against the raw files, not the claim:
```
before.untracked-set.sha256 → e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
after.untracked-set.sha256  → e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
printf '' | shasum -a 256   → e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  -
```
Both digests equal the SHA-256 of empty input. The note is exactly right, including the honest
"low discriminating power" framing.

**Note B (secret-scan narrowing), record line 11:**
> "The narrowed inline-plan secret scan misses `sk-proj-...` and `sk-ant-api03-...` forms because
> its key character class dropped dashes. …the pattern lives in Phase-51 plan-inline checks, not a
> shipped gate, and is not changed here."

This matches the initial pass's independently reproduced finding (`(^|[^A-Za-z0-9])sk-[A-Za-z0-9]{20,}`
misses both prefixed forms because `-` was dropped from the class), correctly names the cause
(dash-free class, not the boundary anchor), and correctly bounds the impact (plan-inline, not a
shipped gate — consistent with NG-01). Accurate, not overstated in either direction.

### D-07 five-field completeness — survived the edit

| Record | symptom | reproduction | code location | purpose tag | proposed disposition |
|---|---|---|---|---|---|
| OBS-D-01 | ✓ | ✓ (literal) | `detect.py:46` | ② PROPOSAL ONLY | repair-in-52 |
| OBS-D-02 | ✓ | ✓ (literal) | `detect.py:273`; `package_facts.py:216` | ② PROPOSAL ONLY | no-change-evidence-backed |
| OBS-D-03 | ✓ (extended) | ✓ (literal) | `harness/project.toml:26`; `loader.py:297` | ① PROPOSAL ONLY | repair-in-52 |
| OBS-D-04 | ✓ | ✓ (literal) | `apply.py:306`; `test_atomic_apply.py:267` | ④ PROPOSAL ONLY | repair-in-52 |

All four still carry all five fields; every purpose tag still reads `PROPOSAL ONLY` (D-08 —
Phase 52 retains triage authority); D-16 still honored (OBS-D-01 and OBS-D-02 remain separate ids
even though the latter is clean).

### No softening — full diff review against `a0de4e8`

The repair commit touches 2 files, +15/−9. Every hunk classified:

| Change | Class |
|---|---|
| 5× SHA `723b32d6…` → `723b32d9…` | fact correction |
| OBS-D-04 `apply.py:246` → `apply.py:306` + test ref | fact correction |
| OBS-D-02/03 elided argv → literal argv | completion |
| OBS-D-03 symptom + missing-`lint` clause | **strengthens** the observation |
| +2 disclosure sentences (lines 9, 11) | **adds** disclosed limitations |
| `drifting_commits` 2 → 6 entries | completion |

**Zero deletions of observation content.** No symptom sentence was removed, narrowed, or hedged; no
`matches: false` became true; no disposition moved from `repair-in-52` to `no-change`; no severity
language was downgraded. The only two net-new sentences both *disclose weaknesses* in the phase's
own evidence — the opposite of softening. The `evidence/` captures other than `external-drift.json`
are untouched, so the record was reconciled to the raw evidence rather than the raw evidence being
reconciled to the record.

---

## SC-3 — OBS-03 verdict

**Verdict: VERIFIED. The refutation is evidence-decided and non-vacuous.**

The record's deciding excerpt matches `evidence/downstream/workspace-edge-comparison.json`
content exactly (modulo JSON pretty-print collapsing):

```
{"from": "@fops/backend",  "kind": "runtime", "to": "@fops/shared"}
{"from": "@fops/frontend", "kind": "runtime", "to": "@fops/shared"}
"result": "refuted"
```

Both decisive edges are present, `missing_edges: []`, `unexpected_edges: []`.

**Not decided by code reading.** I traced past the derived comparison file to the raw captured
output. `evidence/downstream/package-facts.json` — produced by an exit-0 run of
`build_facts(repo_root=<worktree>)` with its literal argv and cwd captured — contains
`@fops/backend → @fops/shared`, `@fops/frontend → @fops/shared`, and `@fops/ui → @fops/shared`, all
`kind: runtime`. The comparison file is a faithful projection of real tool output, not a hand-authored
assertion.

**The refutation is meaningful, not an artifact of a target that lacks the protocol.** I checked the
target's manifests at the baseline commit:

- `apps/frontend/package.json` → `{"@fops/shared": "workspace:*", "@fops/ui": "workspace:*"}`
- `apps/backend/package.json` → `{"@fops/shared": "workspace:*"}`
- `packages/ui/package.json` → `{"@fops/shared": "workspace:*"}`
- `pnpm-workspace.yaml` present (`apps/*`, `packages/*`)

So the `workspace:*` protocol really is in play and the current harness records the edge correctly
anyway — `_dependencies_from_package_json` keys off dependency *names* and ignores version values
(`detect.py:273`). OBS-03 is properly refuted, and per D-14 that is a milestone output, not a failure.

**Regression check after `c0d2568`:** the OBS-03 verdict section and
`workspace-edge-comparison.json` are untouched by the repair commit.

---

## SC-4 — No repair preceded the record

**Verdict: VERIFIED — re-confirmed after the repair commit.**

```
git diff --name-only 723b32d9 HEAD -- tools/ harness/ contracts/ docs/adr/   → empty
git diff --name-only 723b32d9 HEAD | grep -v '^.planning/phases/51-...'      → empty
```

Both checks still return empty with `c0d2568` included, and the repair commit itself touches only
two files, both inside the phase directory (`51-BASELINE-EVIDENCE.md`,
`evidence/isolation/external-drift.json`). `uv.lock` is unmodified.

**NG-01 confirmed by construction:** no command, skill, contract, JSON Schema, parser, CI job, gate,
or fixture was added — no file outside the phase directory changed at all. D-17 honored (no
reproduction fixture committed). Notably, the repair *documented* the secret-scan narrowing rather
than shipping a gate for it, which is the NG-01-compliant disposition.

**Regression suite green:** `uv run --frozen pytest` → **981 passed, 8 snapshots passed, 12.24s**,
with `uv.lock` unmodified. The repair is docs-only, so no source behavior could have changed.

---

## The Two Human-Directed Deviations

*(Preserved from the initial verification; unchanged by the repair — both analyses were re-checked
against the current tree and still hold. The secret-scan over-narrowing is now additionally
disclosed inside the evidence record itself, at line 11.)*

### Secret-scan pattern narrowing (`30025ed`) — correctly handled as a fix, with an over-narrowing side effect

Old: `sk-[A-Za-z0-9_-]{16,}` → New: `(^|[^A-Za-z0-9])sk-[A-Za-z0-9]{20,}`

**The false positive was real, not invented.** Running the old pattern over the evidence tree yields
genuine path-text matches: `sk-request-tracer-from-finding`, `sk-request-review-decisions`,
`sk-status-transition-and-kanban-board`, `sk-control-plane-lifecycle` — all substrings of
`task-request…` / `task-control-plane…` filenames. The new pattern yields zero hits on the same tree.

**It still catches a real key** — `sk-ABCdef0123456789ABCdef0123456789ABCdef0123456789` matches. So
this is not a blanket weakening.

**But the dash-free restriction is broader than the fix required (WARNING — now disclosed).** The
boundary anchor `(^|[^A-Za-z0-9])` alone kills the false positive (the char before `sk-` in
`task-request` is `a`, an alnum). Dropping `-` from the character class additionally makes the
pattern miss modern prefixed keys — I verified `sk-proj-ABCdef…` and `sk-ant-api03-ABCdef…` are both
**MISSED**. A form like `(^|[^A-Za-z0-9-])sk-[A-Za-z0-9_-]{20,}` would have fixed the false positive
without losing that coverage. Impact is bounded: this pattern lives only in the Phase-51 plans'
inline evidence scan, not in any shipped gate (NG-01 forbade adding one), and the evidence tree
contains no secrets under either pattern. **`c0d2568` records this limitation in
`51-BASELINE-EVIDENCE.md` line 11 rather than silently carrying it — the correct disposition for an
observation-only phase.**

### `16ae1f6` "correct changed-path observation" — genuine parse fix, did NOT soften the observation

The commit changed only `evidence/isolation/worktree.changed-paths.json`. Two raw
`git status --porcelain=v2` lines
(`1 .M N... 100644 … CLAUDE.md`) had been stored verbatim as if they were file paths — a parsing
bug, not an observation. The fix replaced them with the bare paths `AGENTS.md` / `CLAUDE.md` in
`before/after/changed` lists and dropped the two garbage strings from `unexpected_paths`.

**The defect survived the correction intact:** `matches` is still `false`; `unexpected_paths` still
holds the three real leftovers `.AGENTS.md.lock`, `.CLAUDE.md.lock`, `.claude/.settings.json.lock`.
`AGENTS.md` and `CLAUDE.md` are legitimately members of `expected_writable_destinations` (154
entries, matching apply's reported `applied=154`), so moving them out of "unexpected" is factually
correct, not a downgrade of severity. No softening.

---

## Replayability by a Fresh Reader (D-13)

| Metadata | Present? | Note |
|---|---|---|
| Literal argv per command | Yes | Inline in all four `reproduction` fields; byte-identical to `evidence/*/argv.txt`, `evidence/downstream/*.argv.txt` |
| cwd per command | Yes | all `/Users/hyojung/Desktop/2026/lifetimeworkflow` |
| Exit codes | Yes | all stages exit 0; captured in `exit-code.txt` |
| stdout/stderr | Yes | captured per stage |
| Tool versions | Yes | `metadata/tool-versions.json` — git 2.50.1, uv 0.11.6, Python 3.11.15, pnpm 11.1.1, each with argv/cwd/exit |
| Target SHA | Yes | `1d1c8eda…` resolves in `~/Desktop/2026/FeedbackOps`; ancestor of current `develop` |
| Harness SHA | **Yes (fixed)** | `723b32d960c835e81ec887ac84dcf7e070d47243` resolves in this repo and matches `metadata/harness.sha.txt` |

**Verdict: the prose record is now self-sufficient.** A reader who has only
`51-BASELINE-EVIDENCE.md` can check out both SHAs and run all four commands verbatim without
consulting `evidence/` and without guessing. The one remaining prerequisite is inherent to D-04, not
a record defect: the worktree was disposed, so any replay begins with re-provisioning at
`1d1c8eda…`.

---

## Requirements Coverage

| Requirement | Description | Status | Evidence |
|---|---|---|---|
| OBS-01 | Observed defects recorded with symptom · reproduction path · code location | SATISFIED | 4 records, five D-07 fields each, ids 1:1; every cited SHA resolves in the correct repo; `apply.py:306` provably produces OBS-D-04's symptom; all four argv literal and byte-matched to captures |
| OBS-03 | `workspace:*` recorded as workspace edge, not version string | SATISFIED (refuted) | `package-facts.json` + `workspace-edge-comparison.json`; target genuinely uses `workspace:*` |
| NG-01 (constraint) | No growth in commands/skills/contracts/CI jobs/gates | SATISFIED | Zero files changed outside the phase directory, including in the repair commit |

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|---|---|---|---|---|
| `51-BASELINE-EVIDENCE.md` | 11 | `...` in prose (`sk-proj-...`) | INFO — not a defect | Inside a disclosure note describing a key *form*, not inside a `reproduction` field; no literal value exists to inline |

All BLOCKER and WARNING anti-patterns from the initial verification are cleared:
- Fabricated 40-hex commit id (5 sites) — **removed**; no unresolvable hash remains anywhere.
- Wrong code location `apply.py:246` — **replaced** with `apply.py:306`, symptom-matched.
- `...`-elided `reproduction` fields — **replaced** with literal argv.
- Incomplete `drifting_commits` (2/6) — **completed** to 6/6, each entry history-matched.

No `TODO`/`FIXME`/`TBD`/`XXX` markers in any file changed by this phase.

---

## What Phase 52 Inherits

**Usable as a sole input contract — no correction required first.** The record is now accurate
against both repositories and self-sufficient for replay.

- **Stable, accurate ids.** `OBS-D-01..04` are 1:1 between summary and detail, each with a
  disposition. Phase 52 can enforce "every change traces to an OBS-D id" without any id being
  unusable.
  - `OBS-D-01` (repair-in-52) — `docs/design-prototype/package.json` over-enumeration →
    `detect.py:46`.
  - `OBS-D-02` (no-change, evidence-backed) — workspace edges already correct; Phase 52 SC-3 is
    **already satisfied at baseline** and needs a confirmation test, not a repair.
  - `OBS-D-03` (repair-in-52) — no `javascript` `[[languages]]` entry → all conventions null,
    **and no `lint` key exists in the convention shape at all**. This is the id a lint repair traces
    to; the previously-flagged traceability hole is closed. Verified independently: `conventions.json`
    contains zero occurrences of `lint`, and the key set is
    `agents_md, bash_scope, dir, format, is_default, language, package, test`. Phase 52 SC-4
    ("lint and test commands per package") therefore requires **adding a concept**, not just
    populating a null — plan for a shape change in `conventions_for`
    (`tools/harness_config/loader.py:297`) plus the `harness/project.toml` language entry
    (`harness/project.toml:26`).
  - `OBS-D-04` (repair-in-52) — `.lock` sidecars outside the manifest. **Start at
    `tools/adoption_apply/apply.py:306` in `_apply_marker_merge`** (the `lock_path` line), not
    `_atomic_replace`. Nothing in `apply.py` unlinks `lock_path`, so the repair is about lifecycle
    (remove on release, or declare the sidecars in the expected-destination manifest) — and note
    `tools/adoption_apply/tests/test_atomic_apply.py:265–269` explicitly warns **not** to assert on
    the sidecar's existence as a proxy for the `flock` control, since that assertion holds even with
    `fcntl.flock` deleted. Do not re-introduce that dead check when testing the fix.
- **Reproducibility metadata Phase 52 can rely on verbatim:** harness
  `723b32d960c835e81ec887ac84dcf7e070d47243` (this repo), target baseline
  `1d1c8eda9ed7dd4d79652224b2f3cc92a8dd535a` (FeedbackOps). Both resolve; all four `reproduction`
  argv are literal and match the captures byte-for-byte.
- **Baseline measurements Phase 52 measures improvement from:** `member-comparison.json` (5 required
  + 1 unexpected), `workspace-edge-comparison.json` (3/3 edges present), `convention-comparison.json`
  (6 packages, all null, no `lint` key), `worktree.changed-paths.json` (154 expected + 3 unexpected,
  `matches:false`).
- **Two disclosed evidence limitations Phase 52 should not re-inherit silently:**
  1. `untracked_set_equal: true` is a comparison of two empty-input digests
     (`e3b0c442…b855`) — it carries almost no discriminating power. If Phase 52 reuses the isolation
     proof, strengthen this check or lean on the index-digest reconstruction, which is what actually
     carried the SC-1 proof.
  2. The narrowed secret-scan pattern `(^|[^A-Za-z0-9])sk-[A-Za-z0-9]{20,}` misses `sk-proj-…` and
     `sk-ant-api03-…`. If Phase 52 promotes any scan into a shipped gate, restore dashes to the key
     class (e.g. `(^|[^A-Za-z0-9-])sk-[A-Za-z0-9_-]{20,}`) — the boundary anchor alone already kills
     the original false positive.
- **Clean starting state, but re-pin the target.** The Phase-51 worktree is disposed and FeedbackOps
  `develop` is at `4f16525`, six commits past the recorded baseline (all six now attributed in
  `external-drift.json`). Phase 52 must provision a fresh worktree and re-pin its own target SHA
  rather than assume `1d1c8ed`.
- **Open (non-blocking) governance item carried forward:** the ROADMAP SC-1 wording "the original
  `develop` checkout is byte-unchanged" is satisfied in substance but not literally (HEAD/index moved
  via third-party commits). Consider recording a formal verification override so this human-directed
  deviation is explicit on the record rather than implicit.

---

## Gaps Summary

**None. SC-2 is closed; the phase is 4/4.**

The initial pass accepted the hard part — a real baseline run that touched only the isolated
worktree, an isolation claim that survives independent reconstruction of both index digests, and a
non-vacuous OBS-03 refutation against a target that genuinely uses `workspace:*` — and rejected the
deliverable on accuracy: a harness SHA that resolved to no object anywhere, an OBS-D-04 code
location pointing at a function that cannot produce the observed artifacts, and two elided argv.

Commit `c0d2568` fixes exactly those, and the fixes hold under execution rather than under reading.
Every 40-hex string in the record now resolves — each against the correct repository, and each
failing to resolve against the wrong one; the record cites no short hashes at all, closing a surface
the previous pass had not swept. `apply.py:306` is not merely a valid line number: the f-string on it
generates the exact `.lock` naming shape observed, its enclosing `_apply_marker_merge` covers all
three destinations named in the symptom, and no `unlink` in the file ever removes it — so the symptom
and the code agree in both directions. The two restored argv are byte-identical to the captured
`*.argv.txt`, not paraphrases. The one surviving ellipsis is in prose describing an API-key form, not
in a reproduction field. The `lint` gap is now recorded inside OBS-D-03 with no renumbering and no
fifth id, and is true against `conventions.json`, which contains the string `lint` zero times. All
six drift commits are present with hashes, dates and subjects that match FeedbackOps' real
`1d1c8ed..4f16525` log exactly, and the third-party attribution is unchanged — the drift was not
laundered into an OBS-D id.

Most notably, the repair added evidence *against itself*: two new sentences disclose that
`untracked_set_equal` compares two empty digests and that the narrowed secret-scan misses modern
prefixed key forms. A full diff against `a0de4e8` shows zero deletions of observation content — no
symptom hedged, no `matches: false` flipped, no disposition downgraded. The record was reconciled to
the raw evidence, never the reverse. SC-4 still holds with the repair included: docs-only, entirely
inside the phase directory, `uv.lock` untouched, suite green at 981 tests.

Phase 52 can treat `51-BASELINE-EVIDENCE.md` as its sole input contract as written.

---

_Initial verification: 2026-07-31T15:05:00Z — gaps_found (3/4)_
_Re-verified: 2026-07-31T18:40:00Z — passed (4/4), SC-2 scope, against repair commit `c0d2568`_
_Verifier: gsd-verifier (goal-backward, FORCE stance)_
