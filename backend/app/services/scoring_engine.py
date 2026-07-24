from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.schemas import Bug, BugStatus, DetectionStage, QualityEvent, RoleScore, Story, StoryStatus, User, UserRole

SEVERITY_WEIGHTS = {
    "Informational": 0.5,
    "Cosmetic": 1.0,
    "General": 2.0,
    "Medium": 3.5,
    "High": 5.0,
    "Critical": 7.5,
    "Production": 8.0,
    "Security": 8.5,
    "Performance": 6.0,
    "Data loss": 9.0,
}

DETECTION_BONUS = {
    "Requirement": 1.0,
    "Development": 0.9,
    "Code Review": 1.35,
    "Testing": 1.15,
    "Automation": 1.2,
    "UAT": 0.8,
    "Release": 0.65,
    "Production": 0.35,
}

DETECTOR_ROLE_FACTOR = {
    UserRole.BUSINESS_ANALYST: 0.8,
    UserRole.DEVELOPER: 0.9,
    UserRole.TESTER: 1.1,
    UserRole.AUTOMATION_ENGINEER: 1.0,
}

ROLE_PENALTY_FACTOR = {
    UserRole.BUSINESS_ANALYST: 1.0,
    UserRole.DEVELOPER: 1.2,
    UserRole.TESTER: 1.0,
    UserRole.AUTOMATION_ENGINEER: 0.85,
}

STORY_COMPLETION_BONUS = {
    UserRole.BUSINESS_ANALYST: 1.8,
    UserRole.DEVELOPER: 2.2,
    UserRole.TESTER: 1.6,
    UserRole.AUTOMATION_ENGINEER: 1.4,
}

EARLY_DELIVERY_BONUS = {
    UserRole.BUSINESS_ANALYST: 0.4,
    UserRole.DEVELOPER: 0.8,
}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _severity_weight(value) -> float:
    return SEVERITY_WEIGHTS[str(value.value if hasattr(value, "value") else value)]


def _detection_bonus(stage) -> float:
    return DETECTION_BONUS[str(stage.value if hasattr(stage, "value") else stage)]


def _normalise_role(raw_role: str | UserRole) -> UserRole | None:
    if isinstance(raw_role, UserRole):
        return raw_role
    mapping = {
        "BA": UserRole.BUSINESS_ANALYST,
        "Business Analyst": UserRole.BUSINESS_ANALYST,
        "Developer": UserRole.DEVELOPER,
        "Tester": UserRole.TESTER,
        "Automation": UserRole.AUTOMATION_ENGINEER,
        "Automation Engineer": UserRole.AUTOMATION_ENGINEER,
        "Engineering Manager": UserRole.ENGINEERING_MANAGER,
        "Admin": UserRole.ADMIN,
    }
    return mapping.get(raw_role)


def _story_actor_id(story: Story, role: UserRole) -> int | None:
    if role == UserRole.BUSINESS_ANALYST:
        return story.ba_id
    if role == UserRole.DEVELOPER:
        return story.developer_id
    if role == UserRole.TESTER:
        return story.tester_id
    if role == UserRole.AUTOMATION_ENGINEER:
        return story.automation_id
    return None


def _has_event(db: Session, source_ref: str) -> bool:
    return db.scalar(select(QualityEvent.id).where(QualityEvent.source_ref == source_ref).limit(1)) is not None


def append_quality_event(
    db: Session,
    *,
    actor_id: int,
    role: UserRole,
    event_type: str,
    delta: float,
    reason: str,
    source_ref: str,
    story: Story | None = None,
    bug: Bug | None = None,
    approved_by_id: int | None = None,
    ai_suggested: bool = False,
    details: dict | None = None,
    created_at: datetime | None = None,
) -> QualityEvent:
    event = QualityEvent(
        actor_id=actor_id,
        role=role,
        event_type=event_type,
        delta=round(delta, 2),
        reason=reason,
        source_ref=source_ref,
        ai_suggested=ai_suggested,
        approved_by_id=approved_by_id,
        details=details or {},
        created_at=created_at or _utcnow(),
        story_id=story.id if story else None,
        bug_id=bug.id if bug else None,
        project_id=(story.project_id if story else bug.project_id if bug else None),
        sprint_id=(story.sprint_id if story else bug.sprint_id if bug else None),
        module=(story.module if story else bug.module if bug else None),
    )
    db.add(event)
    return event


