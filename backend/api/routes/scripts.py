from fastapi import APIRouter, Depends
from models.database import get_db
from schemas.script import (
    ScriptCreate,
    ScriptExecutionRequest,
)
from services.script_execution_service import (
    ScriptContext,
    ScriptExecutionService,
)
from services.script_service import ScriptService
from sqlalchemy.orm import Session

router = APIRouter(tags=["scripts"], responses={404: {"description": "Not found"}})


@router.get("/")
def get_script(script_id: int = None, db: Session = Depends(get_db)):
    return ScriptService.get_script(db, script_id=script_id)


@router.get("/supported_actions_metadata")
def get_supported_actions_metadata(db: Session = Depends(get_db)):
    return ScriptExecutionService.get_supported_actions_metadata()


@router.post("/")
def create_script(script: ScriptCreate, db: Session = Depends(get_db)):
    return ScriptService.create_script(db, script_create=script)


@router.post("/services/create")
def create_script_service(log_level: str = "INFO", db: Session = Depends(get_db)):
    return ScriptService.create_script_service(db, log_level=log_level)


@router.delete("/services/{service_id}")
def delete_script_service(service_id: str, db: Session = Depends(get_db)):
    return ScriptService.delete_script_service(service_id)


@router.get("/services")
def get_script_services(db: Session = Depends(get_db)):
    return ScriptService.get_all_script_service_ids(db)


@router.post("/execute")
async def execute_script_bg(
    request: ScriptExecutionRequest, db: Session = Depends(get_db)
):
    return await ScriptService.execute_script_bg(
        db,
        request.script_id,
        request.service_id,
        request.log_level,
        request.log_history,
    )


@router.get("/services/{service_id}/result", response_model=ScriptContext)
def get_script_result(service_id: str):
    return ScriptService.get_script_result(service_id)


@router.get("/services/{service_id}/log")
def get_script_log_buffer(service_id: str):
    return ScriptService.get_script_log_buffer(service_id)


@router.post("/services/{service_id}/log/clear")
def clear_script_log_buffer(service_id: str):
    ScriptService.clear_script_log_buffer(service_id)
    return {"message": "Log buffer cleared"}
