from typing import TypedDict, List, Optional, Dict, Any

class ResearchState(TypedDict):
    # Core
    query: str
    session_id: str
    task_id: str

    # Planning
    task_plan: Optional[Dict[str, Any]]
    subtasks: List[Dict[str, Any]]

    # Research
    raw_findings: List[Dict[str, Any]]
    verified_findings: List[Dict[str, Any]]
    source_scores: Dict[str, float]

    # Reflection
    gaps: List[str]
    new_questions: List[str]
    iteration_count: int
    should_continue: bool
    confidence_score: float

    # Output
    synthesis: Optional[Dict[str, Any]]
    report: Optional[str]
    citations: List[Dict[str, Any]]

    # Meta
    status: str
    error: Optional[str]
    memory: List[Dict[str, Any]]
    human_approved: bool
