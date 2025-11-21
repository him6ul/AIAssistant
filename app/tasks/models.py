"""
Task data models and schemas.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class TaskImportance(str, Enum):
    """Task importance levels."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskClassification(str, Enum):
    """Task classification types."""
    DO = "do"
    RESPOND = "respond"
    DELEGATE = "delegate"
    FOLLOW_UP = "follow-up"
    WAITING_ON = "waiting-on"


class TaskStatus(str, Enum):
    """Task status."""
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Task(BaseModel):
    """Task model."""
    id: Optional[int] = None
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    due_date: Optional[datetime] = Field(None, description="Due date")
    people_involved: List[str] = Field(default_factory=list, description="People involved")
    source: str = Field(..., description="Source (email/onenote)")
    source_id: Optional[str] = Field(None, description="Source item ID")
    importance: TaskImportance = Field(TaskImportance.MEDIUM, description="Importance level")
    classification: TaskClassification = Field(TaskClassification.DO, description="Task classification")
    status: TaskStatus = Field(TaskStatus.OPEN, description="Task status")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class TaskExtractionRequest(BaseModel):
    """Request model for task extraction."""
    content: str = Field(..., description="Content to extract tasks from")
    source: str = Field(..., description="Source type (email/onenote)")
    source_id: Optional[str] = Field(None, description="Source item ID")


class TaskQuery(BaseModel):
    """Query model for filtering tasks."""
    status: Optional[TaskStatus] = None
    classification: Optional[TaskClassification] = None
    importance: Optional[TaskImportance] = None
    source: Optional[str] = None
    overdue: Optional[bool] = None
    limit: Optional[int] = Field(100, ge=1, le=1000)

