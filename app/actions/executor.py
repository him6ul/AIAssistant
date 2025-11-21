"""
Action executor - executes actions like creating reminders, calendar events, email drafts.
Uses AppleScript for macOS integration.
"""

import subprocess
import json
from typing import Dict, Any, Optional
from datetime import datetime
from app.actions.capabilities import ActionType, ActionRequest, ActionResponse
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ActionExecutor:
    """
    Executes actions via AppleScript and other macOS integrations.
    """
    
    def __init__(self):
        """Initialize action executor."""
        pass
    
    def _run_applescript(self, script: str) -> tuple:
        """
        Execute AppleScript.
        
        Args:
            script: AppleScript code
        
        Returns:
            Tuple of (success, output)
        """
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return True, result.stdout.strip()
            else:
                logger.error(f"AppleScript error: {result.stderr}")
                return False, result.stderr.strip()
        
        except subprocess.TimeoutExpired:
            logger.error("AppleScript execution timed out")
            return False, "Execution timed out"
        except Exception as e:
            logger.error(f"AppleScript execution failed: {e}")
            return False, str(e)
    
    async def create_reminder(
        self,
        title: str,
        body: Optional[str] = None,
        due_date: Optional[datetime] = None
    ) -> ActionResponse:
        """
        Create a reminder in macOS Reminders app.
        
        Args:
            title: Reminder title
            body: Reminder body/notes
            due_date: Due date (optional)
        
        Returns:
            Action response
        """
        logger.info(f"Creating reminder: {title}")
        
        # Build AppleScript
        script = f'tell application "Reminders"\n'
        script += f'    set newReminder to make new reminder\n'
        script += f'    set name of newReminder to "{title}"\n'
        
        if body:
            script += f'    set body of newReminder to "{body}"\n'
        
        if due_date:
            # Format date for AppleScript
            date_str = due_date.strftime("%A, %B %d, %Y at %I:%M %p")
            script += f'    set due date of newReminder to date "{date_str}"\n'
        
        script += 'end tell\n'
        
        success, output = self._run_applescript(script)
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Reminder '{title}' created successfully",
                data={"reminder_title": title}
            )
        else:
            return ActionResponse(
                success=False,
                message=f"Failed to create reminder: {output}",
                data={"error": output}
            )
    
    async def create_calendar_event(
        self,
        title: str,
        start_date: datetime,
        end_date: Optional[datetime] = None,
        description: Optional[str] = None,
        location: Optional[str] = None
    ) -> ActionResponse:
        """
        Create a calendar event in macOS Calendar app.
        
        Args:
            title: Event title
            start_date: Start date/time
            end_date: End date/time (optional, defaults to 1 hour after start)
            description: Event description
            location: Event location
        
        Returns:
            Action response
        """
        logger.info(f"Creating calendar event: {title}")
        
        if not end_date:
            from datetime import timedelta
            end_date = start_date + timedelta(hours=1)
        
        # Format dates for AppleScript
        start_str = start_date.strftime("%A, %B %d, %Y at %I:%M %p")
        end_str = end_date.strftime("%A, %B %d, %Y at %I:%M %p")
        
        script = f'tell application "Calendar"\n'
        script += f'    tell calendar "Home"\n'
        script += f'        set newEvent to make new event at end with properties {{summary:"{title}", start date:(date "{start_str}"), end date:(date "{end_str}")}}\n'
        
        if description:
            script += f'        set description of newEvent to "{description}"\n'
        
        if location:
            script += f'        set location of newEvent to "{location}"\n'
        
        script += '    end tell\n'
        script += 'end tell\n'
        
        success, output = self._run_applescript(script)
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Calendar event '{title}' created successfully",
                data={"event_title": title, "start_date": start_date.isoformat()}
            )
        else:
            return ActionResponse(
                success=False,
                message=f"Failed to create calendar event: {output}",
                data={"error": output}
            )
    
    async def create_email_draft(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None
    ) -> ActionResponse:
        """
        Create an email draft in macOS Mail app.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body
            cc: CC recipients (optional)
        
        Returns:
            Action response
        """
        logger.info(f"Creating email draft to: {to}")
        
        script = f'tell application "Mail"\n'
        script += f'    set newMessage to make new outgoing message with properties {{subject:"{subject}", content:"{body}", visible:true}}\n'
        script += f'    tell newMessage\n'
        script += f'        make new to recipient at end of to recipients with properties {{address:"{to}"}}\n'
        
        if cc:
            script += f'        make new cc recipient at end of cc recipients with properties {{address:"{cc}"}}\n'
        
        script += '    end tell\n'
        script += 'end tell\n'
        
        success, output = self._run_applescript(script)
        
        if success:
            return ActionResponse(
                success=True,
                message=f"Email draft created successfully",
                data={"to": to, "subject": subject}
            )
        else:
            # Fallback message
            return ActionResponse(
                success=False,
                message="I can't send an email directly, but I can draft it. Do you want a draft?",
                data={"error": output, "fallback": True}
            )
    
    async def execute(self, request: ActionRequest) -> ActionResponse:
        """
        Execute an action request.
        
        Args:
            request: Action request
        
        Returns:
            Action response
        """
        logger.info(f"Executing action: {request.action_type}")
        
        params = request.parameters
        
        if request.action_type == ActionType.CREATE_REMINDER:
            return await self.create_reminder(
                title=params.get("title", ""),
                body=params.get("body"),
                due_date=params.get("due_date")
            )
        
        elif request.action_type == ActionType.CREATE_CALENDAR_EVENT:
            return await self.create_calendar_event(
                title=params.get("title", ""),
                start_date=params.get("start_date"),
                end_date=params.get("end_date"),
                description=params.get("description"),
                location=params.get("location")
            )
        
        elif request.action_type == ActionType.CREATE_EMAIL_DRAFT:
            return await self.create_email_draft(
                to=params.get("to", ""),
                subject=params.get("subject", ""),
                body=params.get("body", ""),
                cc=params.get("cc")
            )
        
        else:
            return ActionResponse(
                success=False,
                message=f"Unknown action type: {request.action_type}"
            )


# Global executor instance
_executor: Optional[ActionExecutor] = None


def get_action_executor() -> ActionExecutor:
    """
    Get or create the global action executor instance.
    
    Returns:
        ActionExecutor instance
    """
    global _executor
    if _executor is None:
        _executor = ActionExecutor()
    return _executor

