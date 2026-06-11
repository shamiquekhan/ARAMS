from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from app.core.config import settings
from app.models.orm import ResearchTask, ResearchResult, Source, Report
from typing import Optional, List, Dict
from uuid import UUID
from datetime import datetime

class LongTermMemory:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            return session

    async def save_task(self, task: ResearchTask):
        async with self.async_session() as session:
            session.add(task)
            await session.commit()

    async def update_task_status(self, task_id: UUID, status: str, **kwargs):
        async with self.async_session() as session:
            result = await session.execute(select(ResearchTask).where(ResearchTask.id == task_id))
            task = result.scalars().first()
            if task:
                task.status = status
                for k, v in kwargs.items():
                    setattr(task, k, v)
                if status == "completed":
                    task.completed_at = datetime.utcnow()
                await session.commit()

    async def get_task(self, task_id: UUID) -> Optional[ResearchTask]:
        async with self.async_session() as session:
            result = await session.execute(select(ResearchTask).where(ResearchTask.id == task_id))
            return result.scalars().first()

    async def get_user_tasks(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[ResearchTask]:
        async with self.async_session() as session:
            result = await session.execute(
                select(ResearchTask)
                .where(ResearchTask.user_id == user_id)
                .order_by(ResearchTask.created_at.desc())
                .offset(skip)
                .limit(limit)
            )
            return list(result.scalars().all())

    async def save_report(self, report: Report):
        async with self.async_session() as session:
            session.add(report)
            await session.commit()

    async def get_report(self, task_id: UUID) -> Optional[Report]:
        async with self.async_session() as session:
            result = await session.execute(select(Report).where(Report.task_id == task_id))
            return result.scalars().first()

    async def save_result(self, result: ResearchResult):
        async with self.async_session() as session:
            session.add(result)
            await session.commit()
