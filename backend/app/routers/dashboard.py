"""Dashboard endpoints for quality metrics and drill-down (FR-12, FR-13)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    Bug,
    BugSeverity,
    QualityEvent,
    RoleScore,
    Story,
    UserRole,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def get_quality_summary(
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Executive quality dashboard cards (§10.1)."""
    story_query = db.query(Story)
    bug_query = db.query(Bug)

    if project_id:
        story_query = story_query.filter(Story.project_id == project_id)
    if sprint_id:
        story_query = story_query.filter(Story.sprint_id == sprint_id)

    total_stories = story_query.count()
    total_bugs = bug_query.count()

    # Zero-bug stories
    stories_with_bugs = (
        db.query(Bug.story_id).filter(Bug.story_id.isnot(None)).distinct().count()
    )
    zero_bug_stories = total_stories - stories_with_bugs if total_stories > 0 else 0

    # Production defects
    production_defects = bug_query.filter(
        Bug.severity == BugSeverity.PRODUCTION
    ).count()

    # Severity breakdown
    severity_breakdown = (
        db.query(Bug.severity, func.count(Bug.id))
        .group_by(Bug.severity)
        .all()
    )

    return {
        "total_stories": total_stories,
        "total_bugs": total_bugs,
        "zero_bug_stories": zero_bug_stories,
        "zero_bug_percentage": (
            round(zero_bug_stories / total_stories * 100, 1) if total_stories > 0 else 0
        ),
        "production_defects": production_defects,
        "severity_breakdown": {s.value: c for s, c in severity_breakdown},
    }


@router.get("/module-heatmap")
def get_module_heatmap(
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Module heatmap - defect density per module (§10.2 drill-down start)."""
    query = (
        db.query(Story.module, func.count(Bug.id).label("bug_count"))
        .join(Bug, Bug.story_id == Story.id, isouter=True)
        .group_by(Story.module)
    )
    if project_id:
        query = query.filter(Story.project_id == project_id)

    results = query.all()
    return [
        {"module": module or "Unassigned", "bug_count": count}
        for module, count in results
    ]


@router.get("/bug-type-breakdown")
def get_bug_type_breakdown(
    module: str | None = Query(None),
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Bug type breakdown for a module (§10.2 drill-down level 2)."""
    query = db.query(Bug.root_cause_category, func.count(Bug.id))
    if module:
        query = query.join(Story, Story.id == Bug.story_id).filter(Story.module == module)
    if project_id:
        query = query.join(Story, Story.id == Bug.story_id).filter(
            Story.project_id == project_id
        )
    results = query.group_by(Bug.root_cause_category).all()
    total = sum(c for _, c in results)
    return [
        {
            "category": cat.value if cat else "uncategorized",
            "count": count,
            "percentage": round(count / total * 100, 1) if total > 0 else 0,
        }
        for cat, count in results
    ]


@router.get("/root-cause-breakdown")
def get_root_cause_breakdown(
    category: str | None = Query(None),
    module: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Root cause breakdown (§10.2 drill-down level 3)."""
    query = db.query(Bug.origin_stage, func.count(Bug.id))
    if category:
        query = query.filter(Bug.root_cause_category == category)
    if module:
        query = query.join(Story, Story.id == Bug.story_id).filter(Story.module == module)
    results = query.group_by(Bug.origin_stage).all()
    total = sum(c for _, c in results)
    return [
        {
            "origin_stage": stage.value if stage else "unknown",
            "count": count,
            "percentage": round(count / total * 100, 1) if total > 0 else 0,
        }
        for stage, count in results
    ]


@router.get("/leaderboard")
def get_leaderboard(
    role: UserRole = Query(...),
    period: str = Query(...),
    limit: int = Query(10),
    db: Session = Depends(get_db),
):
    """Leaderboard with facts (FR-14). Every rank shows its evidence."""
    scores = (
        db.query(RoleScore)
        .filter(RoleScore.role == role, RoleScore.period == period)
        .order_by(RoleScore.computed_value.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "rank": idx + 1,
            "actor_id": score.actor_id,
            "score": score.computed_value,
            "breakdown": score.breakdown,  # Facts behind the rank (FR-14)
        }
        for idx, score in enumerate(scores)
    ]
