from operator import add
from typing import Annotated, TypedDict


class DiagnosticState(TypedDict):
    messages: Annotated[list, add]
    symptoms: str
    clarifying_questions: list[str]
    user_answers: list[str]
    differential_diagnosis: list[dict]
    skeptic_critique: str
    research_results: list[dict]
    reflection_count: int
    hitl_pending: bool
    hitl_question: str
    needs_research: bool
    research_query: str
    final_report: dict | None
    done: bool
