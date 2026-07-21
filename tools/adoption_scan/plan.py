"""plan.py — the D-02 evidence classification ladder, D-05 question-record generation, and
relationship-candidate emission in the ``adoption/`` namespace (ADOPT-02).

Pure over an already-built inventory (:func:`tools.adoption_scan.scan.build_inventory`) — this
module NEVER touches the filesystem, NEVER computes a new content hash, and NEVER re-reads the
scanned target. Every evidence pointer it emits is copied verbatim from an already-hashed
``inventory["included"]``-derived record; this is a structural consequence of D-10 (an excluded
file, e.g. one excluded as ``secret-content``, carries no ``sha256`` anywhere in the inventory, so
``plan.py`` has no way to cite one as evidence — and does not try to; see 26-RESEARCH.md Pitfall 7).

The bright line (26-RESEARCH.md "Evidence Classification Ladder"): this module may NEVER write an
``authority`` value into a relationship record from inference. A relationship whose authority is
unresolved is emitted as a `relationship-authority` QUESTION (with the partial candidate attached,
schema-incompletely — no ``authority`` key), never as a `relationshipCandidate` with a guessed
authority. :func:`generate_relationship_candidates` enforces this structurally: it only ever reads
a proposal's own ``classification`` field, never derives one from a question's ``candidate``.

Internal "relationship" proposal target convention (this module's own, not part of any schema):
``"<contract>::<authority-or-?>-><dependent>"`` — mirrors the D-05-recommended
``adoption/<contract>/<authority>-><dependent>`` id shape without the ``adoption/`` prefix, so a
resolved-authority proposal and its emitted candidate share a legible id lineage. The inventory
shape produced by Plan 02's ``scan.py``/``detect.py`` carries no relationship/contract signal of
its own today (out of ADOPT-01 scope) — :func:`classify` therefore never manufactures a
``"relationship"``-kind proposal from a real inventory; the gating logic below exists so that a
future inventory extension (or a hand-authored proposal) is safely handled, honoring "never
invented authority" even when the upstream signal source changes.
"""

from __future__ import annotations

import hashlib
from pathlib import PurePosixPath

# proposalRecord.kind -> questionRecord.kind (ADOPT-02 category list -> D-05 kind enum).
_QUESTION_KIND_BY_PROPOSAL_KIND: dict[str, str] = {
    "member": "member-boundary",
    "component": "component-boundary",
    "relationship": "relationship-authority",
    "contract-candidate": "contract-candidate",
    "test-command": "test-command",
    "docs-destination": "docs-destination",
    "agents-boundary": "agents-boundary",
    "codeowners": "codeowners-ownership",
}

# D-05 group bucket per question kind (render-time grouping, coarse).
_GROUP_BY_QUESTION_KIND: dict[str, str] = {
    "relationship-authority": "topology",
    "contract-candidate": "topology",
    "component-boundary": "topology",
    "member-boundary": "topology",
    "test-command": "testing",
    "docs-destination": "docs",
    "agents-boundary": "docs",
    "codeowners-ownership": "ownership",
    "collision": "collision",
    "ambiguous-language": "language",
    "excluded-file": "security",
}

# Kinds ADOPT-06/Phase-27 requires an answer to before apply (26-RESEARCH.md D-05).
_BLOCKING_KINDS: frozenset[str] = frozenset(
    {
        "relationship-authority",
        "component-boundary",
        "member-boundary",
        "codeowners-ownership",
        "collision",
    }
)

_UNRESOLVED_AUTHORITY = "?"


def _question_id(kind: str, target: str) -> str:
    """D-05: content-derived, stable across re-runs — never derived from list position."""
    digest = hashlib.sha256((kind + "\x00" + target).encode("utf-8")).hexdigest()[:12]
    return f"Q-{digest}"


def _question_text(kind: str, target: str) -> str:
    templates: dict[str, str] = {
        "member-boundary": f"Is '{target}' a workspace member, and if so under which name?",
        "component-boundary": f"Is the directory '{target}' one component, or should it split?",
        "relationship-authority": f"Which endpoint is the authority for '{target}'?",
        "contract-candidate": f"Should '{target}' be tracked as a contract?",
        "test-command": f"Which command is the canonical test entrypoint for '{target}'?",
        "docs-destination": f"Which Diataxis quadrant does '{target}' belong to?",
        "agents-boundary": f"Is the existing AGENTS.md at '{target}' nearest-wins-correct?",
        "codeowners-ownership": f"Who owns the CODEOWNERS path '{target}'?",
        "collision": f"'{target}' collides with another included file by content — which wins?",
        "ambiguous-language": f"Multiple languages observed ({target}) — which is primary?",
        "excluded-file": f"'{target}' was excluded from the scan — how should it be handled?",
    }
    return templates.get(kind, f"Please resolve: {target}")


