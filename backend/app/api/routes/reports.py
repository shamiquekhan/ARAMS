from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ReportResponse
from datetime import datetime

router = APIRouter()

_tasks_db_reports = {}


def set_reports_db(db: dict):
    global _tasks_db_reports
    _tasks_db_reports = db


@router.get("/{task_id}", response_model=ReportResponse)
async def get_report(task_id: str):
    task = _tasks_db_reports.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    report_content = task.get("report")
    if not report_content:
        raise HTTPException(status_code=404, detail="Report not ready yet")
    return ReportResponse(
        report_id=task_id,
        title=f"Research Report: {task.get('query', '')[:60]}",
        executive_summary=task.get("synthesis", {}).get("conclusion", "")[:200] if task.get("synthesis") else "",
        full_content=report_content,
        citations=task.get("citations", []),
        word_count=len(report_content.split()),
        created_at=task.get("created_at", datetime.now())
    )


@router.post("/{task_id}/approve")
async def approve_report(task_id: str):
    task = _tasks_db_reports.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task["human_approved"] = True
    return {"message": "Report approved"}
