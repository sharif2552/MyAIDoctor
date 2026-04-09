"""Shared LLM factory — uses Groq (llama-3.3-70b-versatile) with env-based key."""

import os
from dotenv import load_dotenv

load_dotenv()


def get_llm(temperature: float = 0.2):
    """Return a Groq-backed ChatOpenAI-compatible LLM."""
    # Local/demo mode: a deterministic mock LLM that returns structured JSON
    # Useful for running the app without external API keys or SDKs.
    local_demo = os.getenv("LOCAL_DEMO", "0").lower() in ("1", "true", "yes")

    class MockResponse:
        def __init__(self, content: str):
            self.content = content

    class MockLLM:
        def __init__(self, temperature: float = 0.2):
            self.temperature = temperature

        def invoke(self, messages):
            # messages is a list of SystemMessage / HumanMessage objects.
            # Inspect system prompt to decide which agent is calling.
            system_txt = ""
            human_txt = ""
            try:
                for m in messages:
                    c = getattr(m, "content", str(m))
                    tname = m.__class__.__name__.lower()
                    if "systemmessage" in tname:
                        system_txt = c
                    else:
                        human_txt = c
            except Exception:
                human_txt = str(messages[-1]) if messages else ""

            # Actor mock: produce a simple differential JSON
            if "Diagnostic Lead" in system_txt or "Diagnostic Lead" in system_txt:
                out = {
                    "summary": "Probable migraine based on the provided symptoms.",
                    "differential_diagnosis": [
                        {
                            "condition": "Migraine",
                            "confidence": 72,
                            "supporting_evidence": ["Unilateral throbbing headache", "Photophobia", "Nausea"],
                            "against": ["No aura reported"],
                            "icd_hint": "G43.9",
                        },
                        {
                            "condition": "Tension-type headache",
                            "confidence": 12,
                            "supporting_evidence": ["Pressing quality"],
                            "against": ["Severe nausea and photophobia less typical"],
                            "icd_hint": "G44.2",
                        },
                    ],
                }
                return MockResponse(content=__import__("json").dumps(out))

            # Skeptic mock: produce a critique JSON
            if "Skeptical Specialist" in system_txt or "devil's advocate" in system_txt.lower():
                out = {
                    "critique": "Main gap: no information about headache triggers or focal neuro deficits.",
                    "needs_clarification": True,
                    "clarifying_question": "Have you experienced any visual changes or weakness during the headaches?",
                    "needs_research": False,
                    "research_query": "",
                    "resolved": False,
                }
                return MockResponse(content=__import__("json").dumps(out))

            # Default fallback: return the last human text as content
            return MockResponse(content=human_txt)

    if local_demo:
        return MockLLM(temperature=temperature)

    # Try real SDKs first; if not available, fall back to mock LLM
    try:
        from langchain_groq import ChatGroq

        return ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=temperature,
            api_key=os.getenv("GROQ_API_KEY"),
        )
    except Exception:
        try:
            from langchain_openai import ChatOpenAI

            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=temperature,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
        except Exception:
            # Final fallback to MockLLM so app remains runnable in offline/demo mode.
            return MockLLM(temperature=temperature)
