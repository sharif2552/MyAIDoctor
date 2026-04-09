"""Shared LLM factory — uses Groq (llama-3.3-70b-versatile) with env-based key."""

import json
import os

from dotenv import load_dotenv

from backend.utils.logging import get_logger

load_dotenv()
logger = get_logger("myaidoc.llm")


def get_llm(temperature: float = 0.2):
    if not isinstance(temperature, (int, float)):
        temperature = 0.2
    temperature = max(0.0, min(float(temperature), 2.0))

    local_demo = os.getenv("LOCAL_DEMO", "0").lower() in ("1", "true", "yes")

    class MockResponse:
        def __init__(self, content: str):
            self.content = content

    class MockLLM:
        def __init__(self, temperature: float = 0.2):
            self.temperature = temperature

        def invoke(self, messages):
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

            if "routing planner" in system_txt.lower():
                query = human_txt.lower()
                route = "diagnostic_flow"
                reply = ""
                if any(k in query for k in ["hi", "hello", "hey", "what can you do", "help"]):
                    route = "direct_answer"
                    reply = (
                        "Hello. I can help with symptom assessment, follow-up questions, and evidence-backed summaries."
                    )
                elif any(
                    k in query
                    for k in [
                        "search",
                        "tavily",
                        "firecrawl",
                        "latest",
                        "today",
                        "news",
                        "statistics",
                        "how many",
                    ]
                ):
                    route = "tool_research"
                out = {"route": route, "reply": reply, "reason": "mock_planner"}
                return MockResponse(content=json.dumps(out))

            if "Skeptical Specialist" in system_txt or "devil's advocate" in system_txt.lower():
                out = {
                    "critique": "Main gap: no information about headache triggers or focal neuro deficits.",
                    "needs_clarification": True,
                    "clarifying_question": "Have you experienced any visual changes or weakness during the headaches?",
                    "needs_research": False,
                    "research_query": "",
                    "resolved": False,
                }
                return MockResponse(content=json.dumps(out))

            if "Diagnostic Lead" in system_txt:
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
                return MockResponse(content=json.dumps(out))

            return MockResponse(content=human_txt)

    if local_demo:
        logger.info("get_llm: using LOCAL_DEMO mock provider")
        return MockLLM(temperature=temperature)

    groq_key = os.getenv("GROQ_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if groq_key:
        try:
            from langchain_groq import ChatGroq

            logger.info("get_llm: using Groq provider")
            return ChatGroq(
                model="llama-3.3-70b-versatile",
                temperature=temperature,
            )
        except Exception:
            logger.exception("get_llm: failed to initialize Groq model")

    if openai_key:
        try:
            from langchain_openai import ChatOpenAI

            logger.info("get_llm: using OpenAI provider")
            return ChatOpenAI(
                model="gpt-4o-mini",
                temperature=temperature,
            )
        except Exception:
            logger.exception("get_llm: failed to initialize OpenAI model")

    allow_mock = os.getenv("ALLOW_MOCK_FALLBACK", "0").lower() in ("1", "true", "yes")
    if allow_mock:
        logger.warning("get_llm: using mock fallback outside demo mode")
        return MockLLM(temperature=temperature)

    raise RuntimeError(
        "No usable LLM provider configured. Set LOCAL_DEMO=1 for demo mode, "
        "or provide GROQ_API_KEY / OPENAI_API_KEY."
    )
