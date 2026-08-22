from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.models.evidence import Evidence
from backend.app.models.rule import Rule
from backend.app.services.rule_service import (
    get_run_evidence,
    list_rules,
)


def _normalise(value: str) -> str:
    return " ".join(value.lower().split())


def _requirement_terms(requirement: str) -> list[str]:
    """
    Extract useful searchable terms from a human-written requirement.

    This is intentionally deterministic for Phase 15.
    Semantic/LLM evaluation comes later.
    """
    text = _normalise(requirement)

    patterns = [
        r"must contain (.+)",
        r"should contain (.+)",
        r"contains (.+)",
        r"must include (.+)",
        r"should include (.+)",
        r"include (.+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text)

        if match:
            return [match.group(1).strip()]

    return [text]


def evaluate_rule_against_evidence(
    rule: Rule,
    evidence: list[Evidence],
) -> dict:
    requirement = _normalise(rule.requirement)

    if not requirement:
        return {
            "rule_id": rule.id,
            "status": "inconclusive",
            "explanation": "The rule has no requirement.",
            "evidence_ids": [],
        }

    terms = _requirement_terms(requirement)

    matched: list[Evidence] = []

    for item in evidence:
        searchable = _normalise(
            f"{item.claim} {item.excerpt}"
        )

        if any(term in searchable for term in terms):
            matched.append(item)

    if matched:
        return {
            "rule_id": rule.id,
            "status": "pass",
            "explanation": (
                "The requirement is supported by evidence "
                "from the run's documents."
            ),
            "evidence_ids": [
                item.id for item in matched
            ],
        }

    if evidence:
        return {
            "rule_id": rule.id,
            "status": "fail",
            "explanation": (
                "The available document evidence does not "
                "support the rule requirement."
            ),
            "evidence_ids": [],
        }

    return {
        "rule_id": rule.id,
        "status": "inconclusive",
        "explanation": (
            "No document evidence is available yet, so "
            "the rule cannot be evaluated."
        ),
        "evidence_ids": [],
    }


def _evaluate_rule_against_text(
    rule: Rule,
    document_texts: list[str],
) -> dict:
    """
    Evaluate a rule directly against extracted document text.

    This is the fallback path used when persisted Evidence
    records have not yet been generated.
    """
    requirement = _normalise(rule.requirement)

    if not requirement:
        return {
            "rule_id": rule.id,
            "status": "inconclusive",
            "explanation": "The rule has no requirement.",
            "evidence_ids": [],
        }

    if not document_texts:
        return {
            "rule_id": rule.id,
            "status": "inconclusive",
            "explanation": (
                "No document content is available yet, so "
                "the rule cannot be evaluated."
            ),
            "evidence_ids": [],
        }

    terms = _requirement_terms(requirement)

    for text in document_texts:
        searchable = _normalise(text)

        if any(term in searchable for term in terms):
            return {
                "rule_id": rule.id,
                "status": "pass",
                "explanation": (
                    "The requirement is supported by the "
                    "run's extracted document content."
                ),
                "evidence_ids": [],
            }

    return {
        "rule_id": rule.id,
        "status": "fail",
        "explanation": (
            "The available document content does not "
            "support the rule requirement."
        ),
        "evidence_ids": [],
    }


def evaluate_run_rules(
    db: Session,
    run_id: UUID,
) -> list[dict]:
    rules = list_rules(db, run_id)
    evidence = get_run_evidence(db, run_id)

    # Prefer persisted evidence when it exists.
    if not evidence:
        documents = list(
            db.scalars(
                select(Document)
                .where(Document.run_id == run_id)
            ).all()
        )

        generated_evidence: list[Evidence] = []

        for document in documents:
            if not document.extracted_text:
                continue

            evidence_item = Evidence(
                document_id=document.id,
                claim=document.extracted_text,
                excerpt=document.extracted_text,
            )

            db.add(evidence_item)
            generated_evidence.append(evidence_item)

        if generated_evidence:
            db.commit()

            for item in generated_evidence:
                db.refresh(item)

            evidence = generated_evidence

    return [
        evaluate_rule_against_evidence(
            rule,
            evidence,
        )
        for rule in rules
    ]