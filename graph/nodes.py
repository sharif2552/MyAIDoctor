"""
Graph nodes — each node is a pure function that transforms DiagnosticState.
"""

from graph.state import DiagnosticState
from agents.actor import run_actor
from agents.skeptic import run_skeptic
from agents.researcher import run_researcher
from utils.report import build_report
from langgraph.types import interrupt


def intake_node(state: DiagnosticState) -> dict:
    """Initialize state from the user's first message."""
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
        "final_report": None,
    }


def actor_node(state: DiagnosticState) -> dict:
    """Diagnostic Lead: produce or revise the differential diagnosis."""
    full_context = state["symptoms"]
    if state.get("user_answers"):
        full_context += "\n\nAdditional patient answers:\n" + "\n".join(state["user_answers"])
    if state.get("skeptic_critique"):
        full_context += f"\n\nPrevious critique to address:\n{state['skeptic_critique']}"

    result = run_actor(full_context, state.get("differential_diagnosis", []))

    # Increment reflection count here so skeptic sees the updated value
    new_count = state.get("reflection_count", 0) + 1

    return {
        "differential_diagnosis": result["differential_diagnosis"],
        "reflection_count": new_count,
        "messages": [{"role": "assistant", "content": f"[Actor] {result['summary']}"}],
    }


def skeptic_node(state: DiagnosticState) -> dict:
    """Skeptical Specialist: critique the diagnosis and optionally ask the user a question."""
    result = run_skeptic(
        state["symptoms"],
        state["differential_diagnosis"],
        state.get("research_results", []),
        state.get("user_answers", []),
    )

    if result.get("needs_clarification") and result.get("clarifying_question"):
        question = result["clarifying_question"]
        # HITL interrupt — pauses the graph and waits for user input
        user_answer = interrupt({"question": question, "type": "clarification"})
        return {
            "hitl_pending": False,
            "hitl_question": question,
            "user_answers": state.get("user_answers", []) + [f"Q: {question}\nA: {user_answer}"],
            "skeptic_critique": result["critique"],
            "clarifying_questions": state.get("clarifying_questions", []) + [question],
            "messages": [{"role": "assistant", "content": f"[Skeptic] {result['critique']}"}],
        }

    # Check if skeptic is satisfied → mark done so after_skeptic routes to report
    done = result.get("resolved", False)

    return {
        "skeptic_critique": result["critique"],
        "hitl_pending": False,
        "done": done,
        "messages": [{"role": "assistant", "content": f"[Skeptic] {result['critique']}"}],
    }


def researcher_node(state: DiagnosticState) -> dict:
    """Clinical Researcher: Tavily search + Firecrawl scrape for medical evidence."""
    results = run_researcher(state["symptoms"], state["differential_diagnosis"])
    return {
        "research_results": results,
        "messages": [
            {
                "role": "assistant",
                "content": f"[Researcher] Found {len(results)} sources: "
                + ", ".join(r.get("title", "")[:40] for r in results[:3]),
            }
        ],
    }


def report_node(state: DiagnosticState) -> dict:
    """Generate the final structured medical report."""
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
