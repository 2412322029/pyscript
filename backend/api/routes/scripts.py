from fastapi import APIRouter, Depends
from models.database import get_db
from schemas.script import (
    ScriptCreate,
    ScriptExecutionRequest,
)
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/scripts", tags=["scripts"], responses={404: {"description": "Not found"}}
)


@router.get("/")
def get_scripts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Temporary placeholder route for scripts"""
    return {"message": "Scripts endpoint placeholder"}


@router.post("/")
def create_script(script: ScriptCreate, db: Session = Depends(get_db)):
    """Temporary placeholder for script creation"""
    return {"message": "Script creation placeholder", "script_name": script.name}


@router.post("/execute")
def execute_script(request: ScriptExecutionRequest, db: Session = Depends(get_db)):
    """Temporary placeholder for script execution"""
    return {"message": "Script execution placeholder", "script_id": request.script_id}
