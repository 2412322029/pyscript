from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProjectBase(BaseModel):
    """项目基础模型"""
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    """创建项目模型"""
    pass


class ProjectUpdate(BaseModel):
    """更新项目模型"""
    name: Optional[str] = None
    description: Optional[str] = None


class ProjectInDB(ProjectBase):
    """数据库中的项目模型"""
    id: int

    class Config:
        from_attributes = True


class Project(ProjectInDB):
    """项目响应模型"""
    pass


class ProjectResponse(Project):
    """项目API响应模型"""
    pass