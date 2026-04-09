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

When the patient asks what to take, for medication, or for treatment (OTC or prescription-class options), you MUST:
- Stay in character as their physician for this educational simulation.
- Base medication and dosing language on the "Research sources" section when it is non-empty (snippets and scraped page excerpts). Prefer phrasing like "guidelines often mention" or "typical first-line options include" and tie options to what the sources say.
- If research sources are empty, give cautious, mainstream evidence-based options anyway, and say clearly that live sources were unavailable and a clinician must confirm.
- Always include concrete options: drug or class names, typical adult OTC directions when appropriate (e.g. per label / medline-style wording), and key contraindications (pregnancy, kidney disease, bleeding risk, allergies, drug interactions).
- Never refuse with "I am not a doctor" or defer only with disclaimers — give useful clinical guidance while ending with a short reminder that a licensed prescriber must confirm and prescribe.

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
  "summary": "2-5 sentence patient-facing explanation using 'you'/'your'; include treatment direction when they asked for medicine",
  "differential_diagnosis": [
    {
      "condition": "Condition Name",
      "confidence": 75,
      "supporting_evidence": ["symptom A matches", "..."],
      "against": ["missing fever", "..."],
      "icd_hint": "R51.9"
    }
  ],
  "treatment_recommendations": [
    {
      "drug_or_class": "e.g. Ibuprofen or NSAIDs",
      "role": "first-line OTC / discuss with prescriber / etc.",
      "dosing_note": "typical adult guidance; align with research snippets when present",
      "key_cautions": ["GI bleed risk", "avoid if ..."]
    }
  ]
}

If they did not ask for treatment, "treatment_recommendations" may be an empty array [].
"""


logger = get_logger("myaidoc.actor")
SystemMessage, HumanMessage = get_message_types()


def _format_research_for_actor(research_results: list[dict]) -> str:
    if not research_results:
        return "(no research sources yet — use mainstream clinical knowledge and say sources were not loaded.)"
    lines = []
    for r in research_results[:6]:
        if not isinstance(r, dict):
            continue
        title = r.get("title", "Source")
        url = r.get("url", "")
        snip = r.get("snippet", "") or ""
        full = (r.get("full_content") or "")[:2500]
        lines.append(f"### {title}\nURL: {url}\nSnippet: {snip[:600]}")
        if full:
            lines.append(f"Scraped excerpt (Firecrawl):\n{full}\n")
    return "\n".join(lines) if lines else "(no research sources yet)"


def run_actor(
    symptoms_context: str,
    previous_dx: list[dict],
    research_results: list[dict] | None = None,
) -> dict:
    if not isinstance(symptoms_context, str):
        symptoms_context = str(symptoms_context)
    if not isinstance(previous_dx, list):
        previous_dx = []
    if research_results is None:
        research_results = []
    if not isinstance(research_results, list):
        research_results = []

    llm = get_llm(temperature=0.2)

    prev_section = ""
    if previous_dx:
        prev_section = (
            f"\n\nYour previous differential diagnosis was:\n"
            f"{json.dumps(previous_dx, indent=2)}\n"
            f"Revise it based on new information and the critique you received."
        )

    research_section = _format_research_for_actor(research_results)

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=(
                f"Patient presentation:\n{symptoms_context}{prev_section}\n\n"
                f"Research sources (Tavily + scraped pages):\n{research_section}"
            )
        ),
    ]

    try:
        response = llm.invoke(messages)
    except Exception:
        logger.exception("run_actor: llm invoke failed")
        return {
            "summary": "Unable to generate diagnostic differential at this time.",
            "differential_diagnosis": [],
            "treatment_recommendations": [],
        }

    raw = strip_json_code_fence(getattr(response, "content", ""))
    parsed = safe_json_loads(raw)
    if parsed:
        if not isinstance(parsed.get("treatment_recommendations"), list):
            parsed["treatment_recommendations"] = []
        return parsed
    return {
        "summary": raw[:500],
        "differential_diagnosis": [],
        "treatment_recommendations": [],
    }
