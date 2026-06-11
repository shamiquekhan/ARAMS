from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "amars",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.research_pipeline"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.research_pipeline.run_research_pipeline": {"queue": "research"}
    }
)
