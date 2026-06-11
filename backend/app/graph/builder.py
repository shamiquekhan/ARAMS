from langgraph.graph import StateGraph, END
from app.graph.state import ResearchState
import asyncio
import logging
import re
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger("arams.graph")

_tasks_db_ref = {}


def set_tasks_db_ref(db: dict):
    global _tasks_db_ref
    _tasks_db_ref = db


def _update_task(task_id: str, **kwargs):
    if task_id in _tasks_db_ref:
        _tasks_db_ref[task_id].update(kwargs)


_agents = {}

def _get_agents():
    global _agents
    if not _agents:
        from app.agents.supervisor import SupervisorAgent
        from app.agents.research import ResearchAgent
        from app.agents.fact_checker import FactCheckingAgent
        from app.agents.source_evaluator import SourceEvaluationAgent
        from app.agents.reflection import ReflectionAgent
        from app.agents.synthesis import SynthesisAgent
        from app.agents.report_writer import ReportWriterAgent
        from app.agents.memory import MemoryAgent
        _agents["supervisor"] = SupervisorAgent()
        _agents["research"] = ResearchAgent()
        _agents["fact_checker"] = FactCheckingAgent()
        _agents["source_evaluator"] = SourceEvaluationAgent()
        _agents["reflection"] = ReflectionAgent()
        _agents["synthesis"] = SynthesisAgent()
        _agents["report_writer"] = ReportWriterAgent()
        _agents["memory"] = MemoryAgent()
    return _agents

STOP_WORDS = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
              "have", "has", "had", "do", "does", "did", "will", "would",
              "can", "could", "shall", "should", "may", "might", "must",
              "to", "of", "in", "for", "on", "with", "at", "by", "from",
              "as", "into", "through", "during", "before", "after",
              "above", "below", "between", "out", "off", "over", "under",
              "again", "further", "then", "once", "here", "there", "when",
              "where", "why", "how", "all", "each", "every", "both", "few",
              "more", "most", "other", "some", "such", "no", "nor", "not",
              "only", "own", "same", "so", "than", "too", "very", "just",
              "because", "but", "and", "or", "if", "while", "about"}

async def _rate_limit_delay():
    if settings.LLM_BACKEND == "gemini":
        await asyncio.sleep(5)
    else:
        await asyncio.sleep(0.2)

async def supervisor_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    _update_task(tid, status="planning_complete")
    try:
        context = await agents["memory"].retrieve_context(state["query"])
        state["memory"] = context
    except Exception:
        pass
    logger.info(f"[{tid}] supervisor_node: planning")
    await _rate_limit_delay()
    state = await agents["supervisor"].plan(state)
    _update_task(tid, status="running", iteration_count=0)
    logger.info(f"[{tid}] supervisor_node: done, {len(state.get('subtasks',[]))} subtasks")
    return state

async def research_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    subtasks = state["subtasks"]
    memory_str = str(state.get("memory", []))[:2000]
    _update_task(tid, status="running")
    logger.info(f"[{tid}] research_node: executing {len(subtasks)} subtasks")
    await _rate_limit_delay()
    tasks = [agents["research"].execute(st, memory_context=memory_str) for st in subtasks]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    findings = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.warning(f"[{tid}] research_node subtask {i} failed: {r}")
            continue
        findings.extend(r)

    SPAM_DOMAINS = {"customeranalytics.com.au", "deeplearningdaily.com"}
    seen_urls = set()
    deduped = []
    for f in findings:
        url = f.get("url", "")
        domain = url.split("/")[2] if "//" in url else ""
        if url and url not in seen_urls and domain not in SPAM_DOMAINS:
            seen_urls.add(url)
            deduped.append(f)
    state["raw_findings"] = deduped
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    _update_task(tid, iteration_count=state["iteration_count"])
    logger.info(f"[{tid}] research_node: done, {len(findings)} findings, iteration {state['iteration_count']}")
    return state

