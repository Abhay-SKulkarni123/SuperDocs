from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.conflict import Conflict
from backend.app.models.finding import Finding
from backend.app.models.rule import Rule
from backend.app.services.rule_evaluation import evaluate_run_rules


def list_findings(
    db: Session,
    run_id: UUID,
) -> list[Finding]:
    statement = (
        select(Finding)
        .where(Finding.run_id == run_id)
        .order_by(Finding.created_at.asc())
    )

    return list(db.scalars(statement).all())


def generate_findings(
    db: Session,
    run_id: UUID,
) -> list[Finding]:
    """
    Generate review findings from conflicts and failed rules.

    Finding generation is idempotent: an existing finding for the
    same source will not be created again.
    """

    findings: list[Finding] = []

    existing = list_findings(db, run_id)

    existing_sources = {
        (finding.source_type, finding.source_id)
        for finding in existing
    }

    # ---------------------------------------------------------
    # Conflicts -> findings
    # ---------------------------------------------------------
    conflicts = list(
        db.scalars(
            select(Conflict)
            .where(Conflict.run_id == run_id)
            .order_by(Conflict.created_at.asc())
        ).all()
    )

    for conflict in conflicts:
        source_key = ("conflict", conflict.id)

        if source_key in existing_sources:
            continue

        finding = Finding(
            run_id=run_id,
            type="conflict",
            title=conflict.title,
            description=conflict.description,
            severity=conflict.severity,
            status="open",
            source_type="conflict",
            source_id=conflict.id,
        )

        db.add(finding)
        existing_sources.add(source_key)
        findings.append(finding)

    # ---------------------------------------------------------
    # Failed rules -> findings
    # ---------------------------------------------------------
    evaluations = evaluate_run_rules(db, run_id)

    rules = list(
        db.scalars(
            select(Rule)
            .where(Rule.run_id == run_id)
            .order_by(Rule.created_at.asc())
        ).all()
    )

    rules_by_id = {
        rule.id: rule
        for rule in rules
    }

    for evaluation in evaluations:
        if evaluation["status"] != "fail":
            continue

        rule_id = evaluation["rule_id"]
        rule = rules_by_id.get(rule_id)

        if rule is None:
            continue

        source_key = ("rule_failure", rule.id)

        if source_key in existing_sources:
            continue

        finding = Finding(
            run_id=run_id,
            type="rule_failure",
            title=rule.name,
            description=evaluation["explanation"],
            severity=rule.severity,
            status="open",
            source_type="rule",
            source_id=rule.id,
        )

        db.add(finding)
        existing_sources.add(source_key)
        findings.append(finding)

    if findings:
        db.commit()

        for finding in findings:
            db.refresh(finding)

    return findings


def resolve_finding(
    db: Session,
    finding: Finding,
) -> Finding:
    finding.status = "resolved"
    finding.resolved_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(finding)

    return finding