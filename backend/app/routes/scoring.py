from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.pydantic_schemas import LeaderboardEntry, LeaderboardResponse, QualityEventRead, RoleScoreRead, UserRead, UserScorecardResponse
from app.models.schemas import QualityEvent, RoleScore, User, UserRole
from app.services.scoring_engine import fetch_leaderboard, recent_events_for_user, recompute_role_scores

router = APIRouter(prefix="/scoring", tags=["scoring"])


@router.post("/recompute")
def recompute_scores(
    period: str = "all-time",
    window_days: int | None = Query(default=None, ge=1, le=3650),
    module: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    scores = recompute_role_scores(db, period=period, window_days=window_days, module=module)
    return {"period": period, "scores_recomputed": len(scores)}


@router.get("/leaderboard", response_model=LeaderboardResponse)
def scoring_leaderboard(
    role: UserRole | None = None,
    module: str | None = None,
    limit: int = Query(default=10, ge=1, le=50),
    db: Session = Depends(get_db),
) -> LeaderboardResponse:
    scores = fetch_leaderboard(db, role=role, module=module, limit=limit)
    items = [
        LeaderboardEntry(
            user_id=score.actor_id,
            name=score.actor.full_name,
            role=score.role,
            score=round(score.computed_value, 2),
            module=score.module,
            facts=[item["label"] for item in score.breakdown.get("top_event_types", [])[:3]],
        )
        for score in scores
    ]
    return LeaderboardResponse(items=items)


@router.get("/events", response_model=list[QualityEventRead])
def list_score_events(
    actor_id: int | None = None,
    role: UserRole | None = None,
    module: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> list[QualityEvent]:
    query = select(QualityEvent).options(selectinload(QualityEvent.actor)).order_by(QualityEvent.created_at.desc()).limit(limit)
    if actor_id is not None:
        query = query.where(QualityEvent.actor_id == actor_id)
    if role is not None:
        query = query.where(QualityEvent.role == role)
    if module is not None:
        query = query.where(QualityEvent.module == module)
    return list(db.scalars(query).all())


@router.get("/users/{user_id}", response_model=UserScorecardResponse)
def get_user_scorecard(user_id: int, db: Session = Depends(get_db)) -> UserScorecardResponse:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if not db.scalar(select(RoleScore.id).where(RoleScore.actor_id == user_id).limit(1)):
        recompute_role_scores(db, period="all-time", actor_id=user_id)
    scores = list(
        db.scalars(
            select(RoleScore)
            .where(RoleScore.actor_id == user_id)
            .options(selectinload(RoleScore.actor))
            .order_by(RoleScore.module.is_not(None), RoleScore.computed_value.desc())
        ).all()
    )
    events = list(recent_events_for_user(db, user_id=user_id, limit=20))
    return UserScorecardResponse(user=UserRead.model_validate(user), scores=[RoleScoreRead.model_validate(score) for score in scores], recent_events=[QualityEventRead.model_validate(event) for event in events])
