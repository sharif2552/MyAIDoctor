"""
LangGraph workflow definition for the Reflexion-based Medical Diagnostic System.
"""

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from backend.graph.edges import after_skeptic
from backend.graph.nodes import actor_node, intake_node, report_node, researcher_node, skeptic_node
from backend.graph.state import DiagnosticState


def build_graph():
    """
    Build and compile the diagnostic LangGraph.

    Flow:
        START -> intake -> actor -> skeptic
                                 |- (needs_research) -> researcher -> skeptic
                                 |- (max reflections / resolved) -> report -> END
                                 \- (else) -> actor (reflexion loop)
    """
    builder = StateGraph(DiagnosticState)

    builder.add_node("intake", intake_node)
    builder.add_node("actor", actor_node)
    builder.add_node("skeptic", skeptic_node)
    builder.add_node("researcher", researcher_node)
    builder.add_node("report", report_node)

    builder.add_edge(START, "intake")
    builder.add_edge("intake", "actor")
    builder.add_edge("actor", "skeptic")
    builder.add_edge("researcher", "skeptic")
    builder.add_edge("report", END)

    builder.add_conditional_edges(
        "skeptic",
        after_skeptic,
        {
            "actor": "actor",
            "researcher": "researcher",
            "report": "report",
        },
    )

    memory = MemorySaver()
    return builder.compile(checkpointer=memory)