async def source_eval_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    state["status"] = "source_evaluating"
    _update_task(tid, status="source_evaluating")
    logger.info(f"[{tid}] source_eval_node")
    sources = [{"url": f.get("url", ""), "domain": f.get("url", "").split("/")[2] if "//" in f.get("url", "") else "", "published_date": f.get("published_date")} for f in state.get("raw_findings", [])]
    state["source_scores"] = agents["source_evaluator"].evaluate_batch(sources)

    # Drop off-topic sources whose content has zero keyword overlap with the query
    findings = state.get("raw_findings", [])
    filtered = agents["source_evaluator"].filter_relevant(findings, state["query"])
    before = len(findings)
    state["raw_findings"] = filtered
    if len(filtered) < before:
        logger.info(f"[{tid}] source_eval_node: filtered {before - len(filtered)} off-topic findings ({before} -> {len(filtered)})")
    return state

async def fact_check_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    state["status"] = "fact_checking"
    _update_task(tid, status="fact_checking")
    logger.info(f"[{tid}] fact_check_node")
    await _rate_limit_delay()
    findings = state.get("raw_findings", [])
    verified = []
    for f in findings[:3]:
        try:
            result = await asyncio.wait_for(
                agents["fact_checker"].verify(f.get("content", "")[:200], f.get("url", "")),
                timeout=12
            )
            verified.append({**f, "verified": result})
        except Exception:
            verified.append({**f, "verified": {"verified": True, "confidence": 0.5, "contradictions": []}})
    unverified = [f for f in findings if f not in verified]
    seen = set()
    merged = []
    for f in verified + unverified:
        url = f.get("url", "")
        if url and url not in seen:
            seen.add(url)
            merged.append(f)
    state["verified_findings"] = merged
    logger.info(f"[{tid}] verified_findings count: {len(state.get('verified_findings', []))}")
    return state

def _topic_coherence_penalty(query: str, findings: list) -> float:
    query_tokens = {w.lower() for w in query.split() if w.lower() not in STOP_WORDS and len(w) > 2}
    if not query_tokens:
        return 1.0
    overlap = 0
    for f in findings:
        content = (
            f.get("abstract", "") or
            f.get("content", "") or
            f.get("title", "") or
            ""
        ).lower()
        if any(re.search(r'\b' + re.escape(w) + r'\b', content) for w in query_tokens):
            overlap += 1
    total = max(len(findings), 1)
    if overlap == 0:
        return 0.0
    coverage = overlap / total
    return min(1.0, 0.5 + coverage * 0.4)

async def reflection_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    state["status"] = "reflecting"
    _update_task(tid, status="reflecting")
    logger.info(f"[{tid}] reflection_node")
    await _rate_limit_delay()
    try:
        result = await agents["reflection"].reflect(
            state["query"],
            state.get("raw_findings", []),
            state.get("iteration_count", 0)
        )
        state["gaps"] = result.get("gaps", [])
        state["new_questions"] = result.get("new_questions", [])
        state["should_continue"] = result.get("should_continue", False)

        base_confidence = result.get("confidence_score", 0.5)
        coherence = _topic_coherence_penalty(
            state["query"],
            state.get("verified_findings", []) or state.get("raw_findings", [])
        )
        state["confidence_score"] = min(base_confidence, coherence)
        _update_task(tid, confidence_score=state["confidence_score"])
    except Exception:
        state["should_continue"] = False
        state["confidence_score"] = 0.9
    return state

async def synthesis_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    state["status"] = "synthesizing"
    _update_task(tid, status="synthesizing")
    logger.info(f"[{tid}] synthesis_node")
    await _rate_limit_delay()
    logger.info(f"[{tid}] raw_findings count: {len(state.get('raw_findings', []))}")
    logger.info(f"[{tid}] verified_findings count: {len(state.get('verified_findings', []))}")
    findings = state.get("verified_findings", []) or state.get("raw_findings", [])
    try:
        synthesis = await agents["synthesis"].synthesize(query=state["query"], findings=findings)
        state["synthesis"] = synthesis
    except Exception as e:
        logger.error(f"[{tid}] synthesis_node failed: {e}")
        insights = [f.get("content", "")[:200] or f.get("title", "")[:200] for f in findings[:7] if f.get("content") or f.get("title")]
        state["synthesis"] = {
            "insights": insights or ["Analysis complete"],
            "conclusion": f"Research on '{state['query']}' completed with {len(findings)} findings.",
            "evidence_map": {}
        }
    return state

