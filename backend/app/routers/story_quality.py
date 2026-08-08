"""Story Quality Dashboard endpoints (v1.1, §10.5, FR-18–FR-22)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    Bug,
    BugReasoningClass,
    PerRoleStoryScore,
    QualityClass,
    Story,
    StoryClassRecord,
    UserRole,
)
from app.schemas import (
    BugReasoningBreakdown,
    PerRoleStoryScoreResponse,
    StoryClassResponse,
    StoryQualitySummary,
)
from app.services.story_score_engine import (
    compute_and_classify_story,
    update_story_onboarding_status,
)

router = APIRouter(prefix="/story-quality", tags=["story quality (v1.1)"])


# --- FR-22: Total onboarded + "where we fall" dashboard ---


@router.get("/summary", response_model=StoryQualitySummary)
def get_story_quality_summary(
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Story-quality dashboard summary (§10.5).

    Shows total stories onboarded, insufficient-data count, and
    High/Medium/Low class breakdown.
    """
    query = db.query(Story)
    if project_id:
        query = query.filter(Story.project_id == project_id)
    if sprint_id:
        query = query.filter(Story.sprint_id == sprint_id)

    total_stories = query.count()
    onboarded = query.filter(Story.onboarding_complete.is_(True)).count()
    insufficient = total_stories - onboarded

    high = query.filter(Story.quality_class == QualityClass.HIGH).count()
    medium = query.filter(Story.quality_class == QualityClass.MEDIUM).count()
    low = query.filter(Story.quality_class == QualityClass.LOW).count()

    return StoryQualitySummary(
        total_onboarded=onboarded,
        insufficient_data=insufficient,
        high_count=high,
        medium_count=medium,
        low_count=low,
    )


