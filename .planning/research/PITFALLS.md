# Pitfalls Research

**Domain:** opencode agent harness for a polyglot (.NET 10 + Python) semiconductor log-parser pipeline monorepo — contract-first, golden-equivalence tested, two-plane context memory, single-source dual-runtime emit
**Researched:** 2026-07-07
**Confidence:** MEDIUM-HIGH (polyglot boundary + legacy-migration pitfalls HIGH — grounded in `integration_contracts_design.md` §4-5 and `parser_project_revised.md` §8/§10; harness/opencode-runtime specifics MEDIUM — runtime behavior verified via opencode/Claude docs but versions move fast; context-memory-rot pitfalls MEDIUM — pattern-level, not tool-benchmarked)

> Scope note: the deliverable is **the harness**, not the pipeline. So "warning signs" are things you'd see in the *harness* (agents behaving wrong, gates not firing, memory drifting), not in the parser itself. The parser contracts are the *test fixture* that proves the harness works.

---

## Critical Pitfalls

### Pitfall 1: Over-engineering the harness before one real workflow validates it (META pitfall)

**What goes wrong:**
You build all 7 agents, 10 commands, 7 skills, 4 plugins, both runtime emitters, and the full two-plane memory layer — then discover on first real use that the golden-runner's normalization comparison doesn't match how the parser actually emits, that `/strangler-step` encodes a migration flow nobody follows, and half the skills never get routed to. Weeks of harness surface, zero validated workflow.

