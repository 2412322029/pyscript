from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


class ScriptBase(BaseModel):
    name: str = Field(
        ..., min_length=1, max_length=100, description="Name of the script"
    )
    content: str = Field(
        ..., min_length=10, description="Python code content of the script"
    )
    description: Optional[str] = Field(
        None, max_length=500, description="Optional description of the script's purpose"
    )
    project_id: Optional[int] = Field(
        None, ge=1, description="Optional project ID this script belongs to"
    )
    is_active: Optional[bool] = Field(
        True, description="Whether the script is active and can be executed"
    )

    @validator("content")
    def validate_python_syntax(cls, v):
        """Basic Python syntax validation"""
        try:
            compile(v, "<string>", "exec")
        except SyntaxError as e:
            raise ValueError(f"Invalid Python syntax: {str(e)}")
        return v


class ScriptCreate(ScriptBase):
    """Schema for creating a new script"""

    name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Name must be at least 3 characters",
    )


class ScriptUpdate(BaseModel):
    """Schema for updating an existing script"""

    name: Optional[str] = Field(None, min_length=3, max_length=100)
    content: Optional[str] = Field(None, min_length=10)
    description: Optional[str] = Field(None, max_length=500)
    project_id: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class ScriptInDBBase(ScriptBase):
    id: int = Field(..., description="Unique identifier for the script")
    created_at: datetime = Field(
        ..., description="Timestamp when the script was created"
    )
    updated_at: datetime = Field(
        ..., description="Timestamp when the script was last updated"
    )
    created_by: Optional[str] = Field(None, description="User who created the script")

    class Config:
        from_attributes = True


class Script(ScriptInDBBase):
    """Schema for returning complete script details"""

    execution_count: int = Field(
        0, description="Number of times this script has been executed"
    )
    last_executed_at: Optional[datetime] = Field(
        None, description="Timestamp when the script was last executed"
    )
    last_status: Optional[str] = Field(
        None, description="Status of the last execution (success/failed)"
    )


class ScriptList(BaseModel):
    """Schema for listing scripts with pagination"""

    scripts: List[Script]
    pagination: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 10, "has_next": False},
        description="Pagination information",
    )


class ScriptExecutionRequest(BaseModel):
    """Schema for requesting script execution"""

    script_id: int = Field(..., ge=1, description="ID of the script to execute")
    params: Optional[Dict[str, Any]] = Field(
        None, description="Optional parameters to pass to the script"
    )
    timeout: Optional[int] = Field(
        30, ge=5, le=300, description="Execution timeout in seconds (5-300)"
    )


class ScriptExecutionResponse(BaseModel):
    """Schema for script execution response"""

    task_id: str = Field(..., description="ID of the execution task")
    script_id: int = Field(..., description="ID of the executed script")
    status: str = Field(..., description="Current status of the execution task")
    started_at: datetime = Field(..., description="Timestamp when execution started")
    result_url: str = Field(..., description="URL to retrieve execution results")
