from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.pydantic_schemas import BugCreate, BugListResponse, BugRead, BugUpdate
from app.models.schemas import Bug
from app.services.scoring_engine import recompute_role_scores, sync_bug_quality_events, sync_story_quality_events

router = APIRouter(prefix="/bugs", tags=["bugs"])


def _bug_query():
    return select(Bug).options(
        selectinload(Bug.story).selectinload(Bug.story.project),
        selectinload(Bug.story).selectinload(Bug.story.sprint),
        selectinload(Bug.story).selectinload(Bug.story.ba),
        selectinload(Bug.story).selectinload(Bug.story.developer),
        selectinload(Bug.story).selectinload(Bug.story.tester),
        selectinload(Bug.story).selectinload(Bug.story.automation_engineer),
        selectinload(Bug.project),
        selectinload(Bug.sprint),
        selectinload(Bug.detected_by),
        selectinload(Bug.assigned_to),
        selectinload(Bug.human_approved_by),
    )


@router.get("", response_model=BugListResponse)
def list_bugs(
    project_id: int | None = None,
    sprint_id: int | None = None,
    module: str | None = None,
    severity: str | None = None,
    detected_stage: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
) -> BugListResponse:
    query = _bug_query()
    if project_id is not None:
        query = query.where(Bug.project_id == project_id)
    if sprint_id is not None:
        query = query.where(Bug.sprint_id == sprint_id)
    if module is not None:
        query = query.where(Bug.module == module)
    if severity is not None:
        query = query.where(Bug.severity == severity)
    if detected_stage is not None:
        query = query.where(Bug.detected_stage == detected_stage)
    if status_filter is not None:
        query = query.where(Bug.status == status_filter)
    bugs = list(db.scalars(query.order_by(Bug.created_date.desc()).offset(offset).limit(limit)).all())
    total = len(list(db.scalars(query).all()))
    return BugListResponse(items=bugs, total=total)


@router.post("", response_model=BugRead, status_code=status.HTTP_201_CREATED)
def create_bug(payload: BugCreate, db: Session = Depends(get_db)) -> Bug:
    bug = Bug(**payload.model_dump(exclude_none=True))
    db.add(bug)
    db.commit()
    db.refresh(bug)
    sync_bug_quality_events(db, bug)
    if bug.story is not None:
        sync_story_quality_events(db, bug.story)
    db.commit()
    recompute_role_scores(db, period="all-time")
    return db.scalar(_bug_query().where(Bug.id == bug.id))


@router.get("/{bug_id}", response_model=BugRead)
def get_bug(bug_id: int, db: Session = Depends(get_db)) -> Bug:
    bug = db.scalar(_bug_query().where(Bug.id == bug_id))
    if bug is None:
        raise HTTPException(status_code=404, detail="Bug not found")
    return bug


@router.put("/{bug_id}", response_model=BugRead)
def update_bug(bug_id: int, payload: BugUpdate, db: Session = Depends(get_db)) -> Bug:
    bug = db.get(Bug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail="Bug not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(bug, key, value)
    db.add(bug)
    db.commit()
    db.refresh(bug)
    sync_bug_quality_events(db, bug)
    if bug.story is not None:
        sync_story_quality_events(db, bug.story)
    db.commit()
    recompute_role_scores(db, period="all-time")
    return db.scalar(_bug_query().where(Bug.id == bug.id))


@router.delete("/{bug_id}")
def delete_bug(bug_id: int, db: Session = Depends(get_db)) -> dict:
    bug = db.get(Bug, bug_id)
    if bug is None:
        raise HTTPException(status_code=404, detail="Bug not found")
    if bug.quality_events:
        raise HTTPException(status_code=409, detail="Bug has immutable quality events and cannot be deleted")
    db.delete(bug)
    db.commit()
    return {"status": "deleted"}
