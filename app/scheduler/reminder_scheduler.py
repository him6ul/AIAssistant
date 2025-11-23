"""
Reminder scheduler - checks due tasks and creates reminders.
"""

import asyncio
from datetime import datetime
from app.tasks.storage import get_task_storage
from app.tasks.models import TaskStatus, TaskQuery
from app.actions.executor import get_action_executor
from app.utils.logger import get_logger

logger = get_logger(__name__)


class ReminderScheduler:
    """
    Schedules reminders for due tasks.
    """
    
    def __init__(self, interval_seconds: int = 60):  # 1 minute
        """
        Initialize reminder scheduler.
        
        Args:
            interval_seconds: Interval between reminder checks
        """
        self.interval_seconds = interval_seconds
        self.storage = get_task_storage()
        self.action_executor = get_action_executor()
        self._running = False
        self._reminded_tasks: set = set()
    
    async def _check_and_remind(self):
        """
        Check for due tasks and create reminders.
        """
        try:
            # Get overdue tasks
            query = TaskQuery(overdue=True, status=TaskStatus.OPEN)
            overdue_tasks = await self.storage.query_tasks(query)
            
            # Get tasks due today
            today = datetime.utcnow().date()
            all_tasks = await self.storage.query_tasks(TaskQuery(status=TaskStatus.OPEN))
            
            due_today = [
                task for task in all_tasks
                if task.due_date and task.due_date.date() == today and task.id not in self._reminded_tasks
            ]
            
            # Create reminders for overdue and due today tasks
            for task in overdue_tasks + due_today:
                if task.id in self._reminded_tasks:
                    continue
                
                # Validate task has required fields before creating reminder
                if not task.title or not task.title.strip():
                    logger.warning(f"Skipping task {task.id}: missing or empty title")
                    continue
                
                try:
                    # Create reminder (only pass valid data)
                    reminder_body = task.description if task.description else ""
                    reminder_due_date = task.due_date if task.due_date else None
                    
                    await self.action_executor.create_reminder(
                        title=task.title.strip(),
                        body=reminder_body,
                        due_date=reminder_due_date
                    )
                    
                    self._reminded_tasks.add(task.id)
                    logger.info(f"Created reminder for task: {task.title}")
                
                except Exception as e:
                    logger.error(f"Failed to create reminder for task {task.id}: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Reminder check failed: {e}", exc_info=True)
    
    async def start(self):
        """
        Start the scheduler.
        """
        if self._running:
            logger.warning("Reminder scheduler already running")
            return
        
        self._running = True
        logger.info(f"Starting reminder scheduler (interval: {self.interval_seconds}s)")
        
        while self._running:
            await self._check_and_remind()
            await asyncio.sleep(self.interval_seconds)
    
    def stop(self):
        """
        Stop the scheduler.
        """
        self._running = False
        logger.info("Reminder scheduler stopped")

