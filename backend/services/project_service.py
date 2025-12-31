from datetime import datetime
from typing import List, Optional

from models.models import Project
from sqlalchemy.orm import Session


class ProjectService:
    @staticmethod
    def create_project(db: Session, name: str, description: str = None) -> Project:
        """创建新项目"""
        db_project = Project(name=name, description=description)
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        return db_project

    @staticmethod
    def get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]:
        """获取项目列表"""
        return db.query(Project).offset(skip).limit(limit).all()

    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """根据ID获取项目"""
        return db.query(Project).filter(Project.nid == project_id).first()

    @staticmethod
    def update_project(
        db: Session, project_id: int, name: str = None, description: str = None
    ) -> Optional[Project]:
        """更新项目信息"""
        db_project = db.query(Project).filter(Project.nid == project_id).first()
        if db_project:
            if name is not None:
                db_project.name = name
            if description is not None:
                db_project.description = description
            db_project.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_project)
        return db_project

    @staticmethod
    def delete_project(db: Session, project_id: int) -> bool:
        """删除项目"""
        db_project = db.query(Project).filter(Project.nid == project_id).first()
        if db_project:
            db.delete(db_project)
            db.commit()
            return True
        return False




