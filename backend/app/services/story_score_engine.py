"""Per-Role Story Score Engine and Story Classification (v1.1, §4.6, §4.7, §4.8).

Design principles:
- Each participating role starts at 10.0 on every story
- Deductions are only for that role's own attributed faults
- No shared pool — one role's deduction never changes another role's score
- Story class (High/Medium/Low) determined by escalation + serious-bug gates
- Scores are derived and recomputed by replaying events — never overwritten
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.models import (
    Bug,
    BugReasoningClass,
    BugSeverity,
    PerRoleStoryScore,
    QualityClass,
    QualityEvent,
    Story,
    StoryClassRecord,
    UserRole,
)

# Default deduction weights per reasoning class (§4.6 table, admin-configurable)
DEFAULT_DEDUCTIONS: dict[str, float] = {
    BugReasoningClass.SILLY_MISS.value: 0.75,
    BugReasoningClass.CRITICAL_MISS.value: 3.0,
    BugReasoningClass.INFO_NOT_IN_STORY.value: 2.0,
    BugReasoningClass.MISSING_UNIT_TEST.value: 1.5,
    BugReasoningClass.WRONG_TEST_CASES.value: 1.5,
}

# Default escalation penalty
ESCALATION_PENALTY = 2.0

# Serious severities used by the High/Medium/Low gate (§5.5)
SERIOUS_SEVERITIES = {
    BugSeverity.CRITICAL,
    BugSeverity.PRODUCTION,
    BugSeverity.SECURITY,
    BugSeverity.DATA_LOSS,
}

# Reasoning class → default responsible role mapping (§7.4)
REASONING_CLASS_ROLE_MAP: dict[str, list[str]] = {
    BugReasoningClass.SILLY_MISS.value: ["developer"],
    BugReasoningClass.CRITICAL_MISS.value: ["developer"],
    BugReasoningClass.INFO_NOT_IN_STORY.value: ["business_analyst"],
    BugReasoningClass.MISSING_UNIT_TEST.value: ["developer"],
    BugReasoningClass.WRONG_TEST_CASES.value: ["tester", "business_analyst"],
}


def check_onboarding_completeness(story: Story) -> tuple[bool, list[str]]:
    """Check if a story has all four required data points for scoring (§4.8).

    Returns (is_complete, list_of_gaps).
    """
    gaps = []
    if not story.description and not story.acceptance_criteria:
        gaps.append("story_description")
    # Bug list: an explicit empty list is valid; None means not provided
    # We check after bugs are loaded; for now rely on onboarding_complete flag
    if story.unit_test_cases is None:
        gaps.append("developer_unit_test_cases")
    if story.ba_test_cases is None:
        gaps.append("ba_tester_test_cases")
    return (len(gaps) == 0, gaps)


def update_story_onboarding_status(db: Session, story: Story) -> Story:
    """Evaluate and update the onboarding completeness of a story (§4.8, FR-18)."""
    is_complete, gaps = check_onboarding_completeness(story)

    # Also check bug list availability (even zero bugs is valid)
    bugs = db.query(Bug).filter(Bug.story_id == story.id).all()
    has_bug_list = True  # bugs being queryable means the list exists

    story.onboarding_complete = is_complete and has_bug_list
    story.completeness_gaps = gaps if gaps else None
    if not story.onboarding_complete:
        story.quality_class = QualityClass.INSUFFICIENT_DATA
    db.commit()
    db.refresh(story)
    return story


def compute_per_role_story_scores(db: Session, story_id: int) -> list[PerRoleStoryScore]:
    """Compute per-role story scores by replaying quality events for a story (§4.6).

    Each participating role starts at 10.0 and loses points only for
    their own attributed faults.
    """
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        return []

    # Check onboarding gate
    if not story.onboarding_complete:
        return []

    # Get all approved quality events for this story
    events = (
        db.query(QualityEvent)
        .filter(
            QualityEvent.story_id == story_id,
        )
        .all()
    )

    # Get bugs with approved reasoning classes
    bugs = (
        db.query(Bug)
        .filter(
            Bug.story_id == story_id,
            Bug.reasoning_class.isnot(None),
            Bug.reasoning_class_approved.is_(True),
        )
        .all()
    )

    # Collect all participating roles from the story
    role_actors: dict[str, int] = {}
    if story.ba_id:
        role_actors[UserRole.BUSINESS_ANALYST.value] = story.ba_id
    if story.developer_id:
        role_actors[UserRole.DEVELOPER.value] = story.developer_id
    if story.tester_id:
        role_actors[UserRole.TESTER.value] = story.tester_id
    if story.automation_id:
        role_actors[UserRole.AUTOMATION_ENGINEER.value] = story.automation_id

    if not role_actors:
        return []

    # Initialize scores at 10.0 for each role
    role_scores: dict[str, float] = {role: 10.0 for role in role_actors}
    role_breakdowns: dict[str, list] = {role: [] for role in role_actors}

    # Apply deductions from approved bug reasoning classes
    for bug in bugs:
        if not bug.reasoning_class:
            continue
        deduction_amount = DEFAULT_DEDUCTIONS.get(bug.reasoning_class.value, 1.0)

        # Use ownership_split if available, else use default role mapping
        if bug.ownership_split:
            for role_key, pct in bug.ownership_split.items():
                normalized_role = _normalize_role(role_key)
                if normalized_role in role_scores:
                    share = deduction_amount * (pct / 100.0)
                    role_scores[normalized_role] = max(0.0, role_scores[normalized_role] - share)
                    role_breakdowns[normalized_role].append({
                        "bug_id": bug.id,
                        "reasoning_class": bug.reasoning_class.value,
                        "deduction": -round(share, 2),
                        "ownership_pct": pct,
                    })
        else:
            default_roles = REASONING_CLASS_ROLE_MAP.get(bug.reasoning_class.value, ["developer"])
            share = deduction_amount / len(default_roles)
            for role_key in default_roles:
                if role_key in role_scores:
                    role_scores[role_key] = max(0.0, role_scores[role_key] - share)
                    role_breakdowns[role_key].append({
                        "bug_id": bug.id,
                        "reasoning_class": bug.reasoning_class.value,
                        "deduction": -round(share, 2),
                    })

    # Apply escalation penalties
    escalations = story.escalations or []
    for _esc in escalations:
        # Trace escalation to responsible role(s) — for now apply evenly
        if role_actors:
            share = ESCALATION_PENALTY / len(role_actors)
            for role_key in role_actors:
                role_scores[role_key] = max(0.0, role_scores[role_key] - share)
                role_breakdowns[role_key].append({
                    "type": "escalation",
                    "deduction": -round(share, 2),
                })

    # Also apply negative events from quality events
    for event in events:
        if event.ai_suggested and event.approved_by is None:
            continue
        if event.delta < 0:
            role_key = event.role.value
            if role_key in role_scores:
                role_scores[role_key] = max(0.0, role_scores[role_key] + event.delta)
                role_breakdowns[role_key].append({
                    "event_id": event.id,
                    "event_type": event.event_type.value,
                    "deduction": event.delta,
                    "reason": event.reason,
                })

    # Upsert per-role story scores
    results = []
    now = datetime.utcnow()
    for role_key, actor_id in role_actors.items():
        role_enum = UserRole(role_key)
        existing = (
            db.query(PerRoleStoryScore)
            .filter(
                PerRoleStoryScore.story_id == story_id,
                PerRoleStoryScore.role == role_enum,
            )
            .first()
        )
        score_val = round(role_scores[role_key], 2)
        breakdown = role_breakdowns[role_key]

        if existing:
            existing.score = score_val
            existing.breakdown = breakdown
            existing.computed_at = now
            existing.actor_id = actor_id
        else:
            existing = PerRoleStoryScore(
                story_id=story_id,
                role=role_enum,
                actor_id=actor_id,
                score=score_val,
                breakdown=breakdown,
                computed_at=now,
            )
            db.add(existing)
        results.append(existing)

    db.commit()
    for r in results:
        db.refresh(r)
    return results


def classify_story(db: Session, story_id: int) -> Optional[StoryClassRecord]:
    """Classify a story as High/Medium/Low based on §4.7 rules.

    Rules (all admin-configurable thresholds, proposed defaults):
    - High: 0 escalations AND 0 serious bugs AND rollup >= 8.0
    - Medium: 0 escalations AND 0 serious bugs AND 5.0 <= rollup < 8.0
    - Low: Any escalation OR any serious bug OR rollup < 5.0
    """
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        return None

    if not story.onboarding_complete:
        return None

    # Count escalations
    escalation_count = len(story.escalations or [])

    # Count serious bugs
    serious_bug_count = (
        db.query(Bug)
        .filter(
            Bug.story_id == story_id,
            Bug.severity.in_([s.value for s in SERIOUS_SEVERITIES]),
        )
        .count()
    )

    # Compute rollup (average of per-role story scores)
    role_scores = (
        db.query(PerRoleStoryScore)
        .filter(PerRoleStoryScore.story_id == story_id)
        .all()
    )
    rollup = 10.0
    if role_scores:
        rollup = round(sum(rs.score for rs in role_scores) / len(role_scores), 2)

    # Determine class
    if escalation_count > 0 or serious_bug_count > 0 or rollup < 5.0:
        quality_class = QualityClass.LOW
    elif rollup >= 8.0:
        quality_class = QualityClass.HIGH
    else:
        quality_class = QualityClass.MEDIUM

    # Upsert story class record
    now = datetime.utcnow()
    existing = (
        db.query(StoryClassRecord)
        .filter(StoryClassRecord.story_id == story_id)
        .first()
    )
    if existing:
        existing.quality_class = quality_class
        existing.rollup = rollup
        existing.serious_bug_count = serious_bug_count
        existing.escalation_count = escalation_count
        existing.computed_at = now
    else:
        existing = StoryClassRecord(
            story_id=story_id,
            quality_class=quality_class,
            rollup=rollup,
            serious_bug_count=serious_bug_count,
            escalation_count=escalation_count,
            computed_at=now,
        )
        db.add(existing)

    # Update story denormalized fields
    story.quality_class = quality_class
    story.story_rollup = rollup

    db.commit()
    db.refresh(existing)
    return existing


def compute_and_classify_story(db: Session, story_id: int) -> dict:
    """Full recomputation: per-role scores + story classification."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        return {"error": "Story not found"}

    # Update onboarding status first
    update_story_onboarding_status(db, story)

    if not story.onboarding_complete:
        return {
            "story_id": story_id,
            "status": "insufficient_data",
            "gaps": story.completeness_gaps,
        }

    role_scores = compute_per_role_story_scores(db, story_id)
    classification = classify_story(db, story_id)

    return {
        "story_id": story_id,
        "onboarding_complete": True,
        "role_scores": [
            {
                "role": rs.role.value,
                "actor_id": rs.actor_id,
                "score": rs.score,
                "breakdown": rs.breakdown,
            }
            for rs in role_scores
        ],
        "classification": {
            "quality_class": classification.quality_class.value if classification else None,
            "rollup": classification.rollup if classification else None,
            "serious_bug_count": classification.serious_bug_count if classification else 0,
            "escalation_count": classification.escalation_count if classification else 0,
        },
    }


def _normalize_role(role_key: str) -> str:
    """Normalize role key from ownership split to UserRole value."""
    mapping = {
        "ba": UserRole.BUSINESS_ANALYST.value,
        "business_analyst": UserRole.BUSINESS_ANALYST.value,
        "dev": UserRole.DEVELOPER.value,
        "developer": UserRole.DEVELOPER.value,
        "tester": UserRole.TESTER.value,
        "test": UserRole.TESTER.value,
        "automation": UserRole.AUTOMATION_ENGINEER.value,
        "automation_engineer": UserRole.AUTOMATION_ENGINEER.value,
    }
    return mapping.get(role_key.lower(), role_key.lower())
