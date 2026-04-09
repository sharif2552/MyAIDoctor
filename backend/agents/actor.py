"""
Actor Agent — Diagnostic Lead

Senior internal medicine physician persona. Proposes a differential diagnosis
(ranked list of 3-5 possible conditions with confidence scores).
"""

import json

from backend.utils.agent_utils import get_message_types, safe_json_loads, strip_json_code_fence
from backend.utils.llm import get_llm
from backend.utils.logging import get_logger

SYSTEM_PROMPT = """You are the Diagnostic Lead — a senior internal medicine physician speaking directly to the patient.

Your job is to analyze the patient's symptoms and produce a differential diagnosis: a ranked list of 3-5 possible conditions.

Rules you must follow:
- Think step by step. Consider common causes first, then rare but serious ones.
- Assign a rough confidence score (0-100) to each condition.
- Note what additional information would strengthen or weaken each diagnosis.
- If a previous critique is included, explicitly address each point and revise your assessment.
- Never dismiss a symptom as "probably nothing."
- In "summary", write in plain language for the patient, use second-person wording ("you"/"your"), and avoid clinician-to-clinician phrasing.
- If information is limited, explicitly tell the patient what details you need from them next.
- Output ONLY valid JSON — no preamble, no explanation outside the JSON.

Output format:
{
  "summary": "2-3 sentence patient-facing explanation using 'you'/'your'",
  "differential_diagnosis": [
    {
      "condition": "Condition Name",
      "confidence": 75,
      "supporting_evidence": ["symptom A matches", "..."],
      "against": ["missing fever", "..."],
      "icd_hint": "R51.9"
    }
  ]
}
"""


logger = get_logger("myaidoc.actor")
SystemMessage, HumanMessage = get_message_types()


def run_actor(symptoms_context: str, previous_dx: list[dict]) -> dict:
    if not isinstance(symptoms_context, str):
        symptoms_context = str(symptoms_context)
    if not isinstance(previous_dx, list):
        previous_dx = []

    llm = get_llm(temperature=0.2)

    prev_section = ""
    if previous_dx:
        prev_section = (
            f"\n\nYour previous differential diagnosis was:\n"
            f"{json.dumps(previous_dx, indent=2)}\n"
            f"Revise it based on new information and the critique you received."
        )

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Patient presentation:\n{symptoms_context}{prev_section}"
        ),
    ]

    try:
        response = llm.invoke(messages)
    except Exception:
        logger.exception("run_actor: llm invoke failed")
        return {
            "summary": "Unable to generate diagnostic differential at this time.",
            "differential_diagnosis": [],
        }

    raw = strip_json_code_fence(getattr(response, "content", ""))
    parsed = safe_json_loads(raw)
    if parsed:
        return parsed
    return {
        "summary": raw[:500],
        "differential_diagnosis": [],
    }
