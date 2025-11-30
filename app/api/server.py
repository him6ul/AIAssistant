"""
FastAPI server for the AI Assistant.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel
from contextlib import asynccontextmanager
import uvicorn

from app.llm_router import get_llm_router, reset_llm_router
from app.stt import reset_stt_engine
from app.voice_listener import reset_voice_listener
from app.tts import get_tts_engine
from app.tasks.storage import get_task_storage
from app.tasks.models import Task, TaskQuery, TaskStatus, TaskClassification, TaskImportance
from app.tasks.extractor import get_task_extractor, TaskExtractionRequest
from app.actions.executor import get_action_executor, ActionRequest, ActionType
from app.ingestion.email_o365_ingestor import EmailO365Ingestor
from app.ingestion.onenote_ingestor import OneNoteIngestor
from app.ingestion.github_client import get_github_client
from app.network import get_network_monitor
from app.utils.logger import get_logger
from app.commands.handler import get_command_handler
import asyncio
import os

logger = get_logger(__name__)

# Note: Email monitor is managed in main.py, not here, to avoid duplicate instances

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - startup and shutdown."""
    # Startup
    logger.info("🚀 FastAPI lifespan: Starting up...")
    # Note: Email monitor is started in main.py to avoid duplicate instances
    # and to run in a separate thread with its own event loop
    logger.info("✅ FastAPI lifespan: Startup complete")
    yield
    
    # Shutdown
    logger.info("🛑 FastAPI lifespan: Shutting down...")
    logger.info("✅ FastAPI lifespan: Shutdown complete")

