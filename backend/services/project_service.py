from typing import List, Optional
from sqlalchemy.orm import Session
from models.models import Project, Script, Display
from datetime import datetime


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
        return db.query(Project).filter(Project.id == project_id).first()

    @staticmethod
    def update_project(
        db: Session, project_id: int, name: str = None, description: str = None
    ) -> Optional[Project]:
        """更新项目信息"""
        db_project = db.query(Project).filter(Project.id == project_id).first()
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
        db_project = db.query(Project).filter(Project.id == project_id).first()
        if db_project:
            db.delete(db_project)
            db.commit()
            return True
        return False


class ScriptService:
    @staticmethod
    def create_script(db: Session, project_id: int, name: str, content: str) -> Script:
        """创建新脚本"""
        db_script = Script(project_id=project_id, name=name, content=content)
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
        return db.query(Script).filter(Script.id == script_id).first()

    @staticmethod
    def update_script(
        db: Session,
        script_id: int,
        name: str = None,
        content: str = None,
        is_active: bool = None,
    ) -> Optional[Script]:
        """更新脚本信息"""
        db_script = db.query(Script).filter(Script.id == script_id).first()
        if db_script:
            if name is not None:
                db_script.name = name
            if content is not None:
                db_script.content = content
            if is_active is not None:
                db_script.is_active = is_active
            db_script.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_script)
        return db_script

    @staticmethod
    def delete_script(db: Session, script_id: int) -> bool:
        """删除脚本"""
        db_script = db.query(Script).filter(Script.id == script_id).first()
        if db_script:
            db.delete(db_script)
            db.commit()
            return True
        return False


class DisplayService:
    @staticmethod
    def create_display(db: Session, project_id: int, name: str, config: str) -> Display:
        """创建新的展示界面"""
        db_display = Display(project_id=project_id, name=name, config=config)
        db.add(db_display)
        db.commit()
        db.refresh(db_display)
        return db_display

    @staticmethod
    def get_displays(db: Session, project_id: int) -> List[Display]:
        """获取项目的所有展示界面"""
        return db.query(Display).filter(Display.project_id == project_id).all()

    @staticmethod
    def get_display(db: Session, display_id: int) -> Optional[Display]:
        """根据ID获取展示界面"""
        return db.query(Display).filter(Display.id == display_id).first()

    @staticmethod
    def update_display(
        db: Session, display_id: int, name: str = None, config: str = None
    ) -> Optional[Display]:
        """更新展示界面配置"""
        db_display = db.query(Display).filter(Display.id == display_id).first()
        if db_display:
            if name is not None:
                db_display.name = name
            if config is not None:
                db_display.config = config
            db_display.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(db_display)
        return db_display

    @staticmethod
    def delete_display(db: Session, display_id: int) -> bool:
        """删除展示界面"""
        db_display = db.query(Display).filter(Display.id == display_id).first()
        if db_display:
            db.delete(db_display)
            db.commit()
            return True
        return False
