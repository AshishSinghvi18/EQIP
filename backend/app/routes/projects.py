from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.models.pydantic_schemas import ProjectCreate, ProjectRead, SprintCreate, SprintRead
from app.models.schemas import Bug, Project, Sprint, Story

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectRead])
def list_projects(db: Session = Depends(get_db)) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.key)).all())


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db)) -> dict:
    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.sprints), selectinload(Project.stories), selectinload(Project.bugs))
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    modules = sorted({story.module for story in project.stories})
    return {
        "id": project.id,
        "key": project.key,
        "name": project.name,
        "description": project.description,
        "status": project.status,
        "sprint_count": len(project.sprints),
        "story_count": len(project.stories),
        "bug_count": len(project.bugs),
        "modules": modules,
        "sprints": [SprintRead.model_validate(sprint).model_dump(mode="json") for sprint in sorted(project.sprints, key=lambda item: item.start_date)],
    }


@router.get("/{project_id}/sprints", response_model=list[SprintRead])
def list_project_sprints(project_id: int, db: Session = Depends(get_db)) -> list[Sprint]:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return list(db.scalars(select(Sprint).where(Sprint.project_id == project_id).order_by(Sprint.start_date)).all())


@router.post("/{project_id}/sprints", response_model=SprintRead, status_code=status.HTTP_201_CREATED)
def create_sprint(project_id: int, payload: SprintCreate, db: Session = Depends(get_db)) -> Sprint:
    if db.get(Project, project_id) is None:
        raise HTTPException(status_code=404, detail="Project not found")
    sprint_data = payload.model_dump()
    sprint_data["project_id"] = project_id
    sprint = Sprint(**sprint_data)
    db.add(sprint)
    db.commit()
    db.refresh(sprint)
    return sprint


@router.get("/sprints/{sprint_id}")
def get_sprint(sprint_id: int, db: Session = Depends(get_db)) -> dict:
    sprint = db.scalar(
        select(Sprint)
        .where(Sprint.id == sprint_id)
        .options(selectinload(Sprint.project), selectinload(Sprint.stories), selectinload(Sprint.bugs))
    )
    if sprint is None:
        raise HTTPException(status_code=404, detail="Sprint not found")
    return {
        "id": sprint.id,
        "name": sprint.name,
        "project": {"id": sprint.project.id, "key": sprint.project.key, "name": sprint.project.name},
        "status": sprint.status,
        "release_name": sprint.release_name,
        "date_range": {"start": sprint.start_date, "end": sprint.end_date},
        "story_count": len(sprint.stories),
        "bug_count": len(sprint.bugs),
        "modules": sorted({story.module for story in sprint.stories}),
    }
