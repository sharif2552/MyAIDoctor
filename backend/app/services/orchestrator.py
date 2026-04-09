import json
from uuid import UUID

from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.errors import GraphInterrupt
from langsmith import traceable
from sqlalchemy.orm import Session

from backend.agents.researcher import firecrawl_scrape_content, tavily_search_results
from backend.app.db.models import ChatMessage, ChatSession
from backend.graph.graph import build_graph
from backend.utils.agent_utils import get_message_types, safe_json_loads, strip_json_code_fence
from backend.utils.llm import get_llm
from backend.utils.logging import get_logger

logger = get_logger("myaidoc.api.orchestrator")
INTERRUPT_KEY = "__interrupt__"
SystemMessage, PlannerHumanMessage = get_message_types()
ROUTE_OPTIONS = {"direct_answer", "tool_research", "diagnostic_flow"}
PLACEHOLDER_SESSION_TITLES = frozenset({"new session", "new conversation"})


def is_placeholder_session_title(title: str | None) -> bool:
    return (title or "").strip().lower() in PLACEHOLDER_SESSION_TITLES


def refresh_session_title_if_placeholder(db: Session, session: ChatSession) -> bool:
    if not is_placeholder_session_title(session.title):
        return False
    db.flush()
    first_user = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session.id, ChatMessage.role == "user")
        .order_by(ChatMessage.created_at.asc())
        .first()
    )
    if first_user and (first_user.content or "").strip():
        session.title = first_user.content.strip().splitlines()[0][:80]
        return True
    prefix = str(session.id).replace("-", "")[:8]
    session.title = f"Chat · {prefix}"
    return True

ROUTE_PLANNER_PROMPT = """You are a routing planner for a medical assistant app.
Choose exactly one route:
- direct_answer — only for greetings, app help, or generic non-clinical chit-chat.
- tool_research — only when the user explicitly asks for a web search (e.g. tavily, firecrawl, look up online).
- diagnostic_flow — symptoms, possible diagnoses, treatment questions, medications, "what should I take", dosing, prescriptions, OTC advice (full workflow with research + skeptic).

Never use direct_answer to refuse medication or treatment questions — send those to diagnostic_flow.
Return JSON: {"route":"...","reply":"...","reason":"..."}"""

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def save_message(db: Session, session: ChatSession, role: str, content: str, agent: str = "system") -> None:
    db.add(ChatMessage(session_id=session.id, role=role, content=content, agent=agent))


def list_messages(db: Session, session_id: UUID) -> list[dict]:
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [{"role": r.role, "agent": r.agent, "content": r.content} for r in rows]


def interrupt_args_to_messages(interrupts: tuple) -> tuple[list[dict], str]:
    out: list[dict] = []
    question = ""
    for intr in interrupts:
        val = getattr(intr, "value", intr)
        if not isinstance(val, dict):
            continue
        if val.get("question"):
            question = str(val["question"])
        crit = str(val.get("critique", "")).strip()
        if crit:
            out.append({"role": "assistant", "agent": "skeptic", "content": f"[Skeptic] {crit}"})
    return out, question


def extract_interrupt_from_stream_event(event: dict) -> tuple[list[dict], str]:
    if INTERRUPT_KEY not in event:
        return [], ""
    chunk = event[INTERRUPT_KEY]
    tup = chunk if isinstance(chunk, (list, tuple)) else (chunk,)
    return interrupt_args_to_messages(tuple(tup))


def build_symptoms_context_from_history(db: Session, session_id: UUID, fallback: str) -> str:
    rows = list_messages(db, session_id)
    if not rows:
        return fallback
    tail = rows[-40:]
    parts: list[str] = []
    for m in tail:
        label = "Patient" if m["role"] == "user" else f"Assistant ({m.get('agent', 'system')})"
        parts.append(f"{label}: {m['content']}")
    text = "\n\n".join(parts)
    if len(text) > 28000:
        text = "...[earlier conversation truncated]\n\n" + text[-28000:]
    return text