@router.get("/class-breakdown")
def get_class_breakdown(
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Quality-class breakdown: High/Medium/Low as counts and percentages (§10.5)."""
    query = db.query(Story).filter(Story.onboarding_complete.is_(True))
    if project_id:
        query = query.filter(Story.project_id == project_id)
    if sprint_id:
        query = query.filter(Story.sprint_id == sprint_id)

    results = (
        db.query(Story.quality_class, func.count(Story.id))
        .filter(Story.onboarding_complete.is_(True))
        .group_by(Story.quality_class)
    )
    if project_id:
        results = results.filter(Story.project_id == project_id)
    if sprint_id:
        results = results.filter(Story.sprint_id == sprint_id)

    breakdown = results.all()
    total = sum(c for _, c in breakdown) or 1
    return [
        {
            "quality_class": cls.value if cls else "unclassified",
            "count": count,
            "percentage": round(count / total * 100, 1),
        }
        for cls, count in breakdown
    ]


@router.get("/reasoning-breakdown", response_model=list[BugReasoningBreakdown])
def get_reasoning_breakdown(
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """'Where we fall' — bug-reasoning class breakdown across all bugs (§10.5, §7.4).

    Shows the five reasoning classes as percentages, e.g.:
    Silly miss 34%, Missing unit testing 22%, etc.
    This is the primary 'where do we need to improve' view.
    """
    query = db.query(Bug.reasoning_class, func.count(Bug.id)).filter(
        Bug.reasoning_class.isnot(None),
        Bug.reasoning_class_approved.is_(True),
    )

    if project_id or sprint_id:
        query = query.join(Story, Story.id == Bug.story_id)
        if project_id:
            query = query.filter(Story.project_id == project_id)
        if sprint_id:
            query = query.filter(Story.sprint_id == sprint_id)

    results = query.group_by(Bug.reasoning_class).all()
    total = sum(c for _, c in results) or 1

    return [
        BugReasoningBreakdown(
            reasoning_class=cls.value if cls else "unknown",
            count=count,
            percentage=round(count / total * 100, 1),
        )
        for cls, count in results
    ]


@router.get("/stories-by-class")
def get_stories_by_class(
    quality_class: QualityClass = Query(...),
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Drill-down: list stories in a given class (§10.5 drill path)."""
    query = db.query(Story).filter(Story.quality_class == quality_class)
    if project_id:
        query = query.filter(Story.project_id == project_id)
    if sprint_id:
        query = query.filter(Story.sprint_id == sprint_id)

    stories = query.all()
    return [
        {
            "id": s.id,
            "story_id": s.story_id,
            "title": s.title,
            "module": s.module,
            "quality_class": s.quality_class.value if s.quality_class else None,
            "story_rollup": s.story_rollup,
            "escalation_count": len(s.escalations or []),
        }
        for s in stories
    ]


# --- FR-19: Per-role story scores ---


@router.get("/story/{story_id}/role-scores", response_model=list[PerRoleStoryScoreResponse])
def get_story_role_scores(story_id: int, db: Session = Depends(get_db)):
    """Per-role contribution on a story: each participant's 10 and what they lost (§10.5)."""
    scores = (
        db.query(PerRoleStoryScore)
        .filter(PerRoleStoryScore.story_id == story_id)
        .all()
    )
    return scores


@router.post("/story/{story_id}/compute")
def compute_story_quality(story_id: int, db: Session = Depends(get_db)):
    """Full recomputation: onboarding check → per-role scores → story classification.

    Implements FR-18 (onboarding gate), FR-19 (per-role 10), FR-20 (classification).
    """
    result = compute_and_classify_story(db, story_id)
    return result


@router.get("/story/{story_id}/classification", response_model=StoryClassResponse)
def get_story_classification(story_id: int, db: Session = Depends(get_db)):
    """Get the High/Medium/Low classification for a story (§4.7)."""
    record = (
        db.query(StoryClassRecord)
        .filter(StoryClassRecord.story_id == story_id)
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="No classification found. Run /compute first.")
    return record


# --- Escalation view ---


@router.get("/escalations")
def get_escalation_view(
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Stories with escalations, drill to the traced origin (§10.5)."""
    query = db.query(Story).filter(Story.escalations.isnot(None))
    if project_id:
        query = query.filter(Story.project_id == project_id)
    if sprint_id:
        query = query.filter(Story.sprint_id == sprint_id)

    stories = query.all()
    return [
        {
            "id": s.id,
            "story_id": s.story_id,
            "title": s.title,
            "quality_class": s.quality_class.value if s.quality_class else None,
            "escalations": s.escalations,
            "escalation_count": len(s.escalations or []),
        }
        for s in stories
        if s.escalations  # filter out empty lists
    ]


# --- Class trend ---


@router.get("/class-trend")
def get_class_trend(
    project_id: int = Query(...),
    db: Session = Depends(get_db),
):
    """High/Medium/Low mix per sprint to see quality trend over time (§10.5)."""
    from app.models.models import Sprint

    sprints = (
        db.query(Sprint)
        .filter(Sprint.project_id == project_id)
        .order_by(Sprint.start_date)
        .all()
    )

    trend = []
    for sprint in sprints:
        stories = (
            db.query(Story)
            .filter(
                Story.sprint_id == sprint.id,
                Story.onboarding_complete.is_(True),
            )
            .all()
        )
        total = len(stories)
        if total == 0:
            continue
        high = sum(1 for s in stories if s.quality_class == QualityClass.HIGH)
        medium = sum(1 for s in stories if s.quality_class == QualityClass.MEDIUM)
        low = sum(1 for s in stories if s.quality_class == QualityClass.LOW)

        trend.append({
            "sprint_id": sprint.id,
            "sprint_name": sprint.name,
            "total": total,
            "high": high,
            "medium": medium,
            "low": low,
            "high_pct": round(high / total * 100, 1),
            "medium_pct": round(medium / total * 100, 1),
            "low_pct": round(low / total * 100, 1),
        })

    return trend


# --- FR-18: Onboarding data gate ---


@router.post("/story/{story_id}/check-onboarding")
def check_story_onboarding(story_id: int, db: Session = Depends(get_db)):
    """Check and update onboarding completeness for a story (§4.8, FR-18)."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    story = update_story_onboarding_status(db, story)
    return {
        "story_id": story_id,
        "onboarding_complete": story.onboarding_complete,
        "completeness_gaps": story.completeness_gaps,
        "quality_class": story.quality_class.value if story.quality_class else None,
    }


# --- Needs-data queue (§4.8) ---


@router.get("/needs-data")
def get_needs_data_queue(
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """Stories flagged as 'Insufficient data' — needs data queue (§4.8)."""
    query = db.query(Story).filter(Story.onboarding_complete.is_(False))
    if project_id:
        query = query.filter(Story.project_id == project_id)

    stories = query.all()
    return [
        {
            "id": s.id,
            "story_id": s.story_id,
            "title": s.title,
            "completeness_gaps": s.completeness_gaps,
        }
        for s in stories
    ]
