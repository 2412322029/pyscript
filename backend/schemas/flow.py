from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class FlowBase(BaseModel):
    """流程基础模型"""
    name: str = Field(..., description="流程名称", max_length=255)
    description: Optional[str] = Field("", description="流程描述")
    nodes: List[Dict[str, Any]] = Field(default_factory=list, description="节点列表")
    connections: List[Dict[str, Any]] = Field(default_factory=list, description="连接列表")
    selected: List[str] = Field(default_factory=list, description="选中的节点ID列表")
    zoom: float = Field(1.0, description="缩放比例")
    position: Dict[str, float] = Field(default_factory=lambda: {"x": 0, "y": 0}, description="位置信息")


class FlowCreate(FlowBase):
    """创建流程模型"""
    project_id: int = Field(..., description="所属项目ID")


class FlowUpdate(BaseModel):
    """更新流程模型"""
    name: Optional[str] = Field(None, description="流程名称", max_length=255)
    description: Optional[str] = Field(None, description="流程描述")
    nodes: Optional[List[Dict[str, Any]]] = Field(None, description="节点列表")
    connections: Optional[List[Dict[str, Any]]] = Field(None, description="连接列表")
    selected: Optional[List[str]] = Field(None, description="选中的节点ID列表")
    zoom: Optional[float] = Field(None, description="缩放比例")
    position: Optional[Dict[str, float]] = Field(None, description="位置信息")


class Flow(FlowBase):
    """流程响应模型"""
    id: int = Field(..., description="流程ID")
    project_id: int = Field(..., description="所属项目ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True


class FlowList(BaseModel):
    """流程列表响应模型"""
    flows: List[Flow] = Field(..., description="流程列表")
    pagination: Dict[str, Any] = Field(..., description="分页信息")