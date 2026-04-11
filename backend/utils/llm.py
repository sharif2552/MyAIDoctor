"""
Shared LLM factory — Groq (llama-3.3-70b-versatile) with automatic key rotation.

How key rotation works
----------------------
Add as many Groq API keys as you have to .env:

    GROQ_API_KEY=gsk_...      # primary key (required)
    GROQ_API_KEY_2=gsk_...    # second key
    GROQ_API_KEY_3=gsk_...    # third key
    # and so on…

When a key hits Groq's rate limit (HTTP 429), RotatingGroqLLM automatically
switches to the next available key and retries the same request.  Each
exhausted key enters a 65-second cooldown (matches Groq's 1-minute RPM window)
before it becomes eligible again.  If every key is simultaneously exhausted a
RuntimeError is raised immediately — no endless spin.
"""

from __future__ import annotations

import json
import os
import time

from dotenv import load_dotenv

from backend.utils.logging import get_logger

load_dotenv()
logger = get_logger("myaidoc.llm")

# ── module-level rotation state (persists across get_llm() calls) ────────────
_groq_current_idx: int = 0
# maps key index → monotonic time after which it is eligible again
_groq_cooldown_until: dict[int, float] = {}

# How long (seconds) to cool a key down after hitting its rate limit.
# Groq free-tier resets per-minute quotas every 60 s; we add 5 s margin.
_COOLDOWN_SECONDS: float = 65.0


# ── helpers ───────────────────────────────────────────────────────────────────

def _collect_groq_keys() -> list[str]:
    """Return all configured Groq API keys in order."""
    keys: list[str] = []
    primary = os.getenv("GROQ_API_KEY", "").strip()
    if primary:
        keys.append(primary)
    i = 2
    while True:
        k = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
        if not k:
            break
        keys.append(k)
        i += 1
    return keys


def _is_rate_limit_error(exc: Exception) -> bool:
    """Return True if the exception looks like a Groq 429 / quota error."""
    msg = str(exc).lower()
    tname = type(exc).__name__.lower()
    return (
        "429" in msg
        or ("rate" in msg and "limit" in msg)
        or "quota" in msg
        or "too many requests" in msg
        or "ratelimit" in tname
        or "rate_limit" in tname
    )


# ── rotating wrapper ──────────────────────────────────────────────────────────

class RotatingGroqLLM:
    """
    Wraps multiple ChatGroq clients (one per API key).

    On every invoke() call:
    1. Try the current key.
    2. If a rate-limit error is raised, mark that key on cooldown, rotate to
       the next available key, and retry — up to len(keys) attempts.
    3. If all keys are on cooldown, raise RuntimeError immediately.
    """

    def __init__(self, clients: list, key_count: int) -> None:
        self._clients = clients          # list[ChatGroq]
        self._key_count = key_count

    # -- internal helpers -----------------------------------------------------

    @staticmethod
    def _current_idx() -> int:
        return _groq_current_idx

    @staticmethod
    def _is_available(idx: int) -> bool:
        return time.monotonic() >= _groq_cooldown_until.get(idx, 0.0)

    @staticmethod
    def _mark_cooldown(idx: int) -> None:
        _groq_cooldown_until[idx] = time.monotonic() + _COOLDOWN_SECONDS
        logger.warning(
            "Groq key #%d is rate-limited — cooling down for %.0f s.",
            idx + 1,
            _COOLDOWN_SECONDS,
        )

    # -- public interface ------------------------------------------------------

    def invoke(self, messages, **kwargs):
        global _groq_current_idx

        last_exc: Exception | None = None

        for _attempt in range(self._key_count):
            idx = _groq_current_idx

            if not self._is_available(idx):
                # Current key still cooling down — find the next available one
                rotated = self._try_rotate()
                if not rotated:
                    wait = min(
                        _groq_cooldown_until.get(i, 0) - time.monotonic()
                        for i in range(self._key_count)
                    )
                    raise RuntimeError(
                        f"All {self._key_count} Groq API keys are rate-limited. "
                        f"Earliest key available in {max(wait, 0):.0f} s."
                    )
                idx = _groq_current_idx

            try:
                result = self._clients[idx].invoke(messages, **kwargs)
                return result

            except Exception as exc:
                if _is_rate_limit_error(exc):
                    last_exc = exc
                    self._mark_cooldown(idx)
                    if not self._try_rotate():
                        raise RuntimeError(
                            f"All {self._key_count} Groq API key(s) are rate-limited. "
                            "Add more keys (GROQ_API_KEY_3, …) or wait for the cooldown."
                        ) from exc
                    # brief pause so we don't hammer Groq's auth endpoint
                    time.sleep(0.3)
                else:
                    raise

        raise RuntimeError(
            f"Exhausted all {self._key_count} Groq key rotation attempts."
        ) from last_exc

    def try_rotate(self):
        self._try_rotate()

    def _try_rotate(self) -> bool:
        global _groq_current_idx
        for step in range(1, self._key_count):
            candidate = (_groq_current_idx + step) % self._key_count
            if self._is_available(candidate):
                prev = _groq_current_idx
                _groq_current_idx = candidate
                logger.info(
                    "Groq key rotation: #%d → #%d (%d key(s) configured).",
                    prev + 1,
                    candidate + 1,
                    self._key_count,
                )
                return True
        return False

    # Forward any other LangChain attribute access to the current client
    def __getattr__(self, name: str):
        return getattr(self._clients[_groq_current_idx], name)


