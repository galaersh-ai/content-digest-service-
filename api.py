"""
FastAPI server for worker communication.
Worker polls this API to get tasks and submit results.
"""
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Config
DB_PATH = Path(__file__).parent / "data" / "queue.db"

app = FastAPI(title="Content Digest API")


class TaskResult(BaseModel):
    task_id: int
    status: str  # "completed" or "failed"
    result: Optional[str] = None
    error: Optional[str] = None


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
def root():
    """Health check."""
    return {"status": "ok", "service": "content-digest-api"}


@app.get("/tasks/pending")
def get_pending_tasks():
    """Get pending tasks for worker."""
    conn = get_db()
    tasks = conn.execute(
        "SELECT id, url, created_at FROM tasks WHERE status = 'pending' ORDER BY created_at LIMIT 10"
    ).fetchall()
    conn.close()

    return {
        "tasks": [dict(task) for task in tasks]
    }


@app.post("/tasks/{task_id}/claim")
def claim_task(task_id: int):
    """Mark task as processing."""
    conn = get_db()

    # Check task exists and is pending
    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ? AND status = 'pending'", [task_id]
    ).fetchone()

    if not task:
        conn.close()
        raise HTTPException(404, "Task not found or already claimed")

    # Claim it
    conn.execute(
        "UPDATE tasks SET status = 'processing' WHERE id = ?", [task_id]
    )
    conn.commit()
    conn.close()

    return {"claimed": True, "task": dict(task)}


@app.post("/tasks/{task_id}/result")
def submit_result(task_id: int, result: TaskResult):
    """Submit task result."""
    conn = get_db()

    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?", [task_id]
    ).fetchone()

    if not task:
        conn.close()
        raise HTTPException(404, "Task not found")

    if result.status == "completed":
        conn.execute(
            "UPDATE tasks SET status = 'completed', result = ?, completed_at = ? WHERE id = ?",
            [result.result, datetime.now(), task_id]
        )
    else:
        conn.execute(
            "UPDATE tasks SET status = 'failed', result = ? WHERE id = ?",
            [result.error, task_id]
        )

    conn.commit()
    conn.close()

    return {"updated": True}


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    """Get task by ID."""
    conn = get_db()
    task = conn.execute(
        "SELECT * FROM tasks WHERE id = ?", [task_id]
    ).fetchone()
    conn.close()

    if not task:
        raise HTTPException(404, "Task not found")

    return dict(task)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
