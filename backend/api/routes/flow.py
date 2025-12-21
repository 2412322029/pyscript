from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from models.database import get_db
from schemas.flow import Flow, FlowCreate, FlowUpdate, FlowList
from services import flow as flow_service

router = APIRouter()


@router.post("/", response_model=Flow, status_code=status.HTTP_201_CREATED)
def create_flow(
    flow: FlowCreate,
    db: Session = Depends(get_db)
):
    """创建新流程"""
    try:
        return flow_service.create_flow(db=db, flow=flow)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/", response_model=FlowList)
def get_flows(
    project_id: int,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取项目的流程列表"""
    try:
        flows, total, has_next = flow_service.get_flows(
            db=db, project_id=project_id, skip=skip, limit=limit
        )
        return FlowList(
            flows=flows,
            pagination={
                "total": total,
                "skip": skip,
                "limit": limit,
                "has_next": has_next
            }
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{id}", response_model=Flow)
def get_flow(
    id: int,
    db: Session = Depends(get_db)
):
    """获取单个流程详情"""
    db_flow = flow_service.get_flow(db=db, flow_id=id)
    if not db_flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    return db_flow


@router.put("/{id}", response_model=Flow)
def update_flow(
    id: int,
    flow: FlowUpdate,
    db: Session = Depends(get_db)
):
    """更新流程"""
    db_flow = flow_service.update_flow(db=db, flow_id=id, flow_update=flow)
    if not db_flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    return db_flow


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_flow(
    id: int,
    db: Session = Depends(get_db)
):
    """删除流程"""
    success = flow_service.delete_flow(db=db, flow_id=id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    return None


@router.get("/{id}/export")
def export_flow(
    id: int,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """导出流程"""
    flow = flow_service.get_flow(db=db, flow_id=id)
    if not flow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Flow not found")
    
    # 导出为JSON格式
    return {
        "name": flow.name,
        "description": flow.description,
        "connections": flow.connections,
        "selected": flow.selected,
        "zoom": flow.zoom,
        "position": flow.position
    }


@router.post("/import", response_model=Flow, status_code=status.HTTP_201_CREATED)
def import_flow(
    project_id: int,
    flow_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """导入流程"""
    try:
        # 从导入的数据创建流程
        flow_create = FlowCreate(
            name=flow_data["name"],
            description=flow_data.get("description", ""),
            project_id=project_id,
            connections=flow_data.get("connections", []),
            selected=flow_data.get("selected", []),
            zoom=flow_data.get("zoom", 1.0),
            position=flow_data.get("position", {"x": 0, "y": 0})
        )
        return flow_service.create_flow(db=db, flow=flow_create)
    except KeyError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Missing required field: {str(e)}")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))