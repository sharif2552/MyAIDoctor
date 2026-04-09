"""
Graph edge routing logic for the Reflexion loop.
"""

import os

from backend.graph.state import DiagnosticState

try:
    MAX_REFLECTIONS = int(os.getenv("MAX_REFLECTIONS", "3"))
except ValueError:
    MAX_REFLECTIONS = 3


def after_skeptic(state: DiagnosticState) -> str:
    if state.get("done"):
        return "report"

    reflection_count = state.get("reflection_count", 0)
    if reflection_count >= MAX_REFLECTIONS:
        return "report"

    if state.get("needs_research"):
        return "researcher"

    return "actor"
