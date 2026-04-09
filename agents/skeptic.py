"""
Skeptic Agent — Skeptical Specialist

Devil's advocate physician that stress-tests the proposed differential diagnosis,
identifies missing information, and triggers HITL clarification if needed.
"""

import json
from utils.llm import get_llm

try:
    from langchain_core.messages import SystemMessage, HumanMessage
except Exception:
    class SystemMessage:
        def __init__(self, content: str):
            self.content = content

    class HumanMessage:
        def __init__(self, content: str):
            self.content = content

SYSTEM_PROMPT = """You are the Skeptical Specialist — a devil's advocate physician whose entire job is to stress-test a diagnosis.

You receive a patient's symptoms, the Diagnostic Lead's proposed differential, and any research evidence gathered.

Your job:
1. Find the WEAKEST point in the proposed diagnosis. What key symptom, lab finding, or clinical criterion is MISSING?
2. Identify 1 specific clarifying question that, if answered, would most change the differential. Make it a real clinical question (e.g., "Is the pain worse on inspiration?", "Have you had any recent travel?")
3. If you have research results, cite specific contradictions between the evidence and the proposed diagnosis.
4. Decide if the current evidence is enough to finalize — say so clearly.

Be harsh but precise. Vague critiques are not allowed.

Output ONLY valid JSON:
{
  "critique": "Your detailed critique (2-4 sentences)",
  "needs_clarification": true or false,
  "clarifying_question": "The single most important question to ask the patient, or empty string",
  "needs_research": true or false,
  "research_query": "What to search for, or empty string",
  "resolved": true or false
}

Set resolved=true ONLY when you are satisfied that the differential diagnosis is well-supported and no critical gaps remain.
"""


def run_skeptic(
    symptoms: str,
    differential: list[dict],
    research_results: list[dict],
    user_answers: list[str],
) -> dict:
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

    response = llm.invoke(messages)
    raw = response.content.strip()

    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {
            "critique": raw[:500],
            "needs_clarification": False,
            "clarifying_question": "",
            "needs_research": False,
            "research_query": "",
            "resolved": False,
        }

    return result
