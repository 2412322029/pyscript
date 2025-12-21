from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Possible status values for a task"""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskBase(BaseModel):
    """Base model for task data"""

    script_id: int = Field(..., ge=1, description="ID of the script being executed")
    params: Optional[Dict[str, Any]] = Field(
        None, description="Parameters passed to the script"
    )
    timeout: Optional[int] = Field(
        30, ge=5, le=300, description="Execution timeout in seconds (5-300)"
    )


class TaskCreate(TaskBase):
    """Schema for creating a new task"""

    pass


class TaskUpdate(BaseModel):
    """Schema for updating task information"""

    status: Optional[TaskStatus] = Field(None, description="Updated task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Task execution result")
    error: Optional[str] = Field(None, description="Error message if task failed")


class TaskInDBBase(TaskBase):
    """Base model for task data stored in database"""

    id: str = Field(..., description="Unique task identifier")
    status: TaskStatus = Field(TaskStatus.QUEUED, description="Current task status")
    created_at: datetime = Field(..., description="Timestamp when task was created")
    started_at: Optional[datetime] = Field(
        None, description="Timestamp when task execution started"
    )
    completed_at: Optional[datetime] = Field(
        None, description="Timestamp when task execution completed"
    )
    execution_time_ms: Optional[int] = Field(
        None, description="Execution time in milliseconds"
    )

    class Config:
        from_attributes = True


class Task(TaskInDBBase):
    """Schema for returning complete task details"""

    result: Optional[Dict[str, Any]] = Field(None, description="Task execution result")
    error: Optional[str] = Field(None, description="Error message if task failed")
    logs: Optional[List[str]] = Field(None, description="Execution logs")


class TaskList(BaseModel):
    """Schema for listing tasks with pagination"""

    tasks: List[Task]
    pagination: dict = Field(
        default_factory=lambda: {"total": 0, "skip": 0, "limit": 10, "has_next": False},
        description="Pagination information",
    )


class TaskStatusUpdate(BaseModel):
    """Schema for updating just the task status"""

    status: TaskStatus = Field(..., description="New task status")
    message: Optional[str] = Field(None, description="Status update message")

    @validator("status")
    def validate_transition(cls, v, values, **kwargs):
        """Validate valid status transitions"""
        # In a real implementation, you would check the current status
        # and validate that the transition to the new status is allowed
        return v


class TaskResult(BaseModel):
    """Schema specifically for task execution results"""

    task_id: str = Field(..., description="Task identifier")
    status: TaskStatus = Field(..., description="Final task status")
    result: Optional[Dict[str, Any]] = Field(None, description="Execution result data")
    error: Optional[str] = Field(None, description="Error details if failed")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")
    completed_at: datetime = Field(..., description="Completion timestamp")