**Why it happens:**
The harness surface is enumerable and feels like "the spec" (it's literally listed in PROJECT.md Active requirements), so it reads as a build checklist. Every requirement in PROJECT.md is explicitly flagged as a **hypothesis until validated** ("모두 검증 전까지 가설", "ship to validate") — but enumerated lists invite completionism.

**How to avoid:**
Pick one **thin vertical slice** and drive it end-to-end before widening: seed one real contract (the TSV spec skeleton) → one `/component` scaffold → one `/golden` run that actually produces a normalized diff → one `/contract-check` that actually fails on a hash mismatch. Only after that closed loop works do you add the second agent/command. Treat `/checkpoint` + one golden loop as the walking skeleton. Defer `polyglot-auditor`, B-model extension points, and Claude-Code emit until the opencode-primary loop is proven.

**Warning signs:**
- Agents/commands/skills exist but no `.planning/` history shows one running end-to-end on real seed data.
- You're writing the 4th plugin before the 1st golden test has ever gone red-then-green.
- Skill/command descriptions reference workflows you've never actually executed.

**Phase to address:** Phase 1 (walking skeleton). This is a phase-*ordering* mandate, not a single feature — the roadmap must sequence "one validated loop" before "full surface."

---

### Pitfall 2: Context bloat — loading everything into every agent's context

**What goes wrong:**
Every agent boots with the full standard-log TSV spec, all 50+ normalization/correction rules, every AGENTS.md, the whole contracts index, and the entire glossary. Context fills with irrelevant material; the model gets slower, more expensive, and *less* accurate (relevant instructions get buried). A Python-scheduler task drags in the entire .NET converter contract.

**Why it happens:**
Two-plane memory + SessionStart injection makes it tempting to inject "the constitution" wholesale so nothing is ever missing. `instructions` in opencode.json takes globs, and a broad glob (`**/AGENTS.md`, `contracts/**`) silently pulls everything.

**How to avoid:**
- **Lazy, scoped loading.** Root AGENTS.md carries only cross-cutting invariants (the §4-5 checklist as a pointer, not inlined). Per-package AGENTS.md (dotnet/, python/) loads only when work is in that package.
- **Inject pointers, not payloads.** SessionStart injects *where* the constitution lives and the non-negotiable rules, not the full spec text. Reference/ docs are fetched on demand via skill, not preloaded.
- **Derived indexes stay small.** `contracts-index` and `repo-map` are lookup tables (names + paths), not full contents.
- Budget it: if session-start injection exceeds a few KB of instructions, it's already an anti-pattern.

**Warning signs:**
- SessionStart injection is measured in tens of KB.
- A dotnet-only task's transcript contains Python scheduler contract text.
- Response latency/cost climbs as you add contracts, even for narrow tasks.

**Phase to address:** Phase 3 (two-plane memory + SessionStart injection). Guard rail: cap injected instruction size and assert scoping in a plugin test.

---

### Pitfall 3: Over-broad permissions in the bash glob matrix (last-wins misconfigured)

**What goes wrong:**
The 15-key permission matrix uses bash glob patterns with last-wins precedence. A late broad `allow` (`*`) or an early-but-shadowed `deny` lets an agent run destructive commands — `rm -rf`, `git push --force`, `dotnet nuget push`, network calls — or edit the constitution plane (contracts/, adr/, golden/) that is supposed to be human-gated. On an ephemeral remote container where commit/push is the only persistence, a bad push is real damage.

**Why it happens:**
Glob last-wins ordering is easy to get subtly wrong: people append an `allow` at the bottom "to unblock myself" and it overrides every prior `deny`. Deny rules for the constitution plane are forgotten because the golden-approve human gate feels like enough.

**How to avoid:**
- **Default-deny, explicit-allow.** Start restrictive; add narrow allows. Never end the matrix with a broad `allow`.
- **Constitution plane is `deny`/`ask` for agent edits**: `edit` on `contracts/**`, `adr/**`, `golden/**` requires the human `/golden-approve` + CODEOWNERS gate, encoded as `ask` or `deny` in the matrix — not just social convention.
- **Order-test the matrix.** A plugin/CI check asserts representative commands resolve to the intended decision (e.g., `git push --force` → deny, `dotnet test` → allow, edit golden → ask). Because last-wins is positional, test the *resolution*, not the rule list.
- Per-agent scoping: golden-runner needs test/diff bash but not push; explorer is read-only.

**Warning signs:**
- The matrix ends with a catch-all `allow`.
- No test exists that feeds sample commands through the resolver.
- An agent successfully edited a file under `contracts/` or `golden/` without human approval.

**Phase to address:** Phase 1-2 (opencode.json + permission matrix, alongside contract-guard plugin). Verification: an order-resolution test suite for the matrix.

---

### Pitfall 4: Naive byte-diff golden tests producing false failures (the polyglot boundary, weaponized)

**What goes wrong:**
The golden-equivalence comparator does a raw byte/line diff of legacy output vs. new-system output. It goes red not because parsing logic differs but because of **representation differences** across the .NET↔Python boundary: a UTF-8 BOM the .NET writer prepends, CRLF vs LF, `1.0` vs `1`, `2026-07-07T00:00:00Z` vs `2026-07-07 00:00:00+00:00`, empty-string vs `\N` for null, trailing-tab handling, InvariantCulture vs locale decimal comma. Every run is noisy; real regressions hide in the noise; the team learns to ignore red.

**Why it happens:**
Byte-diff is the trivial first implementation and "works" on a hand-picked sample. The §4.3/§4.6 hazards (encoding/BOM, LF, TSV escaping, timezone, decimal/locale, null-vs-empty) are exactly the differences a byte comparator cannot tell apart from real bugs. This is the single most-called-out risk in `integration_contracts_design.md` ("폴리글랏의 버그는 대부분 '기능'이 아니라 표현 차이에서 난다").

**How to avoid:**
- **Compare on a normalized canonical form, not bytes.** The golden-runner parses both sides into a typed, canonical representation (strip BOM, normalize newlines to LF, parse decimals under InvariantCulture, parse timestamps to a single UTC instant, canonicalize null vs empty per contract) *then* diffs. This is exactly the "정규화 비교" the harness promises.
- **Separate representation failures from semantic failures in the report.** If the diff is purely representational, the comparator flags it as a *contract-conformance* failure (someone violated §5 checklist), not a parity regression — different remediation, different owner.
- The canonicalization rules ARE a contract: derive them from the §4-5 checklist, version them, and let a `polyglot-boundary` linter enforce the *emit* side so producers stay canonical.

**Warning signs:**
- Golden diffs flip red/green between machines or between .NET and Python producers with identical logic.
- Diff output shows only whitespace/encoding/format deltas.
- Team has a habit of re-running or eyeballing goldens instead of trusting them.

**Phase to address:** Phase 2 (golden-testing skill + golden-runner agent). This is the linchpin — build the normalized comparator *first*, before any migration command relies on it.

---

### Pitfall 5: Single-source emit drifting from generated runtime artifacts

**What goes wrong:**
The harness is authored once and emits opencode (primary) + Claude Code `.claude/` artifacts. Over time someone hand-edits a generated `.claude/` file (or a live `opencode.json`) to fix a bug; the source-of-truth isn't updated; regeneration silently reverts it — or worse, the two runtimes now behave differently and nobody knows which is canonical. Same class of drift the pipeline itself fears: two truths.

**Why it happens:**
Generated files are right there and editable; fixing the artifact is faster than fixing the generator. Dual-runtime means two artifact sets, doubling the drift surface. Runtime-specific constraints (skill size caps, description limits, frontmatter shape) tempt per-runtime hand-tweaks.

**How to avoid:**
- **Generated artifacts are read-only / regenerated in CI.** Mark them with a "DO NOT EDIT — generated from <source>" header and a CI check that fails if committed artifacts differ from a fresh emit (a drift gate for the harness's own outputs, mirroring contract-drift for the pipeline).
- **Encode per-runtime constraints in the emitter**, not by hand-editing outputs: the emitter enforces Claude's SKILL.md ≤ ~500 lines and description ≤ 200 chars (per Claude skill docs), and opencode's shape, from one source.
- Single source lives in the constitution/derived split correctly: source = hand-authored, both artifact trees = derived (never hand-maintained), same rule as repo-map/contracts-index.

**Warning signs:**
- A `.claude/` or emitted opencode file has manual edits with no corresponding source change.
- opencode and Claude runs of the "same" agent give materially different behavior.
- No CI job re-emits and diffs.

**Phase to address:** Phase 1 (single-source emitter) + Phase 2 (drift gate). Verify: `emit && git diff --exit-code` is green in CI.

---

### Pitfall 6: Runtime-specific limits violated (skill size / description caps)

**What goes wrong:**
A skill authored generously in the source exceeds a target runtime's hard cap on emit — Claude Code enforces SKILL.md description ≤ 200 chars (hard limit; name ≤ 64) and recommends body ≤ ~500 lines; opencode has its own shape. The emitted artifact is silently truncated, rejected, or the skill never loads — and because opencode is the *primary* target you may not notice the Claude-side breakage until much later.

**Why it happens:**
Single-source authoring hides per-runtime limits. Limits differ between runtimes and change across versions (training data is stale here — verify against current docs).

**How to avoid:**
- **Validate against each runtime's limits at emit time**; fail the build, don't truncate. Keep the limit values in one config the emitter reads.
- Author the *source* skill to the strictest common denominator (short descriptions, split reference material into linked files — which also helps context bloat, Pitfall 2).
- Re-verify caps against live docs at each dependency bump, not from memory.

**Warning signs:**
- A skill loads in opencode but not Claude Code (or vice versa).
- Emit warnings about truncated/overlong frontmatter.
- Skill descriptions creep past ~200 chars in source.

**Phase to address:** Phase 1-2 (emitter + skill-creator skill). Verify: emit-time schema/length validation per runtime.

---

### Pitfall 7: Description-as-label → bad agent/skill routing

**What goes wrong:**
Agent and skill `description` fields are written as *titles* ("Golden runner", "Python agent") instead of *routing triggers* ("Use when comparing legacy vs. new parser output for equivalence; normalizes encoding/decimal/timezone before diffing"). The orchestrator (or the model deciding which skill to invoke) routes to the wrong subagent, or never invokes the right skill, because the description gives no invocation signal. In Claude/opencode, the description is literally what the model uses to decide *when* to invoke.

**Why it happens:**
Descriptions read like documentation labels to humans, so people write labels. The 200-char cap pushes toward terse names. The functional load of the field (routing) is non-obvious.

**How to avoid:**
- Write every description as **"Use when / trigger + what it does"**, verb-first, mentioning concrete triggers (contract change, golden red, boundary violation, migration step).
- Skill-creator skill should template this and reject label-only descriptions.
- **Test routing:** give the orchestrator representative tasks and assert the right subagent/skill is selected. Skill sprawl (Pitfall 8) makes routing worse, so keep the set small and descriptions disjoint.

**Warning signs:**
- Descriptions are noun phrases with no "when."
- Orchestrator picks the wrong agent, or does work itself instead of delegating.
- Two skills have overlapping/ambiguous descriptions.

**Phase to address:** Phase 2-3 (agents + skills authoring). Verify: routing test fixtures.

---

### Pitfall 8: Skill sprawl and agents ignoring the rules

**What goes wrong:**
(a) Skill count grows (dotnet, python, pipeline-patterns, data-contracts, golden-testing, normalization-catalog, skill-creator... then more) until they overlap, contradict, and dilute routing. (b) Agents "read" root AGENTS.md but proceed to violate it — edit a contract without going through `/golden-approve`, skip the boundary checklist, hand-edit a derived doc — because rules that live only in a prose instruction file are advisory, and models drift from long prose.

**Why it happens:**
Every new need feels like "add a skill." Rules-as-prose have no enforcement; the model treats them as soft context, especially deep in a long session. Monolithic AGENTS.md (Pitfall 11) makes the rules easy to lose.

**How to avoid:**
- **Enforce invariants with plugins/hooks, not prose.** contract-guard blocks writes to the constitution plane; format-on-write enforces LF/no-BOM/InvariantCulture on emit; polyglot-boundary linter fails on §5 violations. A rule that must hold gets a hook; prose is only for judgment calls.
- **Cap and curate skills.** Prefer fewer, composable skills; fold overlapping ones. skill-creator should require a "why not an existing skill?" justification.
- Keep rules short, imperative, and co-located with the work (per-package AGENTS.md), not a wall of text.

**Warning signs:**
- Two skills you can't crisply distinguish.
- An agent violated a "rule" and nothing stopped it (no hook fired).
- AGENTS.md keeps growing and agents cite it less.

**Phase to address:** Phase 2 (contract-guard / format-on-write / boundary plugins) + ongoing skill curation. Verify: attempt a forbidden action in a test and assert the hook blocks it.

---

### Pitfall 9: Agents "fixing" golden files to make CI green (legacy-migration safety)

**What goes wrong:**
The golden test goes red during a strangler step. Instead of investigating whether the new parser diverged, an agent (or a human under deadline) **updates the golden/expected file to match the new output** — turning the safety net into a rubber stamp. The undetected divergence flows into production statistics. This is the highest-consequence failure in the whole harness: it defeats the one language-agnostic safety mechanism the project depends on.

**Why it happens:**
"Make CI green" is a legible, rewarded goal; regenerating goldens is a one-command fix; agents optimize for the visible pass/fail signal. Contracts and goldens *do* legitimately change sometimes (Pitfall 4's representation fixes, intentional behavior changes), so blanket-blocking is wrong too — which makes the loophole feel justified.

**How to avoid:**
- **Golden updates require the human gate, always.** `golden/` is in the constitution plane: CODEOWNERS + `/golden-approve` + contract-guard deny agent writes. An agent may *propose* a golden change (with a diff and a written rationale of "intended vs. unintended") but cannot merge it.
- **Every golden change must cite an ADR or contract-change record** (§6 contract change mgmt: version bump + golden update together). A golden diff with no linked decision is auto-rejected.
- Distinguish "representation-only" diffs (route to boundary fix, Pitfall 4) from "semantic" diffs (require explicit human sign-off) in the runner's report so approving a real behavior change is a conscious act.

**Warning signs:**
- A golden file changed in the same commit that made a failing test pass, with no ADR/rationale.
- `/golden-approve` history is empty but goldens have churned.
- Commit messages like "update goldens" / "fix expected output."

**Phase to address:** Phase 2 (golden gate + CODEOWNERS) then enforced through every migration step (`/strangler-step`). Verify: attempt an agent golden edit → blocked; approval flow leaves an audit trail.

---

### Pitfall 10: Big-bang rewrite temptation + missing characterization of undocumented legacy behavior

**What goes wrong:**
Because the harness *could* scaffold everything, the roadmap tries to replace the legacy parser wholesale rather than strangler-stepping. But the legacy parser's behavior is **undocumented** (`parser_project_revised.md` §2.2, §8: no tests, no handover, 50+ scattered normalization/correction cases). Without characterizing the legacy's hidden behaviors first, "equivalence" has no reference — you can't diff against a baseline you never captured. Result: silent loss of edge-case handling that only surfaces weeks later in downstream stats.

**Why it happens:**
Big-bang feels faster and cleaner than a strangler; the harness's scaffolding power amplifies the temptation. The legacy's undocumented exceptions are invisible until they break — you don't know what you're about to lose.

**How to avoid:**
- **Characterization-first, encoded as a harness step.** Before replacing any path, capture legacy input→output as golden fixtures (§8 mitigation: "골든 테스트로 실제 입출력을 기준 삼아 동작을 역으로 고정"). The harness should make "capture legacy behavior as golden" a first-class command, prerequisite to `/strangler-step`.
- **Strangler, not big-bang**, encoded in `/strangler-step`: one path at a time, each behind golden equivalence + the human gate. The project doc explicitly chose 단계별 전환 — the harness must make that the path of least resistance.
- Treat discovered legacy behaviors as findings to document (ADR/reference) as they surface, not as noise.

**Warning signs:**
- A migration step exists with no captured legacy baseline for that path.
- Roadmap phases replace multiple components at once.
- "We'll characterize it later" appears in planning.

**Phase to address:** Phase 2 (golden capture) precedes Phase 5 (strangler/migration commands). Ordering is the mitigation: no `/strangler-step` before characterization exists.

---

### Pitfall 11: Nested AGENTS.md closest-wins silently dropping root/constitutional guidance

**What goes wrong:**
Per-package AGENTS.md (dotnet/, python/) are meant to *add* package rules on top of root invariants. But merge semantics differ by runtime: some resolvers **concatenate root→cwd**, while others (e.g., Codex-style) **stop searching once they reach the working directory**, so a deep AGENTS.md can *replace* rather than *extend* — silently dropping the root's cross-cutting §4-5 boundary rules exactly where they matter most (inside a language package). Because the harness emits to multiple runtimes, the same file tree behaves differently per runtime.

**Why it happens:**
"Closest-wins" and "merge/concatenate" look identical when you test in the root dir. The divergence only appears when you run *inside* a package under a runtime with replace-semantics. Dual-runtime emit makes this a cross-product hazard.

**How to avoid:**
- **Don't rely on inheritance for non-negotiables.** Enforce the §5 boundary invariants with a plugin/hook (polyglot-boundary linter, format-on-write) that runs regardless of which AGENTS.md loaded — hooks don't have merge semantics.
- Keep per-package AGENTS.md **additive and self-sufficient**: restate (or explicitly `@import`/reference) the boundary checklist pointer so a package file alone is still safe.
- **Verify merge behavior per target runtime** (opencode vs. Claude Code vs. Codex differ; verify against current docs — this moves). Test: run a task inside dotnet/ and assert a root invariant still applies.

**Warning signs:**
- A boundary rule enforced at root is violated only when working deep in a package.
- Behavior differs between opencode and Claude runs of the same in-package task.
- Per-package AGENTS.md assume root context that may not be loaded.

**Phase to address:** Phase 3 (memory/instruction layering) — but the real safety net is Phase 2 hooks. Verify: in-package invariant test across both runtimes.

---

### Pitfall 12: Hand-maintained derived docs going stale (context-memory rot)

**What goes wrong:**
repo-map, contracts-index, and Diátaxis `reference/` are supposed to be *derived* from contracts, but someone edits them by hand (or generation stops running). They drift from the actual contracts. Agents then read a stale index, target the wrong contract path, and "confidently" do the wrong thing — the memory layer actively misleads instead of merely being absent (a silent, confident lie is worse than a gap).

**Why it happens:**
Derived docs are editable text; a quick manual fix is faster than fixing/running the generator. Generation that isn't gated in CI quietly rots. This is the exact failure mode PROJECT.md's constraint warns about: "파생물은 손으로 관리 금지(자동 생성)."

**How to avoid:**
- **Derived = generated, never hand-edited.** Header the files "generated — do not edit"; regenerate in a hook/CI; fail the build if a fresh generation differs from committed (same drift gate as Pitfall 5).
- **Constitution vs. derived boundary is load-bearing:** contracts/adr/glossary/golden are human-owned SSOT; everything else regenerates from them. If a fact lives in both, the derived copy loses.
- `/docs-sync` regenerates reference/ from contracts and is the *only* way reference/ changes.

**Warning signs:**
- A contracts-index entry points to a path that moved.
- `git blame` shows manual edits to repo-map/reference/.
- `/docs-sync` output diffs from committed docs.

**Phase to address:** Phase 3 (two-plane memory + derived generation). Verify: `regenerate && git diff --exit-code` green; manual edit to a derived file is caught.

---

### Pitfall 13: Auto-captured memories misleading silently (volatile plane rot)

**What goes wrong:**
The volatile plane (`.memory/` activeContext, progress) auto-captures session state. A stale or wrong auto-memory ("carryover format decided as X", "TSV column 3 is timestamp") gets injected non-ignorably at SessionStart and is trusted as fact — but it was a mid-session guess, a since-reverted decision, or captured from an abandoned branch. Every future session inherits the error. Because injection is *non-ignorable* by design, the bad memory is amplified, not questioned.

**Why it happens:**
Auto-capture can't tell durable decisions from transient scratch. Non-ignorable injection (a deliberate feature to prevent rule-drop) has a dark side: it launders unverified state into authoritative context. Many project facts are explicitly *undecided* (§7/§10: TSV columns, DB schema, carryover, rework policy) — precisely the things a memory might wrongly "remember" as settled.

**How to avoid:**
- **Decisions are ADR (append-only, human-owned); volatile memory holds only progress/intent, never durable facts.** Keep the planes strictly separated: activeContext is "what I'm doing now," not "what is true."
- **Mark volatile memory as provisional on injection** ("unverified session state — confirm against contracts/ADR before relying"), so it's a hint, not a source of truth. Contracts/ADR always override memory on conflict.
- Undecided items (§7/§10) stay explicitly flagged UNDECIDED in the constitution plane so a memory can't quietly "resolve" them.

**Warning signs:**
- An agent asserts a §7/§10 "미정" item as decided, citing memory not an ADR.
- activeContext contains statements phrased as durable facts.
- A reverted decision keeps reappearing across sessions.

**Phase to address:** Phase 3 (volatile plane + SessionStart injection). Verify: injected memory is labeled provisional; conflict test (memory vs. ADR) resolves to ADR.

---

### Pitfall 14: Contract/code divergence not detected (the drift gate has a hole)

**What goes wrong:**
The core promise — "code that disagrees with the contract is the thing that's wrong" — only holds if divergence is *detected*. The contract-drift gate is supposed to catch it via schema hashing, but the hash covers the wrong surface (e.g., hashes the TSV column list but not the null/BOM/decimal conventions from §4.3/§4.6), so a producer can violate the boundary contract while the hash stays green. Contract-first becomes contract-in-name-only.

**Why it happens:**
Hashing "the schema" naturally captures the visible structure (columns) and misses the cross-cutting representation contract (§4 cross-cutting contracts) that isn't in a column list. The §5 checklist items are conventions, not schema fields — easy to leave out of the hash.

**How to avoid:**
- **Hash the full contract surface**, including the §4-5 cross-cutting conventions (encoding/BOM policy, LF, TSV escaping, timezone format, InvariantCulture, null-vs-empty, identifier/interval `[start,end)` rules), not just column definitions.
- **Pair the hash gate with a behavioral gate:** the polyglot-boundary linter checks actual emitted bytes against the conventions; golden equivalence checks behavior. Hash catches *contract text* changes; linter+golden catch *conformance*. You need all three.
- Version contracts (§6) so an intended change forces a visible hash bump + golden update together — an unversioned silent change is the thing to make impossible.

**Warning signs:**
- Contract hash green while a producer emits BOM/CRLF/locale-decimal.
- The hash input is just the column list.
- A contract changed without a version bump and nothing complained.

**Phase to address:** Phase 2 (contract-guard + contract-drift gate) with Phase 4 (boundary linter). Verify: mutate a §4 convention and assert the hash changes; emit a BOM and assert the linter fails.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Byte-diff golden comparator (skip normalization) | Ships in an hour | False-red epidemic; safety net distrusted; real regressions hidden (Pitfall 4) | Never for the real gate. OK as a throwaway spike to feel out fixtures |
| Inline full contracts into every AGENTS.md | Nothing ever "missing" | Context bloat, cost, buried instructions (Pitfall 2) | Never — inject pointers |
| Hand-edit a generated `.claude/`/opencode artifact to unblock | Instant fix | Silent drift, dual-runtime divergence (Pitfall 5) | Never — fix the source + re-emit |
| Skip legacy characterization, start rewriting | Feels like progress | No equivalence baseline; silent behavior loss (Pitfall 10) | Never for paths going to prod |
| Broad `allow` at bottom of permission matrix | Stops permission prompts | Destructive-command / constitution-edit exposure (Pitfall 3) | Never; scope the allow narrowly |
| Auto-capture everything into volatile memory | Rich context for free | Confident wrong memories injected forever (Pitfall 13) | Only if marked provisional + ADR overrides |
| Build full harness surface up front | Feels comprehensive | Weeks of unvalidated surface (Pitfall 1) | Never; walking skeleton first |
| Defer B-model (gRPC/queue) to extension points only | Simpler MVP (matches §④ A-model) | Must keep job payload isomorphic now or pay later | **Acceptable and recommended** — this is the intended path |

## Integration Gotchas (the .NET↔Python boundary — §4-5)

| Boundary point | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| File encoding (§4.3) | .NET writes UTF-8 **with BOM**; Python reads BOM as part of first column | UTF-8, **no BOM**, enforced on emit by format-on-write hook |
| Newlines (§4.3) | .NET defaults to CRLF; comparator/parser sees phantom `\r` | LF fixed; hook rejects CRLF |
| TSV escaping (§4.3) | Tab/newline inside a value un-escaped → column shift | One escaping rule in the contract; linter checks both producers |
| Timezone (§4.4) | .NET `DateTime` Kind-less vs Python naive/aware → wrong instant | Serialize as one UTC string format; parse to instant before compare |
| Decimal/locale (§4.6) | .NET `ToString()` locale-dependent → `1,5` vs `1.5` | **InvariantCulture** forced; `.` only; no thousands separator |
| Null vs empty (§4.3) | Empty string and NULL conflated across languages | Fixed sentinel per contract; canonicalized before diff |
| File write atomicity (§②) | Reader (.NET) reads a half-written file | temp-write → atomic rename, or completion marker |
| Identifiers/intervals (§4.2) | Case/width differ; interval boundary off-by-one/dup | Fixed identifier casing+width; half-open `[start,end)` everywhere |
| DB charset (§⑤) | Connection charset ≠ UTF-8 → mojibake on .NET insert | DB + driver + connection all UTF-8 |
| exit codes (§4.5) | A-model spawn: nonzero not mapped to failure reason | Standard exit-code→reason map; 0=success only |

## "Looks Done But Isn't" Checklist

- [ ] **Golden runner:** looks done (diffs two files) — verify it **normalizes BOM/LF/decimal/timezone/null before diffing** and separates representation vs. semantic failures (Pitfall 4).
- [ ] **Permission matrix:** looks done (15 keys set) — verify **resolution order** with a sample-command test and that constitution-plane edits are `ask`/`deny` (Pitfall 3).
- [ ] **Single-source emit:** looks done (produces both trees) — verify **CI re-emits and diffs**, artifacts marked do-not-edit, per-runtime limits validated (Pitfalls 5, 6).
- [ ] **Contract-drift gate:** looks done (hashes schema) — verify the hash covers **§4 cross-cutting conventions**, not just columns (Pitfall 14).
- [ ] **Two-plane memory:** looks done (injects at SessionStart) — verify derived docs **regenerate green in CI** and volatile memory is **marked provisional** (Pitfalls 12, 13).
- [ ] **Golden gate:** looks done (goldens in repo) — verify an **agent cannot edit goldens**; approval leaves an audit trail linked to ADR (Pitfall 9).
- [ ] **Strangler command:** looks done (scaffolds a step) — verify it **refuses to run without a captured legacy baseline** for that path (Pitfall 10).
- [ ] **Per-package AGENTS.md:** looks done (rules load in package) — verify **root invariants still apply inside the package** on every target runtime (Pitfall 11).
- [ ] **Agent routing:** looks done (agents exist) — verify **descriptions trigger correct routing** via fixtures, not just read as labels (Pitfall 7).

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Goldens rubber-stamped (P9) | HIGH | Recapture true legacy baselines; re-diff all "approved" goldens against them; revert unauthorized golden edits; add contract-guard deny + ADR-link requirement retroactively |
| Byte-diff false-reds (P4) | MEDIUM | Retrofit normalized canonical comparator; reclassify historical reds as representation vs. semantic; delete "eyeball the golden" habit |
| Emit drift (P5) | LOW-MEDIUM | Re-emit from source; discard hand-edits after diffing to recover any real fix into source; add CI drift gate |
| Derived-doc rot (P12) | LOW | Regenerate; add do-not-edit header + CI gate; blame-audit for lost manual fixes |
| Bad volatile memory (P13) | LOW | Purge `.memory/`; re-derive from contracts/ADR; add provisional labeling + ADR-override rule |
| Big-bang partial rewrite (P10) | HIGH | Stop; characterize each replaced path retroactively; wrap in golden gate before further steps |
| Over-broad permissions (P3) | LOW | Rewrite matrix default-deny; add resolution test; audit git history for damage |
| Over-built harness (P1) | MEDIUM | Freeze surface; drive one vertical slice; prune agents/skills never routed to |

## Pitfall-to-Phase Mapping

Suggested phase labels (greenfield — roadmap may renumber; **ordering is the load-bearing part**).

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| P1 Over-engineering harness | **Phase 1** (walking skeleton) | One golden loop runs end-to-end on seed data before surface widens |
| P2 Context bloat | Phase 3 (memory/injection) | Injection size capped; scoping asserted per package |
| P3 Over-broad permissions | Phase 1-2 (opencode.json + contract-guard) | Sample-command resolution test; constitution edits gated |
| P4 Byte-diff false-reds | **Phase 2** (golden-testing) — build first | Identical logic across .NET/Py diffs green; repr vs. semantic split |
| P5 Emit drift | Phase 1 (emitter) + 2 (drift gate) | `emit && git diff --exit-code` green in CI |
| P6 Runtime limits | Phase 1-2 (emitter + skill-creator) | Emit-time per-runtime length/schema validation |
| P7 Description-as-label | Phase 2-3 (agents/skills) | Routing fixtures select correct subagent/skill |
| P8 Skill sprawl / ignored rules | Phase 2 (plugins) + ongoing | Forbidden action blocked by hook in test |
| P9 Goldens rubber-stamped | **Phase 2** (golden gate) → every strangler step | Agent golden edit blocked; approval audit-trailed to ADR |
| P10 Big-bang / no characterization | Phase 2 (capture) **before** Phase 5 (strangler) | `/strangler-step` refuses without baseline |
| P11 Nested AGENTS.md drop | Phase 3 (layering) + Phase 2 hooks | In-package invariant holds on both runtimes |
| P12 Derived-doc rot | Phase 3 (derived generation) | Regenerate green; manual edit caught |
| P13 Bad volatile memory | Phase 3 (volatile plane) | Injected memory provisional; ADR wins conflict |
| P14 Contract/code divergence undetected | Phase 2 (drift gate) + Phase 4 (linter) | §4 convention mutation bumps hash; BOM emit fails linter |

**Ordering mandates that fall out of the pitfalls:**
1. **Walking skeleton (P1) before full surface.** One validated loop first.
2. **Normalized golden comparator (P4) is the linchpin** — build before any migration command depends on it.
3. **Golden capture / characterization (P10) before any strangler step.**
4. **Golden human-gate + contract-guard (P9, P3) before agents touch the constitution plane.**
5. **Drift gates (P5, P12, P14) land with the thing they guard**, not bolted on later.

## Sources

- `/home/user/lifetimeworkflow/.planning/PROJECT.md` — harness surface, two-plane memory, constraints (HIGH, primary)
- `/workspace/presentationformat/archive/parserimprove/uploads/integration_contracts_design.md` §4-5 boundary checklist, §6 contract change mgmt (HIGH, primary)
- `/workspace/presentationformat/archive/parserimprove/uploads/parser_project_revised.md` §2.2, §5, §8 risks, §7/§10 undecided items (HIGH, primary)
- [Agents | OpenCode](https://opencode.ai/docs/agents/), [Rules | OpenCode](https://opencode.ai/docs/rules/), [Agent Skills | OpenCode](https://opencode.ai/docs/skills/), [Config | OpenCode](https://opencode.ai/docs/config/), [Commands | OpenCode](https://opencode.ai/docs/commands/) — agent/skill/permission/instructions model (MEDIUM; opencode.ai blocked by proxy policy, relied on search snippets — re-verify version-specific behavior)
- [Custom instructions with AGENTS.md — Codex | OpenAI](https://developers.openai.com/codex/guides/agents-md) — nested "stops searching at cwd" replace-vs-merge semantics (MEDIUM; confirms per-runtime divergence, P11)
- [Extend Claude with skills — Claude Code Docs](https://code.claude.com/docs/en/skills), [SKILL.md Format Reference](https://www.agensi.io/learn/skill-md-format-reference), [Skill authoring best practices — Anthropic](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) — description ≤200 chars, name ≤64, body ≤~500 lines (MEDIUM-HIGH; P6)

---
*Pitfalls research for: opencode agent harness (polyglot .NET/Python log-parser pipeline)*
*Researched: 2026-07-07*
