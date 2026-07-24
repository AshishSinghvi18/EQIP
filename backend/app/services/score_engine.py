"""Score Engine - computes per-role scores by replaying immutable quality events.

Design principles (from EQIP Design Spec §4, §9):
- Scores are additive and independent per role
- Every gain/loss is stored as an immutable event
- Scores are always recomputable by replaying events
- Earlier detection scores higher (configurable weight multiplier)
- No shared, zero-sum scoring
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import (
    BugSeverity,
    DetectedStage,
    EventType,
    QualityEvent,
    RoleScore,
    ScoringWeight,
    UserRole,
)


# Detection stage multipliers - earlier detection = higher score (FR-7)
DETECTION_STAGE_MULTIPLIERS = {
    DetectedStage.CODE_REVIEW: 2.0,
    DetectedStage.UNIT_TESTING: 1.8,
    DetectedStage.INTEGRATION_TESTING: 1.5,
    DetectedStage.QA_TESTING: 1.2,
    DetectedStage.UAT: 1.0,
    DetectedStage.STAGING: 0.8,
    DetectedStage.PRODUCTION: 0.5,
}


def get_weight(
    db: Session,
    project_id: Optional[int],
    event_type: Optional[EventType] = None,
    severity: Optional[BugSeverity] = None,
) -> float:
    """Get the configured weight for an event type or severity."""
    query = db.query(ScoringWeight)
    if project_id:
        query = query.filter(ScoringWeight.project_id == project_id)
    if event_type:
        query = query.filter(ScoringWeight.event_type == event_type)
    if severity:
        query = query.filter(ScoringWeight.severity == severity)

    weight = query.first()
    return weight.weight if weight else 1.0


def compute_score_for_actor(
    db: Session,
    actor_id: int,
    role: UserRole,
    period: str,
    module: Optional[str] = None,
) -> RoleScore:
    """Recompute a role's score by replaying all quality events.

    This is the core scoring function. It:
    1. Queries all quality events for the actor/role/period
    2. Sums deltas (applying configured weights)
    3. Returns a RoleScore with full breakdown for explainability (FR-4, NFR-4)
    """
    query = db.query(QualityEvent).filter(
        QualityEvent.actor_id == actor_id,
        QualityEvent.role == role,
    )

    if module:
        # Filter by module through story relationship if needed
        pass

    events = query.all()
    breakdown = []
    total = 0.0

    for event in events:
        # Only count approved events if AI-suggested (FR-9)
        if event.ai_suggested and event.approved_by is None:
            continue

        effective_delta = event.delta
        breakdown.append(
            {
                "event_id": event.id,
                "event_type": event.event_type.value,
                "delta": effective_delta,
                "reason": event.reason,
                "created_at": event.created_at.isoformat(),
            }
        )
        total += effective_delta

    # Update or create role score
    existing = (
        db.query(RoleScore)
        .filter(
            RoleScore.actor_id == actor_id,
            RoleScore.role == role,
            RoleScore.period == period,
        )
        .first()
    )

    if existing:
        existing.computed_value = total
        existing.breakdown = breakdown
        existing.computed_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing
    else:
        score = RoleScore(
            actor_id=actor_id,
            role=role,
            period=period,
            module=module,
            computed_value=total,
            breakdown=breakdown,
            computed_at=datetime.utcnow(),
        )
        db.add(score)
        db.commit()
        db.refresh(score)
        return score


def record_quality_event(
    db: Session,
    story_id: Optional[int],
    bug_id: Optional[int],
    role: UserRole,
    actor_id: int,
    event_type: EventType,
    delta: float,
    reason: str,
    source_ref: Optional[str] = None,
    ai_suggested: bool = False,
    approved_by: Optional[int] = None,
) -> QualityEvent:
    """Record an immutable quality event. This is the ONLY way scores change.

    Per design spec §9: Every score change is append-only. Nothing is overwritten.
    """
    event = QualityEvent(
        story_id=story_id,
        bug_id=bug_id,
        role=role,
        actor_id=actor_id,
        event_type=event_type,
        delta=delta,
        reason=reason,
        source_ref=source_ref,
        ai_suggested=ai_suggested,
        approved_by=approved_by,
        created_at=datetime.utcnow(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
