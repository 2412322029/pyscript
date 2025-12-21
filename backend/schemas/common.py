from pydantic import BaseModel
from typing import Optional, Any


class ApiResponse(BaseModel):
    """
    通用API响应模型
    用于统一API返回格式
    """

    message: str
    data: Optional[Any] = None
    success: bool = True

    class Config:
        json_schema_extra = {
            "example": {"message": "操作成功", "success": True, "data": None}
        }