def sync_story_quality_events(db: Session, story: Story) -> None:
    if story.status not in {StoryStatus.DONE, StoryStatus.RELEASED}:
        return
    event_date = datetime.combine(story.completion_date or story.estimated_date or _utcnow().date(), datetime.min.time(), tzinfo=timezone.utc)
    for role, bonus in STORY_COMPLETION_BONUS.items():
        actor_id = _story_actor_id(story, role)
        if actor_id is None:
            continue
        source_ref = f"story:{story.id}:completion:{role.value}"
        if _has_event(db, source_ref):
            continue
        append_quality_event(
            db,
            actor_id=actor_id,
            role=role,
            event_type="story_completed",
            delta=bonus,
            reason=f"Delivered story {story.story_key} in module {story.module}",
            source_ref=source_ref,
            story=story,
            created_at=event_date,
            details={"story_key": story.story_key},
        )
    if story.estimated_date and story.completion_date and story.completion_date <= story.estimated_date:
        for role, bonus in EARLY_DELIVERY_BONUS.items():
            actor_id = _story_actor_id(story, role)
            if actor_id is None:
                continue
            source_ref = f"story:{story.id}:early:{role.value}"
            if _has_event(db, source_ref):
                continue
            append_quality_event(
                db,
                actor_id=actor_id,
                role=role,
                event_type="early_delivery",
                delta=bonus,
                reason=f"Story {story.story_key} completed on or before estimate",
                source_ref=source_ref,
                story=story,
                created_at=event_date,
                details={"story_key": story.story_key},
            )


def _bug_is_scoreable(bug: Bug) -> bool:
    return not bug.ai_suggested or bug.human_approved_by_id is not None


def sync_bug_quality_events(db: Session, bug: Bug) -> None:
    story = bug.story or db.scalar(select(Story).where(Story.id == bug.story_id))
    created_at = bug.created_date or _utcnow()
    if bug.detected_by_id is not None:
        detector = bug.detected_by or db.get(User, bug.detected_by_id)
        if detector and detector.role in DETECTOR_ROLE_FACTOR:
            source_ref = f"bug:{bug.id}:detection:{bug.detected_by_id}"
            if not _has_event(db, source_ref):
                delta = _severity_weight(bug.severity) * 0.35 * _detection_bonus(bug.detected_stage) * DETECTOR_ROLE_FACTOR[detector.role]
                append_quality_event(
                    db,
                    actor_id=bug.detected_by_id,
                    role=detector.role,
                    event_type="bug_detected",
                    delta=delta,
                    reason=f"Detected {bug.severity.value} bug {bug.bug_key} during {bug.detected_stage.value}",
                    source_ref=source_ref,
                    story=story,
                    bug=bug,
                    created_at=created_at,
                    details={"severity": bug.severity.value, "detected_stage": bug.detected_stage.value},
                )
    if _bug_is_scoreable(bug) and story is not None:
        for raw_role, share in (bug.ownership_split or {}).items():
            role = _normalise_role(raw_role)
            if role not in ROLE_PENALTY_FACTOR:
                continue
            actor_id = _story_actor_id(story, role)
            if actor_id is None:
                continue
            source_ref = f"bug:{bug.id}:ownership:{role.value}:{actor_id}"
            if _has_event(db, source_ref):
                continue
            delta = -1 * _severity_weight(bug.severity) * float(share) * ROLE_PENALTY_FACTOR[role]
            append_quality_event(
                db,
                actor_id=actor_id,
                role=role,
                event_type="bug_root_cause_assigned",
                delta=delta,
                reason=f"RCA for {bug.bug_key}: {bug.root_cause or bug.root_cause_category.value}",
                source_ref=source_ref,
                story=story,
                bug=bug,
                approved_by_id=bug.human_approved_by_id,
                ai_suggested=bool(bug.ai_suggested),
                created_at=bug.human_approved_at or created_at,
                details={
                    "share": float(share),
                    "severity": bug.severity.value,
                    "origin_stage": bug.origin_stage.value,
                    "root_cause_category": bug.root_cause_category.value,
                },
            )
    if bug.status in {BugStatus.RESOLVED, BugStatus.CLOSED} and bug.assigned_to_id is not None:
        assignee = bug.assigned_to or db.get(User, bug.assigned_to_id)
        if assignee and assignee.role in DETECTOR_ROLE_FACTOR:
            source_ref = f"bug:{bug.id}:resolution:{bug.assigned_to_id}"
            if not _has_event(db, source_ref):
                delta = _severity_weight(bug.severity) * 0.15
                append_quality_event(
                    db,
                    actor_id=bug.assigned_to_id,
                    role=assignee.role,
                    event_type="bug_resolved",
                    delta=delta,
                    reason=f"Resolved {bug.severity.value} bug {bug.bug_key}",
                    source_ref=source_ref,
                    story=story,
                    bug=bug,
                    created_at=bug.closed_date or _utcnow(),
                    details={"severity": bug.severity.value},
                )


