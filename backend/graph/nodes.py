"""
Graph nodes — each node is a pure function that transforms DiagnosticState.
"""

from langgraph.types import interrupt

from backend.agents.actor import run_actor
from backend.agents.researcher import run_researcher
from backend.agents.skeptic import run_skeptic
from backend.graph.state import DiagnosticState
from backend.utils.logging import get_logger
from backend.utils.report import build_report

logger = get_logger("myaidoc.graph.nodes")


def intake_node(state: DiagnosticState) -> dict:
    seed_symptoms = state.get("symptoms", "")
    if seed_symptoms:
        content = str(seed_symptoms)
    else:
        last_msg = state["messages"][-1] if state["messages"] else ""
        content = last_msg.get("content", "") if isinstance(last_msg, dict) else str(last_msg)
    return {
        "symptoms": content,
        "reflection_count": 0,
        "hitl_pending": False,
        "hitl_question": "",
        "done": False,
        "differential_diagnosis": [],
        "skeptic_critique": "",
        "research_results": [],
        "clarifying_questions": [],
        "user_answers": [],
        "needs_research": False,
        "research_query": "",
        "final_report": None,
    }


def actor_node(state: DiagnosticState) -> dict:
    full_context = state["symptoms"]
    if state.get("user_answers"):
        full_context += "\n\nAdditional patient answers:\n" + "\n".join(state["user_answers"])
    if state.get("skeptic_critique"):
        full_context += f"\n\nPrevious critique to address:\n{state['skeptic_critique']}"

    result = run_actor(full_context, state.get("differential_diagnosis", []))

    new_count = state.get("reflection_count", 0) + 1

    return {
        "differential_diagnosis": result.get("differential_diagnosis", []),
        "reflection_count": new_count,
        "messages": [
            {"role": "assistant", "content": f"[Actor] {result.get('summary','(no summary)')}"}
        ],
    }


def skeptic_node(state: DiagnosticState) -> dict:
    try:
        result = run_skeptic(
            state["symptoms"],
            state["differential_diagnosis"],
            state.get("research_results", []),
            state.get("user_answers", []),
        )
    except Exception:
        logger.exception("skeptic_node: run_skeptic failed")
        result = {}

    if not isinstance(result, dict):
        logger.error("skeptic_node: invalid result type=%s", type(result).__name__)
        result = {}

    critique = str(result.get("critique", "Unable to produce critique at this time."))

    if result.get("needs_clarification") and result.get("clarifying_question"):
        question = result["clarifying_question"]
        user_answer = interrupt(
            {"question": question, "type": "clarification", "critique": critique}
        )
        return {
            "hitl_pending": False,
            "hitl_question": question,
            "user_answers": state.get("user_answers", []) + [f"Q: {question}\nA: {user_answer}"],
            "skeptic_critique": critique,
            "needs_research": bool(result.get("needs_research", False)),
            "research_query": str(result.get("research_query", "")),
            "clarifying_questions": state.get("clarifying_questions", []) + [question],
            "messages": [],
        }

    done = result.get("resolved", False)

    return {
        "skeptic_critique": critique,
        "hitl_pending": False,
        "needs_research": bool(result.get("needs_research", False)),
        "research_query": str(result.get("research_query", "")),
        "done": done,
        "messages": [{"role": "assistant", "content": f"[Skeptic] {critique}"}],
    }


def researcher_node(state: DiagnosticState) -> dict:
    results = run_researcher(
        state["symptoms"],
        state["differential_diagnosis"],
        state.get("research_query", ""),
    )
    return {
        "research_results": results,
        "needs_research": False,
        "research_query": "",
        "messages": [
            {
                "role": "assistant",
                "content": f"[Researcher] Found {len(results)} sources: "
                + ", ".join(r.get("title", "")[:40] for r in results[:3]),
            }
        ],
    }


def report_node(state: DiagnosticState) -> dict:
    report = build_report(
        state["symptoms"],
        state["differential_diagnosis"],
        state.get("research_results", []),
        state.get("user_answers", []),
        state.get("skeptic_critique", ""),
    )
    return {
        "final_report": report,
        "done": True,
        "messages": [{"role": "assistant", "content": "[System] Final medical report generated."}],
    }