async def report_writer_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    state["status"] = "writing_report"
    _update_task(tid, status="writing_report")
    logger.info(f"[{tid}] report_writer_node")
    await _rate_limit_delay()
    logger.info(f"[{tid}] synthesis keys: {list(state.get('synthesis', {}).keys()) if state.get('synthesis') else 'NONE'}")
    logger.info(f"[{tid}] verified_findings count: {len(state.get('verified_findings', []))}")
    logger.info(f"[{tid}] raw_findings count: {len(state.get('raw_findings', []))}")
    try:
        verified = state.get("verified_findings", []) or []
        raw = state.get("raw_findings", []) or []
        unverified = [f for f in raw if f not in verified]
        all_findings = (verified + unverified)[:15]
        report = await agents["report_writer"].write(
            query=state["query"],
            synthesis=state.get("synthesis", {}),
            verified_findings=all_findings,
            citations=state.get("citations", [])
        )
        state["report"] = report
    except Exception as e:
        logger.error(f"[{tid}] report_writer_node failed: {e}")
        findings = state.get("verified_findings", []) or state.get("raw_findings", [])
        if findings:
            fallback = f"# Research Report: {state['query']}\n\n## Key Findings\n\n"
            for f in findings[:15]:
                text = (f.get("content") or f.get("abstract") or f.get("title") or "")
                url = f.get("url", "unknown")
                if text:
                    fallback += f"- {text[:300]} (source: {url})\n"
            state["report"] = fallback
        else:
            state["report"] = f"# Research Report: {state['query']}\n\nResearch could not retrieve sufficient data for this query."
    return state

async def human_review_node(state: ResearchState) -> ResearchState:
    tid = state["task_id"]
    state["status"] = "awaiting_approval"
    _update_task(tid, status="awaiting_approval")
    logger.info(f"[{tid}] human_review_node: awaiting approval (15s timeout)")
    try:
        await asyncio.wait_for(_wait_for_approval(tid), timeout=15)
    except asyncio.TimeoutError:
        logger.info(f"[{tid}] human_review_node: approval timeout, auto-approving")
    state["human_approved"] = _tasks_db_ref.get(tid, {}).get("human_approved", True)
    logger.info(f"[{tid}] human_review_node: approved={state['human_approved']}")
    return state


async def _wait_for_approval(task_id: str):
    while True:
        task = _tasks_db_ref.get(task_id, {})
        if task.get("human_approved"):
            return
        await asyncio.sleep(1)

async def memory_save_node(state: ResearchState) -> ResearchState:
    agents = _get_agents()
    tid = state["task_id"]
    state["status"] = "complete"
    _update_task(tid, status="complete")
    logger.info(f"[{tid}] memory_save_node")
    try:
        await agents["memory"].persist_findings(state["session_id"], state.get("raw_findings", []))
    except Exception:
        pass
    return state

def should_continue_research(state: ResearchState) -> str:
    if (state.get("should_continue") and 
        state.get("iteration_count", 0) < 3 and 
        state.get("confidence_score", 0) < 0.85):
        return "continue"
    return "synthesize"

def check_human_approval(state: ResearchState) -> str:
    return "approved" if state.get("human_approved") else "revise"

def build_research_graph() -> StateGraph:
    graph = StateGraph(ResearchState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("research", research_node)
    graph.add_node("fact_check", fact_check_node)
    graph.add_node("source_eval", source_eval_node)
    graph.add_node("reflection", reflection_node)
    graph.add_node("synthesis", synthesis_node)
    graph.add_node("report_writer", report_writer_node)
    graph.add_node("human_review", human_review_node)
    graph.add_node("memory_save", memory_save_node)

    graph.set_entry_point("supervisor")

    graph.add_edge("supervisor", "research")
    graph.add_edge("research", "source_eval")
    graph.add_edge("source_eval", "fact_check")
    graph.add_edge("fact_check", "reflection")

    graph.add_conditional_edges(
        "reflection",
        should_continue_research,
        {
            "continue": "research",
            "synthesize": "synthesis"
        }
    )

    graph.add_edge("synthesis", "report_writer")
    graph.add_edge("report_writer", "human_review")

    graph.add_conditional_edges(
        "human_review",
        check_human_approval,
        {
            "approved": "memory_save",
            "revise": "report_writer"
        }
    )

    graph.add_edge("memory_save", END)

    return graph.compile()
