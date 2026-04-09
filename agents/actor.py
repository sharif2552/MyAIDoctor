"""
Actor Agent — Diagnostic Lead

Senior internal medicine physician persona. Proposes a differential diagnosis
(ranked list of 3-5 possible conditions with confidence scores).
"""

import json
from utils.llm import get_llm

# Safer import: langchain_core may not be installed in demo environments.
try:
    from langchain_core.messages import SystemMessage, HumanMessage
except Exception:
    # Lightweight stand-ins used only to carry a `content` attribute.
    class SystemMessage:
        def __init__(self, content: str):
            self.content = content

    class HumanMessage:
        def __init__(self, content: str):
            self.content = content

SYSTEM_PROMPT = """You are the Diagnostic Lead — a senior internal medicine physician.

Your job is to analyze the patient's symptoms and produce a differential diagnosis: a ranked list of 3-5 possible conditions.

Rules you must follow:
- Think step by step. Consider common causes first, then rare but serious ones.
- Assign a rough confidence score (0-100) to each condition.
- Note what additional information would strengthen or weaken each diagnosis.
- If a previous critique is included, explicitly address each point and revise your assessment.
- Never dismiss a symptom as "probably nothing."
- Output ONLY valid JSON — no preamble, no explanation outside the JSON.

Output format:
{
  "summary": "2-3 sentence clinical impression",
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


def run_actor(symptoms_context: str, previous_dx: list[dict]) -> dict:
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

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "summary": raw[:500],
            "differential_diagnosis": [],
        }
