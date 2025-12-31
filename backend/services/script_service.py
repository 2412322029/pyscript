import asyncio
import json
from datetime import datetime
from typing import List, Optional

from models.models import Script
from schemas.script import ScriptCreate, ScriptUpdate
from services.script_execution_service import (
    ScriptExecutionService,
    ScriptExecutionServiceDict,
)
from sqlalchemy.orm import Session


class ScriptService:
    @staticmethod
    def create_script(db: Session, script_create: ScriptCreate) -> Script:
        """创建新脚本"""
        db_script = Script(**script_create.dict())
        db.add(db_script)
        db.commit()
        db.refresh(db_script)
        return db_script

    @staticmethod
    def get_scripts(db: Session, project_id: int) -> List[Script]:
        """获取项目的所有脚本"""
        return db.query(Script).filter(Script.project_id == project_id).all()

    @staticmethod
    def get_script(db: Session, script_id: int) -> Optional[Script]:
        """根据ID获取脚本"""
        return db.query(Script).filter(Script.nid == script_id).first()

    @staticmethod
    def get_all(db: Session) -> List[Script]:
        """获取所有脚本"""
        return db.query(Script).all()

    @staticmethod
    def update_script(db: Session, script_update: ScriptUpdate) -> Optional[Script]:
        """更新脚本信息"""
        db_script = db.query(Script).filter(Script.nid == script_update.nid).first()
        if db_script:
            for key, value in script_update.dict(exclude_unset=True).items():
                setattr(db_script, key, value)
            db_script.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_script)
        return db_script

    @staticmethod
    def delete_script(db: Session, script_id: int) -> bool:
        """删除脚本"""
        db_script = db.query(Script).filter(Script.nid == script_id).first()
        if db_script:
            db.delete(db_script)
            db.commit()
            return True
        return False

    @staticmethod
    def create_script_service(db: Session, log_level: str = "INFO") -> str:
        """创建新脚本服务"""
        S = ScriptExecutionService(log_level=log_level, log_target="buffer")
        return ScriptExecutionService.add_service(S)

    @staticmethod
    def get_all_script_service_ids(db: Session) -> dict:
        """获取所有脚本服务"""
        j = {}
        for service_id, S in ScriptExecutionServiceDict.items():
            j[service_id] = S.get_context_size()
        return j

    @staticmethod
    def get_script_service(service_id: str) -> Optional[ScriptExecutionService]:
        """根据ID获取脚本服务"""
        return ScriptExecutionServiceDict.get(service_id)
    
    @staticmethod
    def delete_script_service(service_id: str) -> bool:
        """删除脚本服务"""
        if service_id in ScriptExecutionServiceDict:
            del ScriptExecutionServiceDict[service_id]
            return True
        return False

    @staticmethod
    async def execute_script_bg(
        db: Session,
        script_id: int,
        service_id: str | None = None,
        log_level: str = "DEBUG",
        log_history: bool = False,
    ) -> Optional[dict]:
        """后台任务：执行脚本"""
        db_script = ScriptService.get_script(db, script_id)
        if not db_script:
            return None
        json_content = json.loads(db_script.content)
        if service_id is None or service_id not in ScriptExecutionServiceDict:
            service_id = ScriptService.create_script_service(db, log_level)
        S = ScriptService.get_script_service(service_id)
        asyncio.create_task(
            S.execute_script(
                script_content_type=db_script.content_type,
                script_content=json_content,
                log_history=log_history,
            )
        )
        return service_id

    @staticmethod
    def get_script_result(service_id: str) -> Optional[dict]:
        """获取脚本执行结果"""
        S = ScriptService.get_script_service(service_id)
        if S:
            return S.get_context()
        else:
            return None

    @staticmethod
    def get_script_log_buffer(service_id: str) -> Optional[str]:
        """获取脚本执行日志缓冲区"""
        S = ScriptService.get_script_service(service_id)
        if S:
            return S.get_log_buffer()
        else:
            return None

    @staticmethod
    def clear_script_log_buffer(service_id: str) -> None:
        """清空脚本执行日志缓冲区"""
        S = ScriptService.get_script_service(service_id)
        if S:
            S.clear_log_buffer()