@traceable(name="RoutePlanner", run_type="chain")
def plan_user_route(user_message: str, prior_user_messages: list[str]) -> dict:
    lowered = (user_message or "").lower()
    explicit_research_markers = (
        "tavily search",
        "do tavily search",
        "use tavily",
        "search with tavily",
        "firecrawl",
        "do search",
        "web search",
        "search the web",
        "look up",
    )
    if any(marker in lowered for marker in explicit_research_markers):
        return {"route": "tool_research", "reply": "", "reason": "explicit_research_command"}

    medication_or_treatment_markers = (
        "give me medicine",
        "give me medication",
        "give me meds",
        "what medicine",
        "what medication",
        "what drug",
        "what pill",
        "which medicine",
        "which medication",
        "prescription",
        "medication for",
        "medicine for",
        "meds for",
        "should i take",
        "what can i take",
        "recommend a drug",
        "otc for",
        "dosage",
        "dose of",
        "antibiotic",
        "painkiller",
        "pain killer",
    )
    if any(marker in lowered for marker in medication_or_treatment_markers):
        return {"route": "diagnostic_flow", "reply": "", "reason": "medication_or_treatment_advice"}

    llm = get_llm(temperature=0)
    context = "\n".join(f"- {msg}" for msg in prior_user_messages[-6:])
    planner_input = f"User message:\n{user_message}\n\nRecent user context:\n{context if context else '(none)'}"
    try:
        response = llm.invoke(
            [SystemMessage(content=ROUTE_PLANNER_PROMPT), PlannerHumanMessage(content=planner_input)]
        )
        parsed = safe_json_loads(strip_json_code_fence(getattr(response, "content", "")))
        route = str(parsed.get("route", "")).strip()
        if route == "direct_answer" and any(marker in lowered for marker in explicit_research_markers):
            return {"route": "tool_research", "reply": "", "reason": "override_explicit_research_command"}
        if route in ROUTE_OPTIONS:
            return {
                "route": route,
                "reply": str(parsed.get("reply", "")).strip(),
                "reason": str(parsed.get("reason", "")).strip(),
            }
    except Exception:
        logger.exception("planner failed")
    return {"route": "diagnostic_flow", "reply": "", "reason": "fallback"}


@traceable(name="ResearchToolCalling", run_type="chain")
def run_toolcalling_research(query: str) -> tuple[str, list[dict]]:
    llm = get_llm(temperature=0.1)
    if not hasattr(llm, "bind_tools"):
        return "", tavily_search_results(query, medical_only=False)

    @tool("tavily_search", return_direct=False)
    def tavily_search(query: str) -> list[dict]:
        """Search recent web results for the provided query."""
        return tavily_search_results(query=query, medical_only=False)

    @tool("firecrawl_scrape", return_direct=False)
    def firecrawl_scrape(url: str) -> str:
        """Scrape and return cleaned content from a URL."""
        return firecrawl_scrape_content(url=url)[:4000]

    tools = [tavily_search, firecrawl_scrape]
    tool_map = {t.name: t for t in tools}
    bound_llm = llm.bind_tools(tools)
    messages = [HumanMessage(content=f"Research this query and summarize with sources: {query}")]
    captured: list[dict] = []

    for _ in range(5):
        ai_msg = bound_llm.invoke(messages)
        messages.append(ai_msg)
        tool_calls = getattr(ai_msg, "tool_calls", []) or []
        if not tool_calls:
            return str(getattr(ai_msg, "content", "") or ""), captured
        for call in tool_calls:
            name = call.get("name", "")
            obj = tool_map.get(name)
            if not obj:
                continue
            args = call.get("args", {}) or {}
            result = obj.invoke(args)
            if name == "tavily_search" and isinstance(result, list) and not captured:
                captured = result
            messages.append(ToolMessage(content=json.dumps(result, ensure_ascii=False), tool_call_id=call.get("id", "")))
    return "", captured


