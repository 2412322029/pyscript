from fastapi import APIRouter, Depends
from models.database import get_db
from schemas.script import (
    ScriptCreate,
    ScriptExecutionRequest,
)
from sqlalchemy.orm import Session
from services.project_service import ScriptService

router = APIRouter(tags=["scripts"], responses={404: {"description": "Not found"}})


@router.get("/")
def get_scripts(
    nid: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)
):
    """Temporary placeholder route for scripts"""
    return ScriptService.get_scripts(db, nid=nid, skip=skip, limit=limit)


@router.post("/")
def create_script(script: ScriptCreate, db: Session = Depends(get_db)):
    """Temporary placeholder for script creation"""
    return ScriptService.create_script(
        db, project_id=script.project_id, name=script.name, content=script.content
    )


@router.post("/execute")
def execute_script(request: ScriptExecutionRequest, db: Session = Depends(get_db)):
    """Temporary placeholder for script execution"""
    return ScriptService.execute_script(db, request)
