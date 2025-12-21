from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DisplayBase(BaseModel):
    """展示界面基础模型"""

    name: str
    content: str
    project_id: int
    created_at: Optional[datetime] = None


class DisplayCreate(DisplayBase):
    """创建展示界面模型"""

    pass


class DisplayUpdate(BaseModel):
    """更新展示界面模型"""

    name: Optional[str] = None
    content: Optional[str] = None


class DisplayInDB(DisplayBase):
    """数据库中的展示界面模型"""

    id: int

    class Config:
        from_attributes = True


class Display(DisplayInDB):
    """展示界面响应模型"""

    pass


class DisplayResponse(Display):
    """展示界面API响应模型"""

    pass
