"""
Graph edge routing logic for the Reflexion loop.
"""

from graph.state import DiagnosticState

MAX_REFLECTIONS = 3


def after_skeptic(state: DiagnosticState) -> str:
    """
    Decide what to do after the Skeptic runs.

    Priority:
      1. If skeptic says resolved → generate report
      2. If max reflections reached → generate report
      3. If critique mentions uncertainty/research needed and no research yet → research
      4. Otherwise → loop back to actor for another reflection
    """
    if state.get("done"):
        return "report"

    reflection_count = state.get("reflection_count", 0)
    if reflection_count >= MAX_REFLECTIONS:
        return "report"

    critique = state.get("skeptic_critique", "").lower()

    needs_research = any(
        kw in critique
        for kw in ["verify", "research", "evidence", "unclear", "uncertain", "literature", "study", "studies"]
    )
    if needs_research and not state.get("research_results"):
        return "researcher"

    return "actor"
