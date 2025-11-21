"""
Action capabilities definitions.
"""

from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel


class ActionType(str, Enum):
    """Action types."""
    CREATE_REMINDER = "create_reminder"
    CREATE_CALENDAR_EVENT = "create_calendar_event"
    CREATE_EMAIL_DRAFT = "create_email_draft"
    LIST_TASKS = "list_tasks"
    COMPLETE_TASK = "complete_task"


class ActionRequest(BaseModel):
    """Action request model."""
    action_type: ActionType
    parameters: Dict[str, Any]


class ActionResponse(BaseModel):
    """Action response model."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

