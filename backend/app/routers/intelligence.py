"""AI, Search, Coaching, Disputes, and Forecast endpoints (Phases 2-4)."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import (
    Badge,
    Bug,
    CoachingRecommendation,
    Dispute,
    QualityForecast,
    UserBadge,
)
from app.schemas import (
    BadgeCreate,
    BadgeResponse,
    CoachingRecommendationResponse,
    DisputeCreate,
    DisputeResolve,
    DisputeResponse,
    QualityForecastResponse,
    SearchResult,
    UserBadgeResponse,
)
from app.services.ai_service import generate_coaching_recommendations, suggest_root_cause
from app.services.forecast_service import generate_release_forecast, get_engineering_health_index
from app.services.search_service import search_entities

router = APIRouter(tags=["intelligence"])


# --- AI Suggestions (Phase 2, FR-8) ---


@router.post("/bugs/{bug_id}/ai-suggest")
def ai_suggest_root_cause(bug_id: int, db: Session = Depends(get_db)):
    """AI suggests root cause, owner, severity for a bug (FR-8).

    Returns suggestions with confidence. Does NOT affect scores until EM approves (FR-9).
    """
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    suggestion = suggest_root_cause(bug)

    # Store suggestion on the bug (does not affect scores)
    bug.ai_suggested = suggestion
    bug.ai_confidence = suggestion["confidence"]
    db.commit()
    db.refresh(bug)

    return {
        "bug_id": bug_id,
        "suggestion": suggestion,
        "note": "This suggestion does NOT affect any score until approved by an EM (FR-9).",
    }


@router.post("/bugs/{bug_id}/approve-suggestion")
def approve_ai_suggestion(
    bug_id: int,
    approved_by: int = Query(..., description="EM user ID"),
    db: Session = Depends(get_db),
):
    """EM approves AI suggestion, applying it to the bug record (FR-9)."""
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    if not bug.ai_suggested:
        raise HTTPException(status_code=400, detail="No AI suggestion to approve")
    if bug.human_approved_by:
        raise HTTPException(status_code=400, detail="Already approved")

    # Apply the suggestion
    suggestion = bug.ai_suggested
    bug.root_cause_category = suggestion.get("root_cause_category")
    bug.origin_stage = suggestion.get("origin_stage")
    bug.ownership_split = suggestion.get("ownership_split")
    bug.human_approved_by = approved_by
    bug.human_approved_at = datetime.utcnow()
    db.commit()
    db.refresh(bug)

    return {
        "bug_id": bug_id,
        "status": "approved",
        "approved_by": approved_by,
        "applied": suggestion,
    }


# --- Semantic Search (Phase 2, FR-10) ---


@router.get("/search", response_model=list[SearchResult])
def semantic_search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
):
    """Natural-language search across stories, bugs, and quality events (FR-10).

    Currently uses keyword matching. In production, uses pgvector embeddings
    for true semantic similarity search.
    """
    return search_entities(db, q, limit)


# --- Dispute Handling (FR-16) ---


@router.post("/disputes", response_model=DisputeResponse, status_code=201)
def create_dispute(dispute: DisputeCreate, db: Session = Depends(get_db)):
    """Raise a dispute against an AI-assigned root cause/owner (FR-16)."""
    bug = db.query(Bug).filter(Bug.id == dispute.bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    db_dispute = Dispute(
        bug_id=dispute.bug_id,
        raised_by=dispute.raised_by,
        reason=dispute.reason,
    )
    db.add(db_dispute)
    db.commit()
    db.refresh(db_dispute)
    return db_dispute


@router.get("/disputes", response_model=list[DisputeResponse])
def list_disputes(
    status: str | None = Query(None),
    bug_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """List disputes with optional filtering."""
    query = db.query(Dispute)
    if status:
        query = query.filter(Dispute.status == status)
    if bug_id:
        query = query.filter(Dispute.bug_id == bug_id)
    return query.order_by(Dispute.created_at.desc()).all()


@router.post("/disputes/{dispute_id}/resolve", response_model=DisputeResponse)
def resolve_dispute(
    dispute_id: int,
    resolution: DisputeResolve,
    db: Session = Depends(get_db),
):
    """EM resolves a dispute (FR-16). Resolution is auditable."""
    dispute = db.query(Dispute).filter(Dispute.id == dispute_id).first()
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    if dispute.status != "open":
        raise HTTPException(status_code=400, detail="Dispute already resolved")

    dispute.resolution = resolution.resolution
    dispute.resolved_by = resolution.resolved_by
    dispute.status = resolution.status
    dispute.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(dispute)
    return dispute


# --- Coaching Recommendations (Phase 3, FR-15) ---


@router.get("/coaching/{user_id}", response_model=list[CoachingRecommendationResponse])
def get_coaching(user_id: int, db: Session = Depends(get_db)):
    """Get coaching recommendations for a user (FR-15)."""
    recs = (
        db.query(CoachingRecommendation)
        .filter(
            CoachingRecommendation.user_id == user_id,
            CoachingRecommendation.is_dismissed == False,  # noqa: E712
        )
        .order_by(CoachingRecommendation.created_at.desc())
        .all()
    )
    return recs


@router.post("/coaching/{user_id}/generate", response_model=list[CoachingRecommendationResponse])
def generate_coaching(
    user_id: int,
    period: str = Query("current"),
    db: Session = Depends(get_db),
):
    """Generate new coaching recommendations based on quality event patterns (FR-15)."""
    recs = generate_coaching_recommendations(db, user_id, period)
    return recs


@router.post("/coaching/{recommendation_id}/dismiss")
def dismiss_coaching(recommendation_id: int, db: Session = Depends(get_db)):
    """Dismiss a coaching recommendation."""
    rec = db.query(CoachingRecommendation).filter(CoachingRecommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    rec.is_dismissed = True
    db.commit()
    return {"status": "dismissed"}


# --- Badges & Recognition (Phase 3, FR-14) ---


@router.post("/badges", response_model=BadgeResponse, status_code=201)
def create_badge(badge: BadgeCreate, db: Session = Depends(get_db)):
    """Create a new badge type."""
    db_badge = Badge(**badge.model_dump())
    db.add(db_badge)
    db.commit()
    db.refresh(db_badge)
    return db_badge


@router.get("/badges", response_model=list[BadgeResponse])
def list_badges(db: Session = Depends(get_db)):
    """List all available badges."""
    return db.query(Badge).all()


@router.get("/badges/user/{user_id}", response_model=list[UserBadgeResponse])
def get_user_badges(user_id: int, db: Session = Depends(get_db)):
    """Get all badges awarded to a user with evidence (FR-14)."""
    return (
        db.query(UserBadge)
        .filter(UserBadge.user_id == user_id)
        .order_by(UserBadge.awarded_at.desc())
        .all()
    )


@router.post("/badges/award", response_model=UserBadgeResponse, status_code=201)
def award_badge(
    user_id: int = Query(...),
    badge_id: int = Query(...),
    period: str = Query(...),
    evidence: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Award a badge to a user with supporting evidence (FR-14)."""
    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge_id,
        period=period,
        evidence=[{"note": evidence}] if evidence else None,
    )
    db.add(user_badge)
    db.commit()
    db.refresh(user_badge)
    return user_badge


# --- Forecast & Prediction (Phase 4) ---


@router.post("/forecast", response_model=QualityForecastResponse)
def create_forecast(
    project_id: int = Query(...),
    sprint_id: int | None = Query(None),
    release: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Generate release-risk prediction (Phase 4)."""
    return generate_release_forecast(db, project_id, sprint_id, release)


@router.get("/forecast/{project_id}", response_model=list[QualityForecastResponse])
def get_forecasts(
    project_id: int,
    limit: int = Query(10),
    db: Session = Depends(get_db),
):
    """Get recent forecasts for a project."""
    return (
        db.query(QualityForecast)
        .filter(QualityForecast.project_id == project_id)
        .order_by(QualityForecast.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/health/{project_id}")
def get_health_index(project_id: int, db: Session = Depends(get_db)):
    """Get Engineering Health Index for a project (Phase 4 KPI)."""
    return get_engineering_health_index(db, project_id)