def classify(inventory: dict) -> list[dict]:
    """Walk ``inventory["manifests"]`` + the four surface arrays and produce
    ``proposalRecord``-shaped entries (D-02 evidence ladder).

    ``observed`` is used ONLY as a direct restatement of an already-``observed`` source record
    (a manifest literally declares a candidate workspace member). ``inferred`` mirrors
    ``candidate_process_boundaries`` verbatim (already ``inferred`` with a ``rationale`` — D-02:
    component/member existence is inherently inferred, never observed). Everything else —
    doc/AGENTS destination placement, which test command is canonical — is ``unknown``: these are
    ownership/placement decisions D-02 explicitly reserves for a human question, never an
    auto-promoted inference.

    ``inventory["languages"]`` is deliberately NOT walked into a proposal here — no proposal kind
    in the ADOPT-02 category list corresponds to raw language presence; a multi-language signal is
    instead surfaced directly as an ``ambiguous-language`` question in :func:`generate_questions`.
    """
    proposals: list[dict] = []

    for entry in inventory.get("manifests", []):
        proposals.append(
            {
                "id": f"member/{entry['path']}",
                "kind": "member",
                "classification": entry["classification"],  # direct restatement -> observed
                "target": entry["path"],
                "evidence": entry["evidence"],
                "rationale": f"manifest:{entry['kind']}",
            }
        )

    for entry in inventory.get("candidate_process_boundaries", []):
        record = {
            "id": f"component/{entry['target']}",
            "kind": "component",
            "classification": entry["classification"],  # mirrored verbatim -> inferred
            "target": entry["target"],
            "evidence": entry["evidence"],
        }
        if "rationale" in entry:
            record["rationale"] = entry["rationale"]
        proposals.append(record)

    for entry in inventory.get("documentation_surfaces", []):
        # WR-01: detect.py now emits one surfaceRecord per distinct AGENTS.md PATH (root AND every
        # nested one), so `target` is a real path like "libs/python/AGENTS.md", not the fixed
        # literal "AGENTS.md" — match by filename, not exact-string-equality, so every nested
        # AGENTS.md still gets its own per-file agents-boundary proposal/question.
        kind = (
            "agents-boundary"
            if PurePosixPath(entry["target"]).name == "AGENTS.md"
            else "docs-destination"
        )
        proposals.append(
            {
                "id": f"{kind}/{entry['target']}",
                "kind": kind,
                "classification": "unknown",  # placement/nearest-wins is an ownership question
                "target": entry["target"],
                "evidence": entry["evidence"],
            }
        )

    for entry in inventory.get("ci_surfaces", []):
        proposals.append(
            {
                "id": f"test-command/{entry['target']}",
                "kind": "test-command",
                "classification": "unknown",  # a CI surface existing != a canonical command
                "target": entry["target"],
                "evidence": entry["evidence"],
            }
        )

    for entry in inventory.get("test_surfaces", []):
        proposals.append(
            {
                "id": f"test-command/{entry['target']}",
                "kind": "test-command",
                "classification": "unknown",
                "target": entry["target"],
                "evidence": entry["evidence"],
            }
        )

    for entry in inventory.get("codeowners_surfaces", []):
        proposals.append(
            {
                "id": f"codeowners/{entry['target']}",
                "kind": "codeowners",
                # ALWAYS unknown — who owns a CODEOWNERS path is an ownership/authority claim
                # D-02 reserves for a question, never a restatement of the source's "observed".
                "classification": "unknown",
                "target": entry["target"],
                "evidence": entry["evidence"],
            }
        )

    for entry in inventory.get("schema_surfaces", []):
        # WR-05: detect_schema_surfaces() returns AT MOST ONE surfaceRecord per repo (target =
        # the fixed "contracts/**/*.schema.json" literal), whose evidence list has one entry per
        # matching schema file — so we walk entry["evidence"] (not the outer list) to emit ONE
        # contract-candidate proposal PER SCHEMA FILE.
        for ref in entry["evidence"]:
            proposals.append(
                {
                    "id": f"contract-candidate/{ref['path']}",
                    "kind": "contract-candidate",
                    # ALWAYS unknown — whether a schema is a tracked, ratified contract is a
                    # human/CODEOWNERS-gated decision, never inferred from file existence alone.
                    "classification": "unknown",
                    "target": ref["path"],
                    "evidence": [ref],
                }
            )

    proposals.sort(key=lambda item: item["id"])
    return proposals


