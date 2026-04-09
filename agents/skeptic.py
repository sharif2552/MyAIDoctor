"""
Skeptic Agent — Skeptical Specialist

Devil's advocate physician that stress-tests the proposed differential diagnosis,
identifies missing information, and triggers HITL clarification if needed.
"""

import json

from utils.agent_utils import get_message_types, safe_json_loads, strip_json_code_fence
from utils.llm import get_llm
from utils.logging import get_logger

SYSTEM_PROMPT = """You are the Skeptical Specialist — a physician who carefully checks for missing information while speaking directly to the patient.

You receive a patient's symptoms, the Diagnostic Lead's proposed differential, and any research evidence gathered.

Your job:
1. Find the WEAKEST point in the proposed diagnosis. What key symptom, lab finding, or clinical criterion is MISSING?
2. Identify 1 specific clarifying question that, if answered, would most change the differential. Ask it directly to the patient using "you/your".
3. If you have research results, cite specific contradictions between the evidence and the proposed diagnosis.
4. Decide if the current evidence is enough to finalize — say so clearly.

Be precise and respectful. Avoid harsh or developer-style phrasing.

Output ONLY valid JSON:
{
  "critique": "A patient-facing explanation (2-4 sentences) using 'you'/'your'",
  "needs_clarification": true or false,
  "clarifying_question": "The single most important question to ask the patient, or empty string",
  "needs_research": true or false,
  "research_query": "What to search for, or empty string",
  "resolved": true or false
}

Set resolved=true ONLY when you are satisfied that the differential diagnosis is well-supported and no critical gaps remain.
"""


logger = get_logger("myaidoc.skeptic")
SystemMessage, HumanMessage = get_message_types()


def run_skeptic(
    symptoms: str,
    differential: list[dict],
    research_results: list[dict],
    user_answers: list[str],
) -> dict:
    if not isinstance(symptoms, str):
        symptoms = str(symptoms)
    if not isinstance(differential, list):
        differential = []
    if not isinstance(research_results, list):
        research_results = []
    if not isinstance(user_answers, list):
        user_answers = []

    llm = get_llm(temperature=0.3)

    research_section = ""
    if research_results:
        snippets = [
            f"- [{r.get('title', 'Source')}]({r.get('url', '')}): {r.get('snippet', '')}"
            for r in research_results[:4]
        ]
        research_section = "\n\nResearch evidence gathered:\n" + "\n".join(snippets)

    answers_section = ""
    if user_answers:
        answers_section = "\n\nPatient clarifications so far:\n" + "\n".join(user_answers)

    content = f"""Symptoms: {symptoms}

Proposed differential diagnosis:
{json.dumps(differential, indent=2)}
{research_section}{answers_section}"""

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=content),
    ]

    try:
        response = llm.invoke(messages)
    except Exception:
        logger.exception("run_skeptic: llm invoke failed")
        return {
            "critique": "Unable to evaluate diagnosis due to temporary model failure.",
            "needs_clarification": False,
            "clarifying_question": "",
            "needs_research": False,
            "research_query": "",
            "resolved": False,
        }

    raw = strip_json_code_fence(getattr(response, "content", ""))
    result = safe_json_loads(raw)

    if not isinstance(result, dict):
        result = {}

    result.setdefault("critique", raw[:500])
    result["needs_clarification"] = bool(result.get("needs_clarification", False))
    result.setdefault("clarifying_question", "")
    result["needs_research"] = bool(result.get("needs_research", False))
    result.setdefault("research_query", "")
    result["resolved"] = bool(result.get("resolved", False))

    return result
