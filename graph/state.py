from typing import TypedDict, Annotated
from operator import add


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
    final_report: dict | None
    done: bool
