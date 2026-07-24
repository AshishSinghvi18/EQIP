"""Quality Events and Scoring endpoints (FR-4, FR-5, FR-9, FR-11)."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import QualityEvent, RoleScore, ScoringWeight, UserRole
from app.schemas import (
    QualityEventCreate,
    QualityEventResponse,
    RoleScoreResponse,
    ScoringWeightCreate,
    ScoringWeightResponse,
)
from app.services.score_engine import compute_score_for_actor, record_quality_event

router = APIRouter(tags=["quality & scoring"])


# --- Quality Events (immutable audit trail, FR-11) ---


@router.post("/events", response_model=QualityEventResponse, status_code=201)
def create_quality_event(event: QualityEventCreate, db: Session = Depends(get_db)):
    """Record an immutable quality event. Append-only - never overwritten."""
    db_event = record_quality_event(
        db=db,
        story_id=event.story_id,
        bug_id=event.bug_id,
        role=event.role,
        actor_id=event.actor_id,
        event_type=event.event_type,
        delta=event.delta,
        reason=event.reason,
        source_ref=event.source_ref,
        ai_suggested=event.ai_suggested,
    )
    return db_event


@router.get("/events", response_model=list[QualityEventResponse])
def list_quality_events(
    actor_id: int | None = Query(None),
    role: UserRole | None = Query(None),
    story_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """List quality events with filtering. Full audit trail (FR-11)."""
    query = db.query(QualityEvent)
    if actor_id:
        query = query.filter(QualityEvent.actor_id == actor_id)
    if role:
        query = query.filter(QualityEvent.role == role)
    if story_id:
        query = query.filter(QualityEvent.story_id == story_id)
    return query.order_by(QualityEvent.created_at.desc()).all()


@router.post("/events/{event_id}/approve", response_model=QualityEventResponse)
def approve_quality_event(
    event_id: int,
    approved_by: int = Query(...),
    db: Session = Depends(get_db),
):
    """EM approves an AI-suggested quality event (FR-9 - mandatory human sign-off)."""
    event = db.query(QualityEvent).filter(QualityEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if not event.ai_suggested:
        raise HTTPException(status_code=400, detail="Event is not AI-suggested")
    if event.approved_by is not None:
        raise HTTPException(status_code=400, detail="Event already approved")

    event.approved_by = approved_by
    db.commit()
    db.refresh(event)
    return event


# --- Scores (FR-4, recomputed from events) ---


@router.get("/scores/{actor_id}", response_model=list[RoleScoreResponse])
def get_scores(actor_id: int, db: Session = Depends(get_db)):
    """Get all role scores for an actor."""
    return db.query(RoleScore).filter(RoleScore.actor_id == actor_id).all()


@router.post("/scores/compute", response_model=RoleScoreResponse)
def compute_score(
    actor_id: int = Query(...),
    role: UserRole = Query(...),
    period: str = Query(...),
    module: str | None = Query(None),
    db: Session = Depends(get_db),
):
    """Recompute score for actor/role/period by replaying events (FR-11)."""
    return compute_score_for_actor(db, actor_id, role, period, module)


# --- Scoring Weights (FR-5) ---


@router.post("/weights", response_model=ScoringWeightResponse, status_code=201)
def create_weight(weight: ScoringWeightCreate, db: Session = Depends(get_db)):
    """Admin sets gain/loss/severity weights."""
    db_weight = ScoringWeight(**weight.model_dump())
    db.add(db_weight)
    db.commit()
    db.refresh(db_weight)
    return db_weight


@router.get("/weights", response_model=list[ScoringWeightResponse])
def list_weights(
    project_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ScoringWeight)
    if project_id:
        query = query.filter(ScoringWeight.project_id == project_id)
    return query.all()
