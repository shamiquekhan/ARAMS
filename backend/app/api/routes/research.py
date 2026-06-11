from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from app.models.schemas import ResearchRequest, TaskResponse, TaskDetailResponse
from app.tasks.research_pipeline import run_research_pipeline_async, set_tasks_db
from app.graph.builder import set_tasks_db_ref
from app.api.routes.reports import set_reports_db
from uuid import uuid4
from datetime import datetime

router = APIRouter()

tasks_db = {}

set_tasks_db(tasks_db)
set_tasks_db_ref(tasks_db)
set_reports_db(tasks_db)


@router.post("", response_model=TaskResponse)
async def create_research_task(
    request: ResearchRequest,
    background_tasks: BackgroundTasks
):
    task_id = str(uuid4())
    tasks_db[task_id] = {
        "task_id": task_id,
        "query": request.query,
        "status": "pending",
        "iteration_count": 0,
        "confidence_score": 0.0,
        "created_at": datetime.now(),
        "completed_at": None
    }

    background_tasks.add_task(run_research_pipeline_async, task_id, request.query)

    return TaskResponse(task_id=task_id, status="pending")


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task_status(task_id: str):
    task = tasks_db.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["error_message"] = task.get("error", task.get("error_message"))
    return TaskDetailResponse(**{k: v for k, v in task.items() if k in TaskDetailResponse.model_fields})
