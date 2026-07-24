"""Trend analytics and module risk view endpoints (Phase 3, Design Spec §10.3).

Provides:
- Quality trends over time per module, team, bug category
- Module risk assessment view
- Auto-badge evaluation based on quality facts
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, case, extract
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    Badge,
    Bug,
    BugSeverity,
    BugStatus,
    DetectedStage,
    OriginStage,
    QualityEvent,
    RoleScore,
    RootCauseCategory,
    Story,
    StoryStatus,
    User,
    UserBadge,
    UserRole,
)

router = APIRouter(prefix="/trends", tags=["trends"])


# --- Trend Analytics (Phase 3, Design Spec §10.3) ---


@router.get("/quality-over-time")
def get_quality_trends(
    project_id: int | None = Query(None),
    module: str | None = Query(None),
    granularity: str = Query("month", description="day, week, or month"),
    months: int = Query(6, description="Number of months to look back"),
    db: Session = Depends(get_db),
):
    """Quality trend lines over time (§10.3).

    Shows quality metrics grouped by time period for trend visualization.
    Supports filtering by project/module and different time granularities.
    """
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    # Build base query for bugs with time filtering
    bug_query = db.query(Bug).filter(Bug.created_date >= cutoff)
    if project_id:
        bug_query = bug_query.join(Story, Story.id == Bug.story_id).filter(
            Story.project_id == project_id
        )
    if module:
        bug_query = bug_query.join(Story, Story.id == Bug.story_id).filter(
            Story.module == module
        )

    # Build base query for quality events
    event_query = db.query(QualityEvent).filter(QualityEvent.created_at >= cutoff)
    if project_id:
        event_query = event_query.join(
            Story, Story.id == QualityEvent.story_id
        ).filter(Story.project_id == project_id)

    # Group bugs by time period
    if granularity == "day":
        time_group = func.date(Bug.created_date)
        event_time_group = func.date(QualityEvent.created_at)
    elif granularity == "week":
        time_group = func.strftime("%Y-W%W", Bug.created_date)
        event_time_group = func.strftime("%Y-W%W", QualityEvent.created_at)
    else:  # month
        time_group = func.strftime("%Y-%m", Bug.created_date)
        event_time_group = func.strftime("%Y-%m", QualityEvent.created_at)

    # Bug trend
    bug_trend = (
        db.query(time_group.label("period"), func.count(Bug.id).label("bug_count"))
        .filter(Bug.created_date >= cutoff)
    )
    if project_id:
        bug_trend = bug_trend.join(Story, Story.id == Bug.story_id).filter(
            Story.project_id == project_id
        )
    if module:
        bug_trend = bug_trend.join(Story, Story.id == Bug.story_id).filter(
            Story.module == module
        )
    bug_trend = bug_trend.group_by("period").order_by("period").all()

    # Quality event trend (positive vs negative)
    positive_trend_query = (
        db.query(
            event_time_group.label("period"),
            func.count(QualityEvent.id).label("count"),
        )
        .filter(QualityEvent.created_at >= cutoff, QualityEvent.delta > 0)
    )
    if project_id:
        positive_trend_query = positive_trend_query.join(
            Story, Story.id == QualityEvent.story_id
        ).filter(Story.project_id == project_id)
    positive_trend = positive_trend_query.group_by("period").order_by("period").all()

    negative_trend_query = (
        db.query(
            event_time_group.label("period"),
            func.count(QualityEvent.id).label("count"),
        )
        .filter(QualityEvent.created_at >= cutoff, QualityEvent.delta < 0)
    )
    if project_id:
        negative_trend_query = negative_trend_query.join(
            Story, Story.id == QualityEvent.story_id
        ).filter(Story.project_id == project_id)
    negative_trend = negative_trend_query.group_by("period").order_by("period").all()

    # Merge into unified timeline
    periods = sorted(
        set(
            [r.period for r in bug_trend]
            + [r.period for r in positive_trend]
            + [r.period for r in negative_trend]
        )
    )

    bug_map = {r.period: r.bug_count for r in bug_trend}
    pos_map = {r.period: r.count for r in positive_trend}
    neg_map = {r.period: r.count for r in negative_trend}

    timeline = []
    for period in periods:
        timeline.append({
            "period": period,
            "bugs": bug_map.get(period, 0),
            "positive_events": pos_map.get(period, 0),
            "negative_events": neg_map.get(period, 0),
        })

    return {"timeline": timeline, "granularity": granularity, "months": months}


@router.get("/bug-category-trend")
def get_bug_category_trend(
    project_id: int | None = Query(None),
    months: int = Query(6),
    db: Session = Depends(get_db),
):
    """Bug category trends over time (§10.3 trend lines per bug category)."""
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    query = db.query(
        func.strftime("%Y-%m", Bug.created_date).label("period"),
        Bug.root_cause_category,
        func.count(Bug.id).label("count"),
    ).filter(Bug.created_date >= cutoff)

    if project_id:
        query = query.join(Story, Story.id == Bug.story_id).filter(
            Story.project_id == project_id
        )

    results = query.group_by("period", Bug.root_cause_category).order_by("period").all()

    # Group by period
    trend_data: dict[str, dict[str, int]] = {}
    for period, category, count in results:
        if period not in trend_data:
            trend_data[period] = {}
        cat_name = category.value if category else "uncategorized"
        trend_data[period][cat_name] = count

    timeline = [
        {"period": period, **categories}
        for period, categories in sorted(trend_data.items())
    ]

    return {"timeline": timeline, "months": months}


@router.get("/severity-trend")
def get_severity_trend(
    project_id: int | None = Query(None),
    months: int = Query(6),
    db: Session = Depends(get_db),
):
    """Bug severity trends over time."""
    cutoff = datetime.utcnow() - timedelta(days=months * 30)

    query = db.query(
        func.strftime("%Y-%m", Bug.created_date).label("period"),
        Bug.severity,
        func.count(Bug.id).label("count"),
    ).filter(Bug.created_date >= cutoff)

    if project_id:
        query = query.join(Story, Story.id == Bug.story_id).filter(
            Story.project_id == project_id
        )

    results = query.group_by("period", Bug.severity).order_by("period").all()

    trend_data: dict[str, dict[str, int]] = {}
    for period, severity, count in results:
        if period not in trend_data:
            trend_data[period] = {}
        trend_data[period][severity.value] = count

    timeline = [
        {"period": period, **severities}
        for period, severities in sorted(trend_data.items())
    ]

    return {"timeline": timeline, "months": months}


# --- Module Risk View (Phase 3, Design Spec §10.3) ---


@router.get("/module-risk")
def get_module_risk_view(
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Module risk assessment view (Phase 3).

    For each module, calculates a composite risk score based on:
    - Total bug count and density
    - Critical/high severity bug proportion
    - Escaped defect count (production bugs)
    - Recent trend direction (improving or worsening)
    - Unresolved bug count
    """
    # Get all modules
    module_query = db.query(Story.module).distinct()
    if project_id:
        module_query = module_query.filter(Story.project_id == project_id)
    modules = [m[0] for m in module_query.all() if m[0]]

    if not modules:
        return {"modules": [], "summary": {"total_modules": 0}}

    results = []
    for mod in modules:
        # Total stories in module
        story_query = db.query(Story).filter(Story.module == mod)
        if project_id:
            story_query = story_query.filter(Story.project_id == project_id)
        story_ids = [s.id for s in story_query.all()]
        total_stories = len(story_ids)

        if not story_ids:
            continue

        # Bug metrics
        bugs = db.query(Bug).filter(Bug.story_id.in_(story_ids)).all()
        total_bugs = len(bugs)
        bug_density = total_bugs / total_stories if total_stories > 0 else 0

        # Severity breakdown
        critical_high = sum(
            1
            for b in bugs
            if b.severity
            in [BugSeverity.CRITICAL, BugSeverity.HIGH, BugSeverity.PRODUCTION]
        )
        production_bugs = sum(
            1 for b in bugs if b.severity == BugSeverity.PRODUCTION
        )

        # Unresolved bugs
        unresolved = sum(
            1
            for b in bugs
            if b.status in [BugStatus.OPEN, BugStatus.IN_PROGRESS, BugStatus.REOPENED]
        )

        # Recent trend (last 30 days vs previous 30 days)
        now = datetime.utcnow()
        recent_cutoff = now - timedelta(days=30)
        older_cutoff = now - timedelta(days=60)

        recent_bugs = sum(
            1
            for b in bugs
            if b.created_date and b.created_date >= recent_cutoff
        )
        older_bugs = sum(
            1
            for b in bugs
            if b.created_date
            and older_cutoff <= b.created_date < recent_cutoff
        )

        if older_bugs > 0:
            trend_direction = ((recent_bugs - older_bugs) / older_bugs) * 100
        elif recent_bugs > 0:
            trend_direction = 100.0  # New bugs appearing, no baseline
        else:
            trend_direction = 0.0

        # Compute risk score (0-100)
        risk_score = 0.0
        risk_score += min(bug_density * 15, 30)  # Bug density component
        risk_score += min((critical_high / total_stories) * 40, 25) if total_stories > 0 else 0
        risk_score += min(production_bugs * 10, 20)  # Production defects
        risk_score += min(unresolved * 5, 15)  # Unresolved backlog
        risk_score += min(max(trend_direction, 0) * 0.1, 10)  # Worsening trend
        risk_score = min(round(risk_score, 1), 100)

        # Risk level
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 40:
            risk_level = "high"
        elif risk_score >= 20:
            risk_level = "medium"
        else:
            risk_level = "low"

        results.append({
            "module": mod,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "total_stories": total_stories,
            "total_bugs": total_bugs,
            "bug_density": round(bug_density, 2),
            "critical_high_bugs": critical_high,
            "production_bugs": production_bugs,
            "unresolved_bugs": unresolved,
            "trend_direction": round(trend_direction, 1),
            "trend_label": (
                "worsening" if trend_direction > 10
                else "improving" if trend_direction < -10
                else "stable"
            ),
        })

    # Sort by risk score descending
    results.sort(key=lambda x: x["risk_score"], reverse=True)

    return {
        "modules": results,
        "summary": {
            "total_modules": len(results),
            "critical_modules": sum(1 for r in results if r["risk_level"] == "critical"),
            "high_modules": sum(1 for r in results if r["risk_level"] == "high"),
        },
    }


