from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.pydantic_schemas import StoryCreate, StoryListResponse, StoryRead, StoryUpdate
from app.models.schemas import Story
from app.services.scoring_engine import recompute_role_scores, sync_story_quality_events

router = APIRouter(prefix="/stories", tags=["stories"])


def _story_query():
    return select(Story).options(
        selectinload(Story.project),
        selectinload(Story.sprint),
        selectinload(Story.ba),
        selectinload(Story.developer),
        selectinload(Story.tester),
        selectinload(Story.automation_engineer),
        selectinload(Story.reviewer),
    )


@router.get("", response_model=StoryListResponse)
def list_stories(
    project_id: int | None = None,
    sprint_id: int | None = None,
    module: str | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=100, le=500),
    offset: int = 0,
    db: Session = Depends(get_db),
) -> StoryListResponse:
    query = _story_query()
    if project_id is not None:
        query = query.where(Story.project_id == project_id)
    if sprint_id is not None:
        query = query.where(Story.sprint_id == sprint_id)
    if module is not None:
        query = query.where(Story.module == module)
    if status_filter is not None:
        query = query.where(Story.status == status_filter)
    stories = list(db.scalars(query.order_by(Story.story_key).offset(offset).limit(limit)).all())
    total = len(list(db.scalars(query).all()))
    return StoryListResponse(items=stories, total=total)


@router.post("", response_model=StoryRead, status_code=status.HTTP_201_CREATED)
def create_story(payload: StoryCreate, db: Session = Depends(get_db)) -> Story:
    story = Story(**payload.model_dump())
    db.add(story)
    db.commit()
    db.refresh(story)
    sync_story_quality_events(db, story)
    db.commit()
    recompute_role_scores(db, period="all-time")
    return db.scalar(_story_query().where(Story.id == story.id))


@router.get("/{story_id}", response_model=StoryRead)
def get_story(story_id: int, db: Session = Depends(get_db)) -> Story:
    story = db.scalar(_story_query().where(Story.id == story_id))
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.put("/{story_id}", response_model=StoryRead)
def update_story(story_id: int, payload: StoryUpdate, db: Session = Depends(get_db)) -> Story:
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(story, key, value)
    db.add(story)
    db.commit()
    db.refresh(story)
    sync_story_quality_events(db, story)
    db.commit()
    recompute_role_scores(db, period="all-time")
    return db.scalar(_story_query().where(Story.id == story.id))


@router.delete("/{story_id}")
def delete_story(story_id: int, db: Session = Depends(get_db)) -> dict:
    story = db.get(Story, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")
    if story.bugs or story.quality_events:
        raise HTTPException(status_code=409, detail="Story has dependent bugs or quality events and cannot be deleted")
    db.delete(story)
    db.commit()
    return {"status": "deleted"}
