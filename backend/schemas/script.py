from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ScriptBase(BaseModel):
    """脚本基础模型"""
    name: str
    code: str
    description: Optional[str] = None
    project_id: int
    created_at: Optional[datetime] = None


class ScriptCreate(ScriptBase):
    """创建脚本模型"""
    pass


class ScriptUpdate(BaseModel):
    """更新脚本模型"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class ScriptInDB(ScriptBase):
    """数据库中的脚本模型"""
    id: int

    class Config:
        from_attributes = True


class Script(ScriptInDB):
    """脚本响应模型"""
    pass


class ScriptResponse(Script):
    """脚本API响应模型"""
    pass


class ScriptExecuteRequest(BaseModel):
    """执行脚本请求模型"""
    inputs: Optional[dict] = None


class ScriptExecuteResponse(BaseModel):
    """执行脚本响应模型"""
    success: bool
    result: Optional[dict] = None
    error: Optional[str] = None