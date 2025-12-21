from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: Optional[str] = Field(
        None, max_length=500, description="Project description"
    )
    is_active: Optional[bool] = Field(True, description="Whether the project is active")


class ProjectCreate(ProjectBase):
    """Schema for creating a new project"""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class ProjectInDBBase(ProjectBase):
    id: int = Field(..., description="Project ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class Project(ProjectInDBBase):
    """Schema for returning project details"""

    script_count: int = Field(0, description="Number of scripts in this project")


class ProjectList(BaseModel):
    """Schema for listing projects with pagination"""

    projects: List[Project]
    pagination: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 10, "has_next": False},
        description="Pagination information",
    )
