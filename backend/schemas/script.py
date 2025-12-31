import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class ScriptCreate(BaseModel):
    """Schema for creating a new script"""

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Name must be at least 3 characters",
    )
    content: str = Field(
        ..., min_length=10, description="Python code content of the script"
    )
    content_type: str = Field(
        "json", description="Type of script content (e.g., json, bash)"
    )
    project_id: Optional[int] = Field(
        None, ge=1, description="Optional project ID this script belongs to"
    )
    @validator("content")
    def validate_json_syntax(cls, v):
        """Basic JSON syntax validation"""
        try:
            json.loads(v)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON syntax: {str(e)}")
        return v


class ScriptUpdate(ScriptCreate):
    ...

class ScriptInDBBase(BaseModel):
    nid: int = Field(..., description="Unique identifier for the script")
    created_at: datetime = Field(
        ..., description="Timestamp when the script was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the script was last updated"
    )
    class Config:
        from_attributes = True


class ScriptList(BaseModel):
    """Schema for listing scripts with pagination"""

    scripts: List[ScriptInDBBase]
    pagination: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 10, "has_next": False},
        description="Pagination information",
    )


class ScriptExecutionRequest(BaseModel):
    """Schema for requesting script execution"""

    script_id: int = Field(..., ge=1, description="ID of the script to execute")
    service_id: str = Field(..., description="ID of the script execution service")
    log_level: str = Field(
        "INFO", description="Log level for script execution (e.g., DEBUG, INFO)"
    )
    timeout: Optional[int] = Field(
        30, description="Execution timeout in seconds (default 30)"
    )


class ScriptExecutionResponse(BaseModel):
    """Schema for script execution response"""

    task_id: str = Field(..., description="ID of the execution task")
    script_id: int = Field(..., description="ID of the executed script")
    status: str = Field(..., description="Current status of the execution task")
    started_at: datetime = Field(..., description="Timestamp when execution started")
    result_url: str = Field(..., description="URL to retrieve execution results")
