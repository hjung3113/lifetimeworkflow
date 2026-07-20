"""DOCSUP-02/03 — the committed review ledger and the disposition/digest coherence rule (D-04).

This module is READ-ONLY BY CONSTRUCTION, and that is the point of D-06. It exposes no
``write``/``save``/``bump`` function of any kind, and its source contains no filesystem write.
Raising ``[coverage] uncovered_max`` or ``[coverage] binding_min`` is a HUMAN edit: a gate that can
lower its own threshold is self-blessing, so the ratchet must be impossible for the guard to move,
not merely left un-moved. ``tests/test_ledger.py`` proves both halves — a public-surface allowlist
and a static write-call scan with a live planted-token negative control.

AGENT-AUTHORITY BOUNDARY (ratified by ADR-0010, plan 28-08). Agents may PROPOSE registry rows; only
a human may author a ledger disposition; and the LEDGER — not the registry — is the greenness
authority. ``first_seen-unratified`` below is the in-code expression of that boundary, and plan
28-09's write-side refusal is its counterpart. Neither alone is sufficient: 28-09 stops the write,
this rule means that even a write which slips through cannot produce green.

Determinism: no wall-clock, no calendar, no floating-point, and every returned sequence is sorted.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

# The ledger's location, as a MODULE CONSTANT — never a registry- or caller-controlled value, so
# nothing attacker-influenced can reach the ``git`` argv below (T-28-20).
LEDGER_PATH = "docs/.docs-review-ledger.toml"

DISPOSITIONS = (
    "updated",
    "reviewed-no-change",
    "REVIEWED_STILL_CURRENT",
    "SUPERSEDING_ADR_REQUIRED",
)

# The two CONTENT-BOUND dispositions: they claim "the document still matches what I reviewed", a
# statement about the present tree alone. ``REVIEWED_STILL_CURRENT`` is the ADR-facing alias (D-09).
CONTENT_BOUND_DISPOSITIONS = ("reviewed-no-change", "REVIEWED_STILL_CURRENT")

# ── reason constants ──────────────────────────────────────────────────────────────────────────
# Three of these describe symptoms an operator could confuse, and they carry three DIFFERENT
# remedies, so they are three distinct greppable literals and must stay that way:
#   REASON_STALE        -> "the document moved; review it and re-record the digest"
#   REASON_FIRST_SEEN   -> "this row has never been ratified; a human must land it in a commit"
#   REASON_UNVERIFIED   -> "history is unreadable; fetch depth/HEAD is the problem, not the docs"
# An indistinguishable failure teaches the wrong fix (D-08), which is why a test asserts them
# pairwise distinct rather than leaving it to inspection.
REASON_UNKNOWN_BINDING = "unknown-binding"
REASON_STALE = "stale-digest"
REASON_INCOHERENT = "disposition-incoherent"
REASON_FIRST_SEEN = "first_seen-unratified"
REASON_UNVERIFIED = "unverified-disposition"
REASON_OPEN_OBLIGATION = "superseding-adr-required"
REASON_BINDING_COUNT = "binding-count-regression"
REASON_BINDING_COUNT_TIGHTEN = "binding-count-can-tighten"

LEVEL_FAIL = "fail"
LEVEL_WARN = "warn"
LEVEL_NOTE = "note"

# ── the permitted committed shape — an ALLOWLIST, never a denylist ────────────────────────────
# DOCSUP-02 verbatim: no time, no human identity, no prose copy, no model identifier. An allowlist
# is used precisely so a forbidden key cannot be smuggled in later by a spelling nobody
# anticipated — `reviewed_at`, `date`, `updated_at` and `timestamp` are four spellings of the same
# forbidden fact, and the next one will be a fifth. `tools/adoption_apply/approval.py`'s schema does
# carry `approved_at`, but that is a per-TASK artifact rather than a repo-wide committed baseline,
# and is explicitly NOT a licence for a timestamp here (research Q2).
_TOP_LEVEL_KEYS = frozenset({"coverage", "reviewed"})
_COVERAGE_KEYS = frozenset({"uncovered_max", "binding_min"})
_ROW_KEYS = frozenset({"id", "source_digest", "target_digest", "disposition"})

_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")

# Shape-anchored model identifiers: a vendor token bound to a MODEL token, never the bare vendor
# word. D-07's human corpus includes root ``CLAUDE.md``, so a binding id like
# ``claude-md-vs-agents-md`` is ordinary and must load — a keyword blocklist would reject it. Same
# posture as ``tools/hooks/secret_scan.py``: anchor on structure, keep false positives near zero.
_MODEL_IDENTIFIER_RE = re.compile(
    r"(?i)\b(?:"
    r"claude-(?:opus|sonnet|haiku|instant|\d)"
    r"|anthropic/"
    r"|openai/"
    r"|gpt-\d"
    r"|o\d-(?:mini|preview)"
    r"|gemini-\d"
    r"|llama-?\d"
    r"|mistral-\w+"
    r")"
)


class LedgerError(ValueError):
    """The ledger is invalid — a shape violation, not a staleness finding.

    Carries the offending element by name and NEVER the file's content: a corrupt or hostile ledger
    must not be echoed back out through the gate's output (T-28-22).
    """


@dataclass(frozen=True, order=True)
class ReviewedRow:
    """One ``[[reviewed]]`` row. Ordered so ``sorted()`` on rows is deterministic by id."""

    id: str
    source_digest: str
    target_digest: str
    disposition: str


@dataclass(frozen=True, order=True)
class Finding:
    """One incoherence. ``level`` is advisory to the caller — ``ledger.py`` never decides an exit
    code; ``guard.classify()`` (plan 28-05) does."""

    binding_id: str
    reason: str
    level: str
    message: str


# ── load ──────────────────────────────────────────────────────────────────────────────────────


def load_ledger(path: str | Path) -> tuple[dict[str, int | None], list[ReviewedRow]]:
    """Parse the ledger at ``path`` into ``(coverage, rows sorted by id)``.

    A MISSING file returns ``({}, [])`` — a repo that has not seeded a ledger yet is empty, not
    broken. Anything present but off-shape raises ``LedgerError`` naming the offending element.

    ``coverage`` carries ``uncovered_max`` and ``binding_min`` as ``int | None``; ``0`` is a
    legitimate (indeed the strictest) ratchet value and is never confused with absent.
    """
    target = Path(path)
    if not target.is_file():
        return {}, []

    raw = _read_text(target)
    if _MODEL_IDENTIFIER_RE.search(raw):
        raise LedgerError(
            f"{target.name}: a model identifier appears in the ledger — the committed review "
            f"record carries no model identity (CLAUDE.md non-negotiable)"
        )

    try:
        doc = tomllib.loads(raw)
    except tomllib.TOMLDecodeError:
        # Deliberately drop the parser's message: it quotes the offending line, and the ledger is
        # untrusted input that must not be echoed into the gate's output (T-28-22). No position is
        # reported either — `TOMLDecodeError.lineno` only exists on Python 3.14+, and a message
        # whose detail varies with the interpreter version is not a stable operator contract.
        raise LedgerError(f"{target.name}: not valid TOML") from None

    extra = sorted(set(doc) - _TOP_LEVEL_KEYS)
    if extra:
        raise LedgerError(f"{target.name}: unknown top-level table(s) {extra}")

    coverage = _load_coverage(target.name, doc.get("coverage", {}))
    rows = _load_rows(target.name, doc.get("reviewed", []))
    return coverage, sorted(rows)


def _read_text(target: Path) -> str:
    try:
        return target.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError) as exc:
        raise LedgerError(f"{target.name}: unreadable ({type(exc).__name__})") from None


def _load_coverage(name: str, block: object) -> dict[str, int | None]:
    if not isinstance(block, dict):
        raise LedgerError(f"{name}: [coverage] must be a table")
    extra = sorted(set(block) - _COVERAGE_KEYS)
    if extra:
        raise LedgerError(f"{name}: unknown [coverage] key(s) {extra}")
    coverage: dict[str, int | None] = {}
    for key in sorted(_COVERAGE_KEYS):
        value = block.get(key)
        if value is None:
            coverage[key] = None
            continue
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise LedgerError(f"{name}: [coverage] {key} must be a non-negative integer")
        coverage[key] = value
    return coverage


def _load_rows(name: str, block: object) -> list[ReviewedRow]:
    if not isinstance(block, list):
        raise LedgerError(f"{name}: [[reviewed]] must be an array of tables")
    rows: list[ReviewedRow] = []
    seen: set[str] = set()
    for entry in block:
        if not isinstance(entry, dict):
            raise LedgerError(f"{name}: each [[reviewed]] entry must be a table")
        extra = sorted(set(entry) - _ROW_KEYS)
        if extra:
            raise LedgerError(f"{name}: [[reviewed]] carries forbidden key(s) {extra}")
        missing = sorted(_ROW_KEYS - set(entry))
        if missing:
            raise LedgerError(f"{name}: [[reviewed]] is missing required key(s) {missing}")
        row_id = entry["id"]
        if not isinstance(row_id, str) or not row_id:
            raise LedgerError(f"{name}: [[reviewed]] id must be a non-empty string")
        if row_id in seen:
            raise LedgerError(f"{name}: duplicate [[reviewed]] id {row_id!r}")
        seen.add(row_id)
        for key in ("source_digest", "target_digest"):
            value = entry[key]
            if not isinstance(value, str) or not _DIGEST_RE.match(value):
                raise LedgerError(f"{name}: {row_id}: {key} must be 64 lowercase hex characters")
        disposition = entry["disposition"]
        if disposition not in DISPOSITIONS:
            raise LedgerError(
                f"{name}: {row_id}: disposition {disposition!r} is not one of {list(DISPOSITIONS)}"
            )
        rows.append(
            ReviewedRow(row_id, entry["source_digest"], entry["target_digest"], disposition)
        )
    return rows


# ── previous committed ledger ─────────────────────────────────────────────────────────────────


def previous_ledger(rel_path: str, cwd: str | Path) -> dict | None:
    """``git show HEAD:./<rel_path>`` — the previous COMMITTED ledger, or ``None``.

    This copies the SHAPE of ``tools/contract_drift/drift.py:129-147`` (fixed argv, ``shell=False``,
    the ``HEAD:./`` prefix, degrade-to-``None``) but NOT the function. ``_git_show_at`` calls
    ``json.loads`` on its stdout and catches ``json.JSONDecodeError``; the ledger is TOML, so it
    cannot be imported and reused here. The two divergences are deliberate and are the only
    differences: ``tomllib.loads(stdout.decode("utf-8"))`` replaces ``json.loads``, and the except
    tuple widens to cover ``tomllib.TOMLDecodeError`` and ``UnicodeDecodeError``.

    The ``./`` prefix is load-bearing and is kept verbatim: a bare ``HEAD:<path>`` always resolves
    against the REPO ROOT and ignores ``cwd``, which would silently read the wrong tree.

    Degrading to ``None`` never raises into the gate (T-28-22). ``None`` means "history is
    UNREADABLE" — a different fact from "history is readable but lacks this row", and
    :func:`check_coherence` keeps the two apart because their remedies differ.
    """
    try:
        proc = subprocess.run(
            ["git", "show", f"HEAD:./{rel_path}"],
            cwd=str(cwd),
            capture_output=True,
            check=True,
            shell=False,
        )
        return tomllib.loads(proc.stdout.decode("utf-8"))
    except (
        subprocess.CalledProcessError,
        tomllib.TOMLDecodeError,
        UnicodeDecodeError,
        OSError,
    ):
        return None


# ── the coherence rule ────────────────────────────────────────────────────────────────────────


def check_coherence(
    rows: Sequence[ReviewedRow],
    previous: dict | None,
    live_digests: Mapping[str, tuple[str, str]],
    bindings: Mapping[str, str],
) -> list[Finding]:
    """Return the sorted incoherence findings for ``rows`` (DOCSUP-03).

    ``previous`` is the parsed previous COMMITTED ledger (or ``None``), ``live_digests`` maps a
    binding id to its live ``(source, target)`` digest pair, and ``bindings`` maps a binding id to
    its severity (``"required"`` / ``"advisory"``). The live binding COUNT is ``len(bindings)``.

    Pure: touches no filesystem, spawns no process, decides no exit code.
    """
    previous_rows = _previous_rows(previous)
    findings: list[Finding] = []

    for row in rows:
        severity = bindings.get(row.id)
        if severity is None:
            # Blessing a binding that does not exist (research Q5 corollary): the ledger row would
            # otherwise sit there as inert, unexaminable green.
            findings.append(
                Finding(
                    row.id,
                    REASON_UNKNOWN_BINDING,
                    LEVEL_FAIL,
                    f"{REASON_UNKNOWN_BINDING}: ledger row {row.id} has no binding in the registry",
                )
            )
            continue
        level = LEVEL_FAIL if severity == "required" else LEVEL_WARN

        if row.disposition == "SUPERSEDING_ADR_REQUIRED":
            # An OPEN OBLIGATION, regardless of digest equality (D-09). If it could set FRESH it
            # would be a rubber stamp with extra syllables — the obligation is discharged by
            # landing a superseding ADR and re-dispositioning, never by the digests agreeing.
            findings.append(
                Finding(
                    row.id,
                    REASON_OPEN_OBLIGATION,
                    level,
                    f"{REASON_OPEN_OBLIGATION}: binding {row.id} carries an open obligation — "
                    f"land a superseding ADR; never edit the accepted one in place",
                )
            )
            continue

        live = live_digests[row.id]
        if (row.source_digest, row.target_digest) != live:
            # Ordinary staleness. Kept as its OWN reason so it is tellable apart from
            # `disposition-incoherent`: same "digests disagree" symptom, different fix.
            findings.append(
                Finding(
                    row.id,
                    REASON_STALE,
                    level,
                    f"{REASON_STALE}: binding {row.id} was reviewed at digests that no longer "
                    f"match the working tree",
                )
            )
            continue

        if row.disposition in CONTENT_BOUND_DISPOSITIONS:
            findings.extend(_check_content_bound(row, previous, previous_rows, level))
            continue

        findings.extend(_check_updated(row, previous, previous_rows, level))

    findings.extend(_check_binding_count(previous, len(bindings)))
    return sorted(findings)


def _check_content_bound(
    row: ReviewedRow, previous: dict | None, previous_rows: dict[str, dict], level: str
) -> list[Finding]:
    """D-04 half 1 plus its self-green closure.

    Half 1 is CONTENT-BOUND and therefore HISTORY-FREE: a ``reviewed-no-change`` row is valid
    exactly when both stored digests equal the live ones, which the caller has already established
    before reaching here. That is correct for an EXISTING binding, and it is why ``previous is
    None`` returns green — a tree with no ``HEAD`` can still verify this claim in full.

    But it opens a hole for a BRAND-NEW binding (Phase-29 researcher finding, T-28-16b). An agent
    can land a new ``[[binding]]`` and, in the same change, a ``reviewed-no-change`` row carrying
    that binding's exact live digests. The row is consistent by construction and there is nothing
    in history to contradict it, so half 1 as originally written reports it FRESH — an agent
    self-blessing a binding.

    ``first_seen-unratified`` closes it, and it is deliberately a HISTORY test rather than a
    content test: the self-blessed row and an honest first-ever seed row are BYTE-IDENTICAL, so
    "has a human committed this row before?" is the only fact that separates them. The consequence
    is intended, not a defect — a genuinely new binding is amber for exactly one commit cycle, and
    the human review that lands the ledger row IS the ratification.
    """
    if previous is None:
        return []  # history-free by design; the unreadable-history case belongs to `updated`
    if row.id in previous_rows:
        return []
    return [
        Finding(
            row.id,
            REASON_FIRST_SEEN,
            level,
            f"{REASON_FIRST_SEEN}: binding {row.id} has no previously committed [[reviewed]] row "
            f"— a binding cannot be blessed in the same change that introduces it",
        )
    ]


def _check_updated(
    row: ReviewedRow, previous: dict | None, previous_rows: dict[str, dict], level: str
) -> list[Finding]:
    """D-04 half 2 — the paste-the-live-digest control (T-28-16).

    Digests ALONE cannot detect the attack: paste the live source digest into the ledger, write
    ``disposition = "updated"``, leave the target document untouched, and the stored and live
    digests agree by construction. Only the previous COMMITTED ledger records what the target
    looked like BEFORE, so only a comparison against it can see that the target never moved.

    ``previous is None`` (history unreadable) and "readable history that lacks this row" are kept
    in separate branches on purpose. Both are unverifiable, but the remedies differ — the first is
    a checkout/fetch problem, the second means the claim has never been ratified — so the message
    distinguishes them even though they share the ``unverified-disposition`` reason (D-08).
    """
    if previous is None:
        return [
            Finding(
                row.id,
                REASON_UNVERIFIED,
                level,
                f"{REASON_UNVERIFIED}: binding {row.id} claims 'updated' but no previous committed "
                f"ledger could be read — the claim cannot be verified",
            )
        ]
    prior = previous_rows.get(row.id)
    if prior is None:
        return [
            Finding(
                row.id,
                REASON_UNVERIFIED,
                level,
                f"{REASON_UNVERIFIED}: binding {row.id} claims 'updated' but has no row in the "
                f"previous committed ledger to have been updated FROM",
            )
        ]
    source_moved = prior.get("source_digest") != row.source_digest
    target_moved = prior.get("target_digest") != row.target_digest
    if source_moved and not target_moved:
        return [
            Finding(
                row.id,
                REASON_INCOHERENT,
                level,
                f"{REASON_INCOHERENT}: binding {row.id} claims 'updated' but its target digest is "
                f"unchanged since the previous committed ledger — the document was never touched",
            )
        ]
    return []


def _check_binding_count(previous: dict | None, live_count: int) -> list[Finding]:
    """The ``[coverage] binding_min`` ratchet (T-28-17b).

    NOT redundant with ``uncovered_max``. A binding whose TARGET lies outside D-07's human corpus
    can be deleted without moving the uncovered count by a single unit, so deleting an inconvenient
    binding would otherwise be entirely unguarded — the registry could be quietly emptied of every
    row that was about to fail.

    The threshold is read from the PREVIOUS COMMITTED ledger, never from the working tree: reading
    it from the working tree would let the same edit that deletes the binding also lower the bar.
    Unreadable history means no check at all, which is the same posture ``previous is None`` takes
    everywhere else in this module. Like ``uncovered_max``, the guard NEVER writes it — raising or
    tightening it is a human edit (D-06).
    """
    if previous is None:
        return []
    minimum = previous.get("coverage", {}).get("binding_min")
    if not isinstance(minimum, int) or isinstance(minimum, bool):
        return []
    if live_count < minimum:
        return [
            Finding(
                "",  # registry-wide, not attributable to a single binding
                REASON_BINDING_COUNT,
                LEVEL_FAIL,
                f"{REASON_BINDING_COUNT}: the registry has {live_count} binding(s) but the "
                f"committed ratchet requires binding_min = {minimum}",
            )
        ]
    if live_count > minimum:
        return [
            Finding(
                "",
                REASON_BINDING_COUNT_TIGHTEN,
                LEVEL_NOTE,
                f"ratchet can tighten: set binding_min = {live_count}",
            )
        ]
    return []


def _previous_rows(previous: dict | None) -> dict[str, dict]:
    """Index the previous committed ledger's rows by id.

    Deliberately LENIENT where :func:`load_ledger` is strict: this is committed history, already
    past the gate once, and re-validating it here would let a historical shape change fail a
    present-day review. Malformed entries are simply not indexed.
    """
    if previous is None:
        return {}
    block = previous.get("reviewed", [])
    if not isinstance(block, list):
        return {}
    return {
        entry["id"]: entry
        for entry in block
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
