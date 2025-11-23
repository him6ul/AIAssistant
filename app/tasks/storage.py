"""
Task storage using SQLite database.
"""

import aiosqlite
from datetime import datetime
from typing import Optional, List
from pathlib import Path
from app.tasks.models import Task, TaskStatus, TaskQuery
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TaskStorage:
    """
    SQLite-based task storage.
    """
    
    def __init__(self, db_path: str = "./data/assistant.db"):
        """
        Initialize task storage.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._initialized = False
    
    async def initialize(self):
        """
        Initialize database schema.
        """
        if self._initialized:
            return
        
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        async with aiosqlite.connect(self.db_path) as db:
            # Create tasks table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    due_date TEXT,
                    people_involved TEXT,  -- JSON array
                    source TEXT NOT NULL,
                    source_id TEXT,
                    importance TEXT NOT NULL DEFAULT 'medium',
                    classification TEXT NOT NULL DEFAULT 'do',
                    status TEXT NOT NULL DEFAULT 'open',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT
                )
            """)
            
            # Create metadata table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            
            # Create ingestion_logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS ingestion_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    ingested_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_tasks_source ON tasks(source)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_ingestion_source ON ingestion_logs(source_type, source_id)")
            
            await db.commit()
        
        self._initialized = True
        logger.info(f"Database initialized: {self.db_path}")
    
    async def create_task(self, task: Task) -> Task:
        """
        Create a new task.
        
        Args:
            task: Task to create
        
        Returns:
            Created task with ID
        """
        await self.initialize()
        
        now = datetime.utcnow().isoformat()
        task.created_at = datetime.utcnow()
        task.updated_at = datetime.utcnow()
        
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO tasks (
                    title, description, due_date, people_involved, source, source_id,
                    importance, classification, status, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.title,
                task.description,
                task.due_date.isoformat() if task.due_date else None,
                json.dumps(task.people_involved),
                task.source,
                task.source_id,
                str(task.importance),
                str(task.classification),
                str(task.status),
                now,
                now
            ))
            await db.commit()
            task.id = cursor.lastrowid
        
        logger.info(f"Created task: {task.id} - {task.title}")
        return task
    
    async def get_task(self, task_id: int) -> Optional[Task]:
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
        
        Returns:
            Task or None if not found
        """
        await self.initialize()
        
        import json
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                
                return Task(
                    id=row["id"],
                    title=row["title"],
                    description=row["description"],
                    due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                    people_involved=json.loads(row["people_involved"]) if row["people_involved"] else [],
                    source=row["source"],
                    source_id=row["source_id"],
                    importance=row["importance"],
                    classification=row["classification"],
                    status=row["status"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
                    completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
                )
    
    async def query_tasks(self, query: TaskQuery) -> List[Task]:
        """
        Query tasks with filters.
        
        Args:
            query: Query parameters
        
        Returns:
            List of matching tasks
        """
        await self.initialize()
        
        import json
        
        conditions = []
        params = []
        
        if query.status:
            conditions.append("status = ?")
            params.append(str(query.status))
        
        if query.classification:
            conditions.append("classification = ?")
            params.append(str(query.classification))
        
        if query.importance:
            conditions.append("importance = ?")
            params.append(str(query.importance))
        
        if query.source:
            conditions.append("source = ?")
            params.append(query.source)
        
        if query.overdue:
            conditions.append("due_date < ? AND status = 'open'")
            params.append(datetime.utcnow().isoformat())
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        limit = query.limit or 100
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                f"SELECT * FROM tasks WHERE {where_clause} ORDER BY due_date ASC, created_at DESC LIMIT ?",
                params + [limit]
            ) as cursor:
                rows = await cursor.fetchall()
                
                tasks = []
                for row in rows:
                    tasks.append(Task(
                        id=row["id"],
                        title=row["title"],
                        description=row["description"],
                        due_date=datetime.fromisoformat(row["due_date"]) if row["due_date"] else None,
                        people_involved=json.loads(row["people_involved"]) if row["people_involved"] else [],
                        source=row["source"],
                        source_id=row["source_id"],
                        importance=row["importance"],
                        classification=row["classification"],
                        status=row["status"],
                        created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                        updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None,
                        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
                    ))
                
                return tasks
    
    async def update_task(self, task: Task) -> Optional[Task]:
        """
        Update a task.
        
        Args:
            task: Task with updated fields
        
        Returns:
            Updated task or None if not found
        """
        await self.initialize()
        
        if not task.id:
            return None
        
        import json
        
        now = datetime.utcnow().isoformat()
        task.updated_at = datetime.utcnow()
        
        if task.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE tasks SET
                    title = ?, description = ?, due_date = ?, people_involved = ?,
                    source = ?, source_id = ?, importance = ?, classification = ?,
                    status = ?, updated_at = ?, completed_at = ?
                WHERE id = ?
            """, (
                task.title,
                task.description,
                task.due_date.isoformat() if task.due_date else None,
                json.dumps(task.people_involved),
                task.source,
                task.source_id,
                str(task.importance),
                str(task.classification),
                str(task.status),
                now,
                task.completed_at.isoformat() if task.completed_at else None,
                task.id
            ))
            await db.commit()
        
        logger.info(f"Updated task: {task.id}")
        return task
    
    async def delete_task(self, task_id: int) -> bool:
        """
        Delete a task.
        
        Args:
            task_id: Task ID
        
        Returns:
            True if deleted, False if not found
        """
        await self.initialize()
        
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            await db.commit()
            
            return cursor.rowcount > 0
    
    async def log_ingestion(
        self,
        source_type: str,
        source_id: str,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Log an ingestion event.
        
        Args:
            source_type: Type of source (email/manual)
            source_id: Source item ID
            status: Status (success/failure)
            error_message: Error message if failed
        """
        await self.initialize()
        
        now = datetime.utcnow().isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO ingestion_logs (source_type, source_id, ingested_at, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (source_type, source_id, now, status, error_message))
            await db.commit()


# Global storage instance
_storage: Optional[TaskStorage] = None


def get_task_storage() -> TaskStorage:
    """
    Get or create the global task storage instance.
    
    Returns:
        TaskStorage instance
    """
    global _storage
    if _storage is None:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        db_path = os.getenv("DATABASE_PATH", "./data/assistant.db")
        _storage = TaskStorage(db_path)
    return _storage