# --- Auto-Badge Evaluation (Phase 3, FR-14) ---


@router.post("/badges/evaluate/{user_id}")
def evaluate_badges(
    user_id: int,
    period: str = Query(..., description="Period to evaluate, e.g. '2026-07'"),
    db: Session = Depends(get_db),
):
    """Automatically evaluate and award badges based on quality facts (FR-14).

    Evaluates predefined badge criteria against actual quality events
    and awards badges when criteria are met. Every badge includes evidence.
    """
    awarded = []

    # Get user's events for the period
    events = (
        db.query(QualityEvent)
        .filter(
            QualityEvent.actor_id == user_id,
            func.strftime("%Y-%m", QualityEvent.created_at).like(f"{period}%"),
        )
        .all()
    )

    if not events:
        return {"user_id": user_id, "period": period, "badges_awarded": []}

    # Get user's stories
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"user_id": user_id, "period": period, "badges_awarded": []}

    positive_events = [e for e in events if e.delta > 0]
    negative_events = [e for e in events if e.delta < 0]

    # Badge criteria evaluations
    badge_evaluations = [
        {
            "name": "Zero-Bug Champion",
            "description": "Delivered stories with zero defects",
            "criteria": "zero_defect_story events >= 3",
            "check": lambda: sum(
                1 for e in events if e.event_type.value == "zero_defect_story"
            ) >= 3,
            "evidence": lambda: {
                "zero_defect_stories": sum(
                    1 for e in events if e.event_type.value == "zero_defect_story"
                ),
                "story_ids": [
                    e.story_id
                    for e in events
                    if e.event_type.value == "zero_defect_story"
                ],
            },
        },
        {
            "name": "Edge-Case Hunter",
            "description": "Found critical edge cases before production",
            "criteria": "edge_case_found or boundary_issue_found events >= 3",
            "check": lambda: sum(
                1
                for e in events
                if e.event_type.value in ("edge_case_found", "boundary_issue_found")
            ) >= 3,
            "evidence": lambda: {
                "edge_cases_found": sum(
                    1
                    for e in events
                    if e.event_type.value in ("edge_case_found", "boundary_issue_found")
                ),
            },
        },
        {
            "name": "Code Guardian",
            "description": "Consistently high code review pass rate",
            "criteria": "first_time_right_review events >= 5",
            "check": lambda: sum(
                1
                for e in events
                if e.event_type.value == "first_time_right_review"
            ) >= 5,
            "evidence": lambda: {
                "first_time_passes": sum(
                    1
                    for e in events
                    if e.event_type.value == "first_time_right_review"
                ),
            },
        },
        {
            "name": "Automation Hero",
            "description": "High automation coverage and stability",
            "criteria": "regression_automated + stable_scripts + high_coverage >= 4",
            "check": lambda: sum(
                1
                for e in events
                if e.event_type.value
                in ("regression_automated", "stable_scripts", "high_coverage")
            ) >= 4,
            "evidence": lambda: {
                "automation_events": sum(
                    1
                    for e in events
                    if e.event_type.value
                    in ("regression_automated", "stable_scripts", "high_coverage")
                ),
            },
        },
        {
            "name": "Quality Champion",
            "description": "Overwhelmingly positive quality contributions",
            "criteria": "positive events > 2x negative events and >= 10 positive",
            "check": lambda: (
                len(positive_events) >= 10
                and len(positive_events) > 2 * len(negative_events)
            ),
            "evidence": lambda: {
                "positive_events": len(positive_events),
                "negative_events": len(negative_events),
                "ratio": round(
                    len(positive_events) / max(len(negative_events), 1), 1
                ),
            },
        },
        {
            "name": "Security Sentinel",
            "description": "Found security issues before production",
            "criteria": "security_issue_found or security_improvement >= 2",
            "check": lambda: sum(
                1
                for e in events
                if e.event_type.value
                in ("security_issue_found", "security_improvement")
            ) >= 2,
            "evidence": lambda: {
                "security_contributions": sum(
                    1
                    for e in events
                    if e.event_type.value
                    in ("security_issue_found", "security_improvement")
                ),
            },
        },
        {
            "name": "Requirement Master",
            "description": "Consistently complete and clear requirements",
            "criteria": "complete_acceptance_criteria + well_documented_story >= 5",
            "check": lambda: sum(
                1
                for e in events
                if e.event_type.value
                in ("complete_acceptance_criteria", "well_documented_story", "edge_cases_covered")
            ) >= 5,
            "evidence": lambda: {
                "quality_requirement_events": sum(
                    1
                    for e in events
                    if e.event_type.value
                    in ("complete_acceptance_criteria", "well_documented_story", "edge_cases_covered")
                ),
            },
        },
    ]

    for badge_eval in badge_evaluations:
        if badge_eval["check"]():
            # Check if badge type exists, create if not
            badge = (
                db.query(Badge).filter(Badge.name == badge_eval["name"]).first()
            )
            if not badge:
                badge = Badge(
                    name=badge_eval["name"],
                    description=badge_eval["description"],
                    criteria={"rule": badge_eval["criteria"]},
                )
                db.add(badge)
                db.flush()

            # Check if already awarded for this period
            existing = (
                db.query(UserBadge)
                .filter(
                    UserBadge.user_id == user_id,
                    UserBadge.badge_id == badge.id,
                    UserBadge.period == period,
                )
                .first()
            )
            if not existing:
                evidence = badge_eval["evidence"]()
                user_badge = UserBadge(
                    user_id=user_id,
                    badge_id=badge.id,
                    period=period,
                    evidence=[evidence],
                )
                db.add(user_badge)
                awarded.append({
                    "badge_name": badge_eval["name"],
                    "badge_id": badge.id,
                    "evidence": evidence,
                })

    if awarded:
        db.commit()

    return {
        "user_id": user_id,
        "period": period,
        "badges_awarded": awarded,
        "total_events_analyzed": len(events),
    }


@router.get("/score-trend/{user_id}")
def get_user_score_trend(
    user_id: int,
    role: UserRole | None = Query(None),
    db: Session = Depends(get_db),
):
    """Get a user's score progression over time (role dashboard trend)."""
    query = db.query(RoleScore).filter(RoleScore.actor_id == user_id)
    if role:
        query = query.filter(RoleScore.role == role)

    scores = query.order_by(RoleScore.period).all()

    return [
        {
            "period": s.period,
            "role": s.role.value,
            "score": s.computed_value,
            "module": s.module,
        }
        for s in scores
    ]
