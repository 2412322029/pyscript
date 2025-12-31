from datetime import datetime
from typing import List, Optional

from models.models import Display
from sqlalchemy.orm import Session


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