def recompute_role_scores(
    db: Session,
    *,
    period: str = "all-time",
    window_days: int | None = None,
    actor_id: int | None = None,
    module: str | None = None,
) -> list[RoleScore]:
    now = _utcnow()
    since = now - timedelta(days=window_days) if window_days else None
    query = select(QualityEvent).options(selectinload(QualityEvent.actor))
    if since is not None:
        query = query.where(QualityEvent.created_at >= since)
    if actor_id is not None:
        query = query.where(QualityEvent.actor_id == actor_id)
    if module is not None:
        query = query.where(QualityEvent.module == module)
    events = list(db.scalars(query).all())

    if actor_id is None and module is None:
        db.execute(delete(RoleScore).where(RoleScore.period == period))
    elif actor_id is not None:
        db.execute(delete(RoleScore).where(RoleScore.period == period, RoleScore.actor_id == actor_id))
    elif module is not None:
        db.execute(delete(RoleScore).where(RoleScore.period == period, RoleScore.module == module))

    aggregates: dict[tuple[int, UserRole, str | None], dict] = defaultdict(lambda: {"score": 0.0, "events": [], "types": defaultdict(float)})
    for event in events:
        overall_key = (event.actor_id, event.role, None)
        module_key = (event.actor_id, event.role, event.module) if event.module else None
        for key in (overall_key, module_key):
            if key is None:
                continue
            aggregates[key]["score"] += event.delta
            aggregates[key]["events"].append(event)
            aggregates[key]["types"][event.event_type] += event.delta

    created_scores: list[RoleScore] = []
    for (score_actor_id, role, score_module), payload in aggregates.items():
        ordered_types = sorted(payload["types"].items(), key=lambda item: abs(item[1]), reverse=True)
        breakdown = {
            "event_count": len(payload["events"]),
            "top_event_types": [{"label": label, "value": round(value, 2)} for label, value in ordered_types[:5]],
            "recent_sources": [event.source_ref for event in sorted(payload["events"], key=lambda item: item.created_at, reverse=True)[:5]],
        }
        score = RoleScore(
            actor_id=score_actor_id,
            role=role,
            period=period,
            module=score_module,
            computed_value=round(payload["score"], 2),
            breakdown=breakdown,
            start_date=since.date() if since else None,
            end_date=now.date(),
        )
        db.add(score)
        created_scores.append(score)
    db.commit()
    for score in created_scores:
        db.refresh(score)
    return created_scores


def fetch_leaderboard(
    db: Session,
    *,
    role: UserRole | None = None,
    module: str | None = None,
    limit: int = 10,
    period: str = "all-time",
) -> list[RoleScore]:
    if not db.scalar(select(RoleScore.id).limit(1)):
        recompute_role_scores(db, period=period)
    query = (
        select(RoleScore)
        .where(RoleScore.period == period, RoleScore.module.is_(module) if module is None else RoleScore.module == module)
        .options(selectinload(RoleScore.actor))
    )
    if role is not None:
        query = query.where(RoleScore.role == role)
    scores = list(db.scalars(query).all())
    scores = [score for score in scores if score.actor and score.actor.role == score.role and score.actor.role in {
        UserRole.DEVELOPER,
        UserRole.BUSINESS_ANALYST,
        UserRole.TESTER,
        UserRole.AUTOMATION_ENGINEER,
    }]
    scores.sort(key=lambda item: item.computed_value, reverse=True)
    return scores[:limit]


def recent_events_for_user(db: Session, user_id: int, limit: int = 20) -> Iterable[QualityEvent]:
    query = (
        select(QualityEvent)
        .where(QualityEvent.actor_id == user_id)
        .order_by(QualityEvent.created_at.desc())
        .limit(limit)
        .options(selectinload(QualityEvent.actor))
    )
    return db.scalars(query).all()