def _parse_relationship_target(target: str) -> tuple[str, str, str]:
    """Parse this module's own ``"<contract>::<authority-or-?>-><dependent>"`` target convention."""
    contract, rest = target.split("::", 1)
    authority, dependent = rest.split("->", 1)
    return contract, authority, dependent


def generate_questions(inventory: dict, proposals: list[dict]) -> list[dict]:
    """Emit a ``questionRecord`` for every ``unknown``-classified proposal, plus one
    ``ambiguous-language`` question when the inventory observed more than one language.

    Sorted by ``(group, kind, target, id)`` — total because ``id`` is unique by construction
    (content-derived from ``kind`` + ``target``).
    """
    questions: list[dict] = []

    for proposal in proposals:
        if proposal["classification"] != "unknown":
            continue
        kind = _QUESTION_KIND_BY_PROPOSAL_KIND.get(proposal["kind"])
        if kind is None:
            continue
        target = proposal["target"]
        question: dict = {
            "id": _question_id(kind, target),
            "kind": kind,
            "group": _GROUP_BY_QUESTION_KIND.get(kind, "general"),
            "target": target,
            "question": _question_text(kind, target),
            "classification": "unknown",
            "evidence": proposal["evidence"],
            "blocking": kind in _BLOCKING_KINDS,
        }
        if proposal["kind"] == "relationship":
            contract, authority, dependent = _parse_relationship_target(target)
            if authority == _UNRESOLVED_AUTHORITY:
                question["candidate"] = {
                    "record_kind": "relationshipCandidate",
                    "record": {
                        "id": f"adoption/{contract}/?->{dependent}",
                        "contract": contract,
                        "dependents": [dependent],
                    },
                }
        questions.append(question)

    languages = inventory.get("languages", [])
    if len(languages) > 1:
        names = sorted(lang["name"] for lang in languages)
        target = ",".join(names)
        evidence: list[dict] = []
        seen_paths: set[str] = set()
        for lang in sorted(languages, key=lambda item: item["name"]):
            for ref in lang["evidence"]:
                if ref["path"] in seen_paths:
                    continue
                seen_paths.add(ref["path"])
                evidence.append(ref)
        evidence.sort(key=lambda ref: ref["path"])
        questions.append(
            {
                "id": _question_id("ambiguous-language", target),
                "kind": "ambiguous-language",
                "group": _GROUP_BY_QUESTION_KIND["ambiguous-language"],
                "target": target,
                "question": _question_text("ambiguous-language", target),
                "classification": "unknown",
                "evidence": evidence,
                "blocking": "ambiguous-language" in _BLOCKING_KINDS,
            }
        )

    questions.sort(key=lambda q: (q.get("group", ""), q["kind"], q["target"], q["id"]))
    return questions


def generate_relationship_candidates(inventory: dict, proposals: list[dict]) -> list[dict]:
    """Emit a ``relationshipCandidate`` ONLY when a proposal's own ``classification`` is
    ``observed`` or ``inferred`` (never ``unknown``) — an unresolved-authority relationship is
    NEVER emitted here (see :func:`generate_questions` instead). Namespaced
    ``adoption/<contract>/<authority>-><dependent>`` (distinct from ``effective_relationships()``'s
    existing ``pipeline/`` namespace).
    """
    candidates: list[dict] = []
    for proposal in proposals:
        if proposal["kind"] != "relationship":
            continue
        if proposal["classification"] not in ("observed", "inferred"):
            continue
        contract, authority, dependent = _parse_relationship_target(proposal["target"])
        if not authority or authority == _UNRESOLVED_AUTHORITY:
            # Structural guard — never invent authority even if misclassified upstream.
            continue
        candidates.append(
            {
                "id": f"adoption/{contract}/{authority}->{dependent}",
                "contract": contract,
                "authority": authority,
                "dependents": [dependent],
            }
        )

    candidates.sort(key=lambda item: item["id"])
    return candidates


def build_plan(inventory: dict) -> dict:
    """Assemble the ``plan.schema.json``-conformant document."""
    proposals = classify(inventory)
    relationships = generate_relationship_candidates(inventory, proposals)
    questions = generate_questions(inventory, proposals)
    return {
        "target_ref": inventory["target_ref"],
        "proposals": proposals,
        "relationships": relationships,
        "questions": questions,
    }
