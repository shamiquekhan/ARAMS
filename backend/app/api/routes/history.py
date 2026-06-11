from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.database import get_db
from app.models.orm import ResearchTask
from app.models.schemas import TaskDetailResponse
from typing import List

router = APIRouter()

@router.get("", response_model=List[TaskDetailResponse])
async def get_history(skip: int = 0, limit: int = 20, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ResearchTask)
        .order_by(ResearchTask.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tasks = result.scalars().all()
    return [
        TaskDetailResponse(
            task_id=str(t.id),
            query=t.query,
            status=t.status,
            iteration_count=t.iteration_count or 0,
            confidence_score=t.confidence_score,
            created_at=t.created_at,
            completed_at=t.completed_at
        )
        for t in tasks
    ]