# ── mock LLM (LOCAL_DEMO mode) ────────────────────────────────────────────────

class _MockResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _MockLLM:
    def __init__(self, temperature: float = 0.2) -> None:
        self.temperature = temperature

    def invoke(self, messages, **_):
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
                reply = "Hello. I can help with symptom assessment, follow-up questions, and evidence-backed summaries."
            elif any(k in query for k in ["medicine", "medication", "prescription", "what drug",
                                           "what pill", "antibiotic", "dosage", "should i take"]):
                route = "diagnostic_flow"
            elif any(k in query for k in ["search", "tavily", "firecrawl", "latest",
                                           "today", "news", "statistics", "how many"]):
                route = "tool_research"
            return _MockResponse(content=json.dumps({"route": route, "reply": reply, "reason": "mock_planner"}))

        if "Skeptical Specialist" in system_txt or "devil's advocate" in system_txt.lower():
            return _MockResponse(content=json.dumps({
                "critique": "Main gap: no information about headache triggers or focal neuro deficits.",
                "needs_clarification": True,
                "clarifying_question": "Have you experienced any visual changes or weakness during the headaches?",
                "needs_research": False,
                "research_query": "",
                "resolved": False,
            }))

        if "Diagnostic Lead" in system_txt:
            return _MockResponse(content=json.dumps({
                "summary": "Probable migraine based on the provided symptoms.",
                "differential_diagnosis": [{
                    "condition": "Migraine",
                    "confidence": 72,
                    "supporting_evidence": ["Unilateral throbbing headache", "Photophobia", "Nausea"],
                    "against": ["No aura reported"],
                    "icd_hint": "G43.9",
                }],
                "treatment_recommendations": [],
            }))

        return _MockResponse(content=human_txt)


# ── public factory ────────────────────────────────────────────────────────────

def get_llm(temperature: float = 0.2):
    """
    Return an LLM instance ready for `.invoke(messages)`.

    Priority:
      1. LOCAL_DEMO=1  → _MockLLM  (no API calls)
      2. GROQ_API_KEY (+ optional GROQ_API_KEY_2/3/…) → RotatingGroqLLM
      3. OPENAI_API_KEY → ChatOpenAI (single key, no rotation)
      4. ALLOW_MOCK_FALLBACK=1 → _MockLLM warning
      5. RuntimeError
    """
    if not isinstance(temperature, (int, float)):
        temperature = 0.2
    temperature = max(0.0, min(float(temperature), 2.0))

    # ── 1. local demo ─────────────────────────────────────────────────────────
    if os.getenv("LOCAL_DEMO", "0").lower() in ("1", "true", "yes"):
        logger.info("get_llm: LOCAL_DEMO — using mock provider")
        return _MockLLM(temperature=temperature)

    # ── 2. Groq (with key rotation) ───────────────────────────────────────────
    groq_keys = _collect_groq_keys()
    if groq_keys:
        try:
            from langchain_groq import ChatGroq

            clients = [
                ChatGroq(
                    model="llama-3.3-70b-versatile",
                    temperature=temperature,
                    api_key=key,
                )
                for key in groq_keys
            ]

            if len(groq_keys) == 1:
                logger.info("get_llm: Groq provider — 1 key configured (no rotation)")
            else:
                logger.info(
                    "get_llm: Groq provider — %d keys configured, rotation active",
                    len(groq_keys),
                )

            return RotatingGroqLLM(clients=clients, key_count=len(groq_keys))

        except Exception:
            logger.exception("get_llm: failed to initialise Groq client(s)")

    # ── 3. OpenAI fallback ────────────────────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    if openai_key:
        try:
            from langchain_openai import ChatOpenAI

            logger.info("get_llm: OpenAI provider")
            return ChatOpenAI(model="gpt-4o-mini", temperature=temperature)
        except Exception:
            logger.exception("get_llm: failed to initialise OpenAI client")

    # ── 4. mock fallback ──────────────────────────────────────────────────────
    if os.getenv("ALLOW_MOCK_FALLBACK", "0").lower() in ("1", "true", "yes"):
        logger.warning("get_llm: no real provider — using mock fallback")
        return _MockLLM(temperature=temperature)

    raise RuntimeError(
        "No usable LLM provider configured. "
        "Set GROQ_API_KEY (+ optional GROQ_API_KEY_2, GROQ_API_KEY_3, …), "
        "OPENAI_API_KEY, or LOCAL_DEMO=1."
    )
