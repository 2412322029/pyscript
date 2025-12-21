from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db
from models.models import Project
from schemas.project import ProjectCreate, ProjectUpdate, Project, ProjectList
from services.project_service import ProjectService, ScriptService

router = APIRouter(
    prefix="/projects", tags=["projects"], responses={404: {"description": "Not found"}}
)


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
def create_new_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    return ProjectService.create_project(
        db=db, name=project.name, description=project.description
    )


@router.get("/", response_model=ProjectList)
def read_projects(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """Retrieve projects with pagination"""
    projects = ProjectService.get_projects(db, skip=skip, limit=limit)
    total = db.query(Project).count()
    return {
        "projects": projects,
        "pagination": {
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_next": skip + limit < total,
        },
    }


@router.get("/{project_id}", response_model=Project)
def read_project(project_id: int, db: Session = Depends(get_db)):
    """Retrieve a specific project by ID"""
    db_project = ProjectService.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return db_project


@router.put("/{project_id}", response_model=Project)
def update_existing_project(
    project_id: int, project: ProjectUpdate, db: Session = Depends(get_db)
):
    """Update an existing project"""
    db_project = get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectService.update_project(
        db=db, project_id=project_id, name=project.name, description=project.description
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_project(project_id: int, db: Session = Depends(get_db)):
    """Delete a project"""
    db_project = ProjectService.get_project(db, project_id=project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    ProjectService.delete_project(db=db, project_id=project_id)
    return {}


@router.get("/{project_id}/scripts/count")
def get_project_scripts_count(project_id: int, db: Session = Depends(get_db)):
    """Get the count of scripts in a specific project"""
    scripts = ScriptService.get_scripts(db, project_id=project_id)
    return {"project_id": project_id, "script_count": len(scripts)}
