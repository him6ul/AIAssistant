"""
Task extraction from emails using LLM.
"""

import json
from typing import List, Optional
from app.llm_router import get_llm_router
from app.tasks.models import Task, TaskExtractionRequest, TaskImportance, TaskClassification
from app.tasks.storage import get_task_storage
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskExtractor:
    """
    Extracts tasks from content using LLM.
    """
    
    def __init__(self):
        """Initialize task extractor."""
        self.llm_router = get_llm_router()
        self.storage = get_task_storage()
    
    def _build_extraction_prompt(self, content: str, source: str) -> str:
        """
        Build the prompt for task extraction.
        
        Args:
            content: Content to extract tasks from
            source: Source type (email/manual)
        
        Returns:
            Extraction prompt
        """
        prompt = f"""Extract tasks from the following {source} content. Return a JSON array of tasks.

Each task must have the following structure:
{{
  "title": "Brief task title",
  "description": "Detailed description or null",
  "due_date": "ISO 8601 date string or null (e.g., 2024-12-31T23:59:59)",
  "people_involved": ["person1", "person2"],
  "source": "{source}",
  "importance": "high|medium|low",
  "classification": "do|respond|delegate|follow-up|waiting-on"
}}

Classification guidelines:
- "do": Action items that need to be done
- "respond": Items requiring a response
- "delegate": Tasks to assign to others
- "follow-up": Items to follow up on later
- "waiting-on": Items waiting for someone else

Importance guidelines:
- "high": Urgent or critical items
- "medium": Normal priority items
- "low": Nice-to-have or low priority items

Content:
{content}

Return only a valid JSON array of tasks. If no tasks are found, return an empty array []."""
        
        return prompt
    
    async def extract_tasks(self, request: TaskExtractionRequest) -> List[Task]:
        """
        Extract tasks from content.
        
        Args:
            request: Extraction request with content and source
        
        Returns:
            List of extracted tasks
        """
        logger.info(f"Extracting tasks from {request.source}")
        
        prompt = self._build_extraction_prompt(request.content, request.source)
        system_prompt = "You are a task extraction assistant. Extract actionable tasks from content and return them as JSON."
        
        # Get LLM response
        response = await self.llm_router.generate(prompt, system_prompt)
        content = response.get("content", "")
        
        # Parse JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            tasks_data = json.loads(content)
            
            if not isinstance(tasks_data, list):
                logger.warning("LLM returned non-array response, wrapping in array")
                tasks_data = [tasks_data] if tasks_data else []
            
            # Convert to Task objects
            tasks = []
            for task_data in tasks_data:
                try:
                    task = Task(
                        title=task_data.get("title", "Untitled Task"),
                        description=task_data.get("description"),
                        due_date=self._parse_date(task_data.get("due_date")),
                        people_involved=task_data.get("people_involved", []),
                        source=request.source,
                        source_id=request.source_id,
                        importance=TaskImportance(task_data.get("importance", "medium")),
                        classification=TaskClassification(task_data.get("classification", "do"))
                    )
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"Failed to parse task: {task_data} - {e}")
                    continue
            
            logger.info(f"Extracted {len(tasks)} tasks from {request.source}")
            return tasks
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Response content: {content}")
            return []
    
    def _parse_date(self, date_str: Optional[str]):
        """
        Parse date string to datetime.
        
        Args:
            date_str: ISO 8601 date string or None
        
        Returns:
            datetime object or None
        """
        if not date_str:
            return None
        
        try:
            from datetime import datetime
            # Try parsing ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception as e:
            logger.warning(f"Failed to parse date: {date_str} - {e}")
            return None
    
    async def extract_and_store(self, request: TaskExtractionRequest) -> List[Task]:
        """
        Extract tasks and store them in the database.
        
        Args:
            request: Extraction request
        
        Returns:
            List of stored tasks
        """
        tasks = await self.extract_tasks(request)
        
        stored_tasks = []
        for task in tasks:
            try:
                stored_task = await self.storage.create_task(task)
                stored_tasks.append(stored_task)
            except Exception as e:
                logger.error(f"Failed to store task: {e}")
        
        logger.info(f"Stored {len(stored_tasks)} tasks")
        return stored_tasks


# Global extractor instance
_extractor: Optional[TaskExtractor] = None


def get_task_extractor() -> TaskExtractor:
    """
    Get or create the global task extractor instance.
    
    Returns:
        TaskExtractor instance
    """
    global _extractor
    if _extractor is None:
        _extractor = TaskExtractor()
    return _extractor

