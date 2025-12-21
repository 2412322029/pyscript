import json
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from models.models import Flow, Project
from schemas.flow import FlowCreate, FlowUpdate
from datetime import datetime


def get_flow(db: Session, flow_id: int) -> Optional[Flow]:
    """获取单个流程"""
    return db.query(Flow).filter(Flow.id == flow_id).first()


def get_flows(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> tuple[List[Flow], int, bool]:
    """获取项目的流程列表"""
    query = db.query(Flow).filter(Flow.project_id == project_id)
    total = query.count()
    flows = query.offset(skip).limit(limit).all()
    has_next = (skip + limit) < total
    return flows, total, has_next


def create_flow(db: Session, flow: FlowCreate) -> Flow:
    """创建新流程"""
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == flow.project_id).first()
    if not project:
        raise ValueError(f"Project with id {flow.project_id} not found")
    
    # 创建流程对象，不使用UUID，使用自动递增的整数ID
    db_flow = Flow(
        project_id=flow.project_id,
        name=flow.name,
        description=flow.description,
        nodes=flow.nodes or [],
        connections=flow.connections or [],
        selected=flow.selected or [],
        zoom=flow.zoom or 1.0,
        position=flow.position or {"x": 0, "y": 0},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(db_flow)
    db.commit()
    db.refresh(db_flow)
    return db_flow


def update_flow(db: Session, flow_id: int, flow_update: FlowUpdate) -> Optional[Flow]:
    """更新流程"""
    db_flow = get_flow(db, flow_id)
    if not db_flow:
        return None
    
    update_data = flow_update.dict(exclude_unset=True)
    update_data['updated_at'] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(db_flow, key, value)
    
    db.commit()
    db.refresh(db_flow)
    return db_flow


def delete_flow(db: Session, flow_id: int) -> bool:
    """删除流程"""
    db_flow = get_flow(db, flow_id)
    if not db_flow:
        return False
    
    db.delete(db_flow)
    db.commit()
    return True


def export_flow(db: Session, flow_id: int) -> dict:
    """导出流程数据"""
    db_flow = get_flow(db, flow_id)
    if not db_flow:
        raise ValueError(f"Flow with id {flow_id} not found")
    
    return {
        'id': db_flow.id,
        'name': db_flow.name,
        'description': db_flow.description,
        'nodes': db_flow.nodes,
        'connections': db_flow.connections,
        'selected': db_flow.selected,
        'zoom': db_flow.zoom,
        'position': db_flow.position,
        'created_at': db_flow.created_at.isoformat(),
        'updated_at': db_flow.updated_at.isoformat()
    }


def import_flow(db: Session, flow_data: dict, project_id: int) -> Flow:
    """导入流程数据"""
    # 验证项目是否存在
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project with id {project_id} not found")
    
    # 创建新的流程，使用新的ID
    flow_create = FlowCreate(
        project_id=project_id,
        name=flow_data.get('name', 'Imported Flow'),
        description=flow_data.get('description', ''),
        nodes=flow_data.get('nodes', []),
        connections=flow_data.get('connections', []),
        selected=flow_data.get('selected', []),
        zoom=flow_data.get('zoom', 1.0),
        position=flow_data.get('position', {'x': 0, 'y': 0})
    )
    
    return create_flow(db, flow_create)