@traceable(name="DiagnosticFlow", run_type="chain")
def run_diagnostic_flow(
    session: ChatSession, message: str, db: Session
) -> tuple[list[dict], bool, str, bool, dict | None]:
    graph = get_graph()
    config = {"configurable": {"thread_id": session.thread_id}}

    symptoms_context = build_symptoms_context_from_history(db, session.id, message)

    initial_state = {
        "messages": [{"role": "user", "content": message}],
        "symptoms": symptoms_context,
        "clarifying_questions": [],
        "user_answers": [],
        "differential_diagnosis": [],
        "skeptic_critique": "",
        "research_results": [],
        "reflection_count": 0,
        "hitl_pending": False,
        "hitl_question": "",
        "needs_research": False,
        "research_query": "",
        "needs_initial_medication_research": False,
        "post_research_route": "",
        "treatment_recommendations": [],
        "final_report": None,
        "done": False,
    }

    out_messages: list[dict] = []
    waiting = False
    question = ""
    done = False
    report = None

    try:
        for raw in graph.stream(initial_state, config=config, stream_mode="updates"):
            event = raw
            if isinstance(raw, tuple):
                if len(raw) == 2:
                    event = raw[-1]
                elif len(raw) == 3:
                    event = raw[-1]
            if not isinstance(event, dict):
                continue
            extra, q = extract_interrupt_from_stream_event(event)
            if q or extra:
                waiting = True
                out_messages.extend(extra)
                if q:
                    question = q
                continue
            for node_name, node_output in event.items():
                if node_name == INTERRUPT_KEY:
                    continue
                if not isinstance(node_output, dict):
                    continue
                for m in node_output.get("messages", []):
                    content = m.get("content", "") if isinstance(m, dict) else str(m)
                    agent = {"actor": "actor", "skeptic": "skeptic", "researcher": "researcher"}.get(
                        node_name, "system"
                    )
                    out_messages.append({"role": "assistant", "agent": agent, "content": content})
        snapshot = graph.get_state(config)
        values = getattr(snapshot, "values", {}) or {}
        report = values.get("final_report")
        done = bool(report)
        if waiting and not question:
            try:
                for task in getattr(snapshot, "tasks", []) or []:
                    for interrupt_obj in getattr(task, "interrupts", []):
                        payload = getattr(interrupt_obj, "value", {})
                        if isinstance(payload, dict) and payload.get("question"):
                            question = str(payload["question"])
                            crit = str(payload.get("critique", "")).strip()
                            if crit and not any(
                                m.get("agent") == "skeptic" for m in out_messages
                            ):
                                out_messages.append(
                                    {
                                        "role": "assistant",
                                        "agent": "skeptic",
                                        "content": f"[Skeptic] {crit}",
                                    }
                                )
                            break
                    if question:
                        break
            except Exception:
                logger.exception("interrupt fallback from snapshot failed")
    except GraphInterrupt as exc:
        waiting = True
        if exc.args and exc.args[0]:
            extra, q = interrupt_args_to_messages(tuple(exc.args[0]))
            out_messages.extend(extra)
            if q:
                question = q
    except Exception as exc:
        if "interrupt" in str(exc).lower():
            waiting = True
            try:
                snapshot = graph.get_state(config)
                for task in getattr(snapshot, "tasks", []) or []:
                    for interrupt_obj in getattr(task, "interrupts", []):
                        payload = getattr(interrupt_obj, "value", {})
                        if isinstance(payload, dict):
                            if payload.get("question"):
                                question = str(payload["question"])
                            crit = str(payload.get("critique", "")).strip()
                            if crit:
                                out_messages.append(
                                    {
                                        "role": "assistant",
                                        "agent": "skeptic",
                                        "content": f"[Skeptic] {crit}",
                                    }
                                )
                            if question:
                                break
                    if question:
                        break
            except Exception:
                logger.exception("interrupt extraction failed")
        else:
            logger.exception("diagnostic flow failed")
            out_messages.append({"role": "assistant", "agent": "system", "content": f"Error: {exc}"})

    return out_messages, waiting, question, done, report
