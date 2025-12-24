from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()


class Project(Base):
    __tablename__ = "projects"
    
    nid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    scripts = relationship("Script", back_populates="project")
    flows = relationship("Flow", back_populates="project")


class Script(Base):
    __tablename__ = "scripts"
    
    nid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    content = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="scripts")
    tasks = relationship("Task", back_populates="script")


class Display(Base):
    __tablename__ = "displays"
    
    nid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    type = Column(String(50))
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"
    
    nid = Column(Integer, primary_key=True, index=True)
    script_id = Column(Integer, ForeignKey("scripts.id"))
    status = Column(String(50), default="pending")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    script = relationship("Script", back_populates="tasks")


class Flow(Base):
    __tablename__ = "flows"
    
    nid = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), index=True)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id"))
    nodes = Column(JSON, default=[])
    connections = Column(JSON, default=[])
    selected = Column(JSON, default=[])
    zoom = Column(Float, default=1.0)
    position = Column(JSON, default={"x": 0, "y": 0})
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # 关系
    project = relationship("Project", back_populates="flows")