"""Project and Sprint management endpoints (FR-1)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Project, Sprint
from app.schemas import ProjectCreate, ProjectResponse, SprintCreate, SprintResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    db_project = Project(name=project.name, description=project.description)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get("/", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/{project_id}/sprints", response_model=SprintResponse, status_code=201)
def create_sprint(project_id: int, sprint: SprintCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db_sprint = Sprint(
        name=sprint.name,
        project_id=project_id,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
    )
    db.add(db_sprint)
    db.commit()
    db.refresh(db_sprint)
    return db_sprint


@router.get("/{project_id}/sprints", response_model=list[SprintResponse])
def list_sprints(project_id: int, db: Session = Depends(get_db)):
    return db.query(Sprint).filter(Sprint.project_id == project_id).all()
