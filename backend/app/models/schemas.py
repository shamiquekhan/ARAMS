from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ResearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    depth: str = "medium"  # shallow | medium | deep
    format: str = "markdown"  # markdown | pdf | html

class TaskResponse(BaseModel):
    task_id: str
    status: str

class TaskDetailResponse(BaseModel):
    task_id: str
    query: str
    status: str
    iteration_count: int
    confidence_score: Optional[float] = None
    error_message: Optional[str] = None
    report: Optional[str] = None
    findings_count: Optional[int] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

class ReportResponse(BaseModel):
    report_id: str
    title: str
    executive_summary: str
    full_content: str
    citations: List[Dict[str, Any]]
    word_count: int
    created_at: datetime
