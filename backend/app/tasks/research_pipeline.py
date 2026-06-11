from app.graph.builder import build_research_graph
from app.memory.short_term import ShortTermMemory
import asyncio


_tasks_db: dict = {}


def set_tasks_db(db: dict):
    global _tasks_db
    _tasks_db = db


async def run_research_pipeline_async(task_id: str, query: str):
    _tasks_db[task_id]["status"] = "running"

    try:
        graph = build_research_graph()
        stm = ShortTermMemory()

        try:
            memory = stm.get_all(task_id)
        except Exception:
            memory = []

        initial_state = {
            "query": query,
            "task_id": task_id,
            "session_id": task_id,
            "subtasks": [],
            "raw_findings": [],
            "verified_findings": [],
            "source_scores": {},
            "gaps": [],
            "new_questions": [],
            "iteration_count": 0,
            "should_continue": True,
            "confidence_score": 0.0,
            "synthesis": None,
            "report": None,
            "citations": [],
            "status": "running",
            "error": None,
            "memory": memory,
            "human_approved": False,
        }

        final_state = await asyncio.wait_for(graph.ainvoke(initial_state), timeout=600)

        _tasks_db[task_id]["status"] = final_state.get("status", "complete")
        _tasks_db[task_id]["iteration_count"] = final_state.get("iteration_count", 0)
        _tasks_db[task_id]["confidence_score"] = final_state.get("confidence_score", 0.0)
        _tasks_db[task_id]["completed_at"] = final_state.get("completed_at")
        _tasks_db[task_id]["report"] = final_state.get("report", "")
        _tasks_db[task_id]["synthesis"] = final_state.get("synthesis", {})
        _tasks_db[task_id]["findings_count"] = len(final_state.get("verified_findings", [])) + len(final_state.get("raw_findings", []))

    except Exception as exc:
        _tasks_db[task_id]["status"] = "failed"
        _tasks_db[task_id]["error_message"] = str(exc)
        import traceback
        print(f"RESEARCH PIPELINE ERROR [{task_id}]: {exc}")
        traceback.print_exc()