app = FastAPI(
    title="AI Personal Assistant API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    system_prompt: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    mode: str
    model: str


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    people_involved: List[str] = []
    source: str = "manual"
    importance: str = "medium"
    classification: str = "do"


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None
    importance: Optional[str] = None
    classification: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "AI Personal Assistant API", "status": "running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    network_monitor = get_network_monitor()
    is_online = await network_monitor.is_online()
    
    return {
        "status": "healthy",
        "network": "online" if is_online else "offline"
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI assistant.
    First tries command handlers for basic commands, then falls back to LLM.
    """
    try:
        # First, confirm what was received
        confirmation = f"I heard: {request.message}. Let me help you with that.\n\n"
        
        # Try command handler first for basic commands
        command_handler = get_command_handler()
        command_response = await command_handler.process(request.message)
        
        if command_response.handled:
            # Command was handled by a command handler
            response_text = command_response.response
            # Speak the response (without confirmation prefix for cleaner audio)
            try:
                tts_engine = get_tts_engine()
                loop = asyncio.get_event_loop()
                # Run TTS in executor to avoid blocking
                await loop.run_in_executor(None, tts_engine.speak, response_text)
            except Exception as e:
                logger.warning(f"TTS failed for chat response: {e}")
            
            return ChatResponse(
                response=confirmation + response_text,
                mode="command",
                model=command_response.command_type.value if command_response.command_type else "command"
            )
        
        # Fall back to LLM for complex queries
        llm_router = get_llm_router()
        response = await llm_router.generate(
            prompt=request.message,
            system_prompt=request.system_prompt
        )
        
        content = response.get("content", "")
        
        # Speak the response
        try:
            tts_engine = get_tts_engine()
            loop = asyncio.get_event_loop()
            # Run TTS in executor to avoid blocking
            await loop.run_in_executor(None, tts_engine.speak, content)
        except Exception as e:
            logger.warning(f"TTS failed for chat response: {e}")
        
        return ChatResponse(
            response=confirmation + content,
            mode=response.get("mode", "unknown"),
            model=response.get("model", "unknown")
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks", response_model=List[Task])
async def get_tasks(
    status: Optional[str] = None,
    classification: Optional[str] = None,
    importance: Optional[str] = None,
    source: Optional[str] = None,
    overdue: Optional[bool] = None,
    limit: int = 100
):
    """
    Get tasks with optional filters.
    """
    try:
        storage = get_task_storage()
        await storage.initialize()
        
        query = TaskQuery(
            status=TaskStatus(status) if status else None,
            classification=TaskClassification(classification) if classification else None,
            importance=TaskImportance(importance) if importance else None,
            source=source,
            overdue=overdue,
            limit=limit
        )
        
        tasks = await storage.query_tasks(query)
        return tasks
    except Exception as e:
        logger.error(f"Get tasks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/today", response_model=List[Task])
async def get_tasks_today():
    """Get tasks due today."""
    # Simplified - in production, filter by date
    return await get_tasks(status="open", limit=100)


@app.get("/tasks/overdue", response_model=List[Task])
async def get_tasks_overdue():
    """Get overdue tasks."""
    return await get_tasks(overdue=True, status="open")


@app.get("/tasks/waiting-on", response_model=List[Task])
async def get_tasks_waiting_on():
    """Get waiting-on tasks."""
    return await get_tasks(classification="waiting-on", status="open")


@app.get("/tasks/follow-ups", response_model=List[Task])
async def get_tasks_follow_ups():
    """Get follow-up tasks."""
    return await get_tasks(classification="follow-up", status="open")


@app.post("/tasks", response_model=Task)
async def create_task(request: TaskCreateRequest):
    """
    Create a new task.
    """
    try:
        from datetime import datetime
        
        storage = get_task_storage()
        await storage.initialize()
        
        # Handle enum conversion - accept string or enum
        importance = request.importance
        if isinstance(importance, str):
            importance = TaskImportance(importance.lower())
        elif not isinstance(importance, TaskImportance):
            importance = TaskImportance.MEDIUM
        
        classification = request.classification
        if isinstance(classification, str):
            classification = TaskClassification(classification.lower())
        elif not isinstance(classification, TaskClassification):
            classification = TaskClassification.DO
        
        task = Task(
            title=request.title,
            description=request.description,
            due_date=datetime.fromisoformat(request.due_date) if request.due_date else None,
            people_involved=request.people_involved or [],
            source=request.source or "manual",
            importance=importance,
            classification=classification
        )
        
        created_task = await storage.create_task(task)
        return created_task
    except Exception as e:
        logger.error(f"Create task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: int, request: TaskUpdateRequest):
    """
    Update a task.
    """
    try:
        from datetime import datetime
        
        storage = get_task_storage()
        await storage.initialize()
        
        task = await storage.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        if request.title:
            task.title = request.title
        if request.description is not None:
            task.description = request.description
        if request.due_date:
            task.due_date = datetime.fromisoformat(request.due_date)
        if request.status:
            task.status = TaskStatus(request.status)
        if request.importance:
            task.importance = TaskImportance(request.importance)
        if request.classification:
            task.classification = TaskClassification(request.classification)
        
        updated_task = await storage.update_task(task)
        return updated_task
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """
    Delete a task.
    """
    try:
        storage = get_task_storage()
        await storage.initialize()
        
        success = await storage.delete_task(task_id)
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {"message": "Task deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete task error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/extract")
async def extract_tasks(request: TaskExtractionRequest):
    """
    Extract tasks from content.
    """
    try:
        extractor = get_task_extractor()
        tasks = await extractor.extract_and_store(request)
        return {"tasks": tasks, "count": len(tasks)}
    except Exception as e:
        logger.error(f"Extract tasks error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/actions/execute")
async def execute_action(request: ActionRequest):
    """
    Execute an action.
    """
    try:
        executor = get_action_executor()
        response = await executor.execute(request)
        return response.dict()
    except Exception as e:
        logger.error(f"Execute action error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingestion/email/scan")
async def scan_emails():
    """
    Manually trigger email scan.
    """
    try:
        ingestor = EmailO365Ingestor()
        emails = await ingestor.ingest_unread(max_emails=50)
        
        # Extract tasks
        extractor = get_task_extractor()
        for email_data in emails:
            content = f"Subject: {email_data.get('subject', '')}\n\n{email_data.get('body', '')}"
            request = TaskExtractionRequest(
                content=content,
                source="email",
                source_id=email_data.get("id")
            )
            await extractor.extract_and_store(request)
        
        return {"emails_processed": len(emails), "status": "success"}
    except Exception as e:
        logger.error(f"Email scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ingestion/onenote/scan")
async def scan_onenote():
    """
    Manually trigger OneNote scan.
    """
    try:
        ingestor = OneNoteIngestor()
        pages = await ingestor.ingest_new_and_updated(max_pages=100)
        
        # Extract tasks
        extractor = get_task_extractor()
        for page_data in pages:
            content = f"Title: {page_data.get('title', '')}\n\n{page_data.get('content', '')}"
            request = TaskExtractionRequest(
                content=content,
                source="onenote",
                source_id=page_data.get("id")
            )
            await extractor.extract_and_store(request)
        
        return {"pages_processed": len(pages), "status": "success"}
    except Exception as e:
        logger.error(f"OneNote scan error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """
    Get system status.
    """
    try:
        network_monitor = get_network_monitor()
        is_online = await network_monitor.is_online()
        
        llm_router = get_llm_router()
        current_mode = llm_router.get_current_mode()
        
        return {
            "network": "online" if is_online else "offline",
            "llm_mode": current_mode or "unknown",
            "status": "running"
        }
    except Exception as e:
        logger.error(f"Status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# GitHub Integration Endpoints
@app.get("/github/user")
async def get_github_user():
    """
    Get authenticated GitHub user information.
    """
    try:
        github_client = get_github_client()
        if not github_client:
            raise HTTPException(status_code=503, detail="GitHub not configured. Please set GITHUB_ACCESS_TOKEN in .env")
        
        user_info = github_client.get_user_info()
        return user_info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub user error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/repos")
async def get_github_repos(username: Optional[str] = None):
    """
    Get repositories for a GitHub user.
    
    Args:
        username: GitHub username (defaults to authenticated user)
    """
    try:
        github_client = get_github_client()
        if not github_client:
            raise HTTPException(status_code=503, detail="GitHub not configured. Please set GITHUB_ACCESS_TOKEN in .env")
        
        repos = github_client.get_repositories(username)
        return {"repositories": repos, "count": len(repos)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub repos error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/repos/{repo_name}")
async def get_github_repo(repo_name: str):
    """
    Get information about a specific repository.
    
    Args:
        repo_name: Repository name (format: owner/repo or just repo for user's repo)
    """
    try:
        github_client = get_github_client()
        if not github_client:
            raise HTTPException(status_code=503, detail="GitHub not configured. Please set GITHUB_ACCESS_TOKEN in .env")
        
        repo = github_client.get_repository(repo_name)
        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository {repo_name} not found")
        
        return repo
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub repo error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/repos/{repo_name}/issues")
async def get_github_issues(repo_name: str, state: str = "open"):
    """
    Get issues for a repository.
    
    Args:
        repo_name: Repository name (format: owner/repo)
        state: Issue state ('open', 'closed', 'all')
    """
    try:
        github_client = get_github_client()
        if not github_client:
            raise HTTPException(status_code=503, detail="GitHub not configured. Please set GITHUB_ACCESS_TOKEN in .env")
        
        issues = github_client.get_issues(repo_name, state)
        return {"issues": issues, "count": len(issues)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub issues error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/github/repos/{repo_name}/issues")
async def create_github_issue(repo_name: str, title: str, body: str = "", labels: List[str] = None):
    """
    Create a new issue in a repository.
    
    Args:
        repo_name: Repository name (format: owner/repo)
        title: Issue title
        body: Issue body/description
        labels: List of label names
    """
    try:
        github_client = get_github_client()
        if not github_client:
            raise HTTPException(status_code=503, detail="GitHub not configured. Please set GITHUB_ACCESS_TOKEN in .env")
        
        issue = github_client.create_issue(repo_name, title, body, labels or [])
        if not issue:
            raise HTTPException(status_code=500, detail="Failed to create issue")
        
        return issue
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub create issue error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/config/reload")
async def reload_config():
    """
    Reload configuration from .env file.
    This resets the LLM router, STT engine, and voice listener to pick up new settings.
    """
    try:
        reset_llm_router()
        reset_stt_engine()
        reset_voice_listener()
        logger.info("Configuration reloaded from .env file")
        return {
            "status": "success",
            "message": "Configuration reloaded. New settings (API keys, wake word, etc.) will be used on next request."
        }
    except Exception as e:
        logger.error(f"Failed to reload configuration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/github/repos/{repo_name}/pulls")
async def get_github_pulls(repo_name: str, state: str = "open"):
    """
    Get pull requests for a repository.
    
    Args:
        repo_name: Repository name (format: owner/repo)
        state: PR state ('open', 'closed', 'all')
    """
    try:
        github_client = get_github_client()
        if not github_client:
            raise HTTPException(status_code=503, detail="GitHub not configured. Please set GITHUB_ACCESS_TOKEN in .env")
        
        prs = github_client.get_pull_requests(repo_name, state)
        return {"pull_requests": prs, "count": len(prs)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub pulls error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    host = os.getenv("SERVER_HOST", "localhost")
    port = int(os.getenv("SERVER_PORT", "8000"))
    
    uvicorn.run(app, host=host, port=port)

