"""Story and Bug endpoints with import support (FR-2, FR-3)."""

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Bug, Story
from app.schemas import (
    BugCreate,
    BugResponse,
    ImportResult,
    StoryCreate,
    StoryResponse,
)
from app.services.import_service import import_bugs, import_stories

router = APIRouter(tags=["stories & bugs"])


# --- Stories ---


@router.post("/stories", response_model=StoryResponse, status_code=201)
def create_story(story: StoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Story).filter(Story.story_id == story.story_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Story ID already exists")
    db_story = Story(**story.model_dump())
    db.add(db_story)
    db.commit()
    db.refresh(db_story)
    return db_story


@router.get("/stories", response_model=list[StoryResponse])
def list_stories(
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    module: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Story)
    if project_id:
        query = query.filter(Story.project_id == project_id)
    if sprint_id:
        query = query.filter(Story.sprint_id == sprint_id)
    if module:
        query = query.filter(Story.module == module)
    return query.all()


@router.get("/stories/{story_id}", response_model=StoryResponse)
def get_story(story_id: int, db: Session = Depends(get_db)):
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story


@router.post("/stories/import", response_model=ImportResult)
async def import_stories_file(
    project_id: int = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import stories from Excel/CSV/JSON file (FR-2)."""
    content = await file.read()
    return import_stories(db, content, file.filename, project_id)


# --- Bugs ---


@router.post("/bugs", response_model=BugResponse, status_code=201)
def create_bug(bug: BugCreate, db: Session = Depends(get_db)):
    existing = db.query(Bug).filter(Bug.bug_id == bug.bug_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Bug ID already exists")
    db_bug = Bug(**bug.model_dump())
    db.add(db_bug)
    db.commit()
    db.refresh(db_bug)
    return db_bug


@router.get("/bugs", response_model=list[BugResponse])
def list_bugs(
    story_id: int | None = Query(None),
    severity: str | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Bug)
    if story_id:
        query = query.filter(Bug.story_id == story_id)
    if severity:
        query = query.filter(Bug.severity == severity)
    if status:
        query = query.filter(Bug.status == status)
    return query.all()


@router.get("/bugs/{bug_id}", response_model=BugResponse)
def get_bug(bug_id: int, db: Session = Depends(get_db)):
    bug = db.query(Bug).filter(Bug.id == bug_id).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")
    return bug


@router.post("/bugs/import", response_model=ImportResult)
async def import_bugs_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Import bugs from Excel/CSV/JSON file (FR-3)."""
    content = await file.read()
    return import_bugs(db, content, file.filename)
