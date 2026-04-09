"""
MyAIDoctor — Multi-Agent Medical Diagnostic System
Streamlit UI with premium dark medical theme.
"""

import os
import uuid
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ─── Page Config (must be first Streamlit call) ────────────────────────────────
st.set_page_config(
    page_title="MyAIDoctor — AI Medical Diagnostic Assistant",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Inject Premium CSS ────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global Reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Background Gradient ── */
.stApp {
    background: linear-gradient(135deg, #0A0E1A 0%, #0D1426 50%, #0A1628 100%);
    background-attachment: fixed;
}

/* ── Header ── */
.main-header {
    background: linear-gradient(90deg, rgba(0,191,165,0.15) 0%, rgba(59,130,246,0.1) 100%);
    border: 1px solid rgba(0,191,165,0.25);
    border-radius: 16px;
    padding: 28px 36px;
    margin-bottom: 28px;
    backdrop-filter: blur(10px);
    text-align: center;
}
.main-header h1 {
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #00BFA5, #3B82F6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0;
    letter-spacing: -0.5px;
}
.main-header p {
    color: #94A3B8;
    font-size: 1rem;
    margin: 0;
    font-weight: 400;
}

/* ── Chat Messages ── */
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
    margin-bottom: 24px;
}

.message-row {
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.message-row.user { flex-direction: row-reverse; }

.avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    flex-shrink: 0;
    font-weight: 600;
}
.avatar.user      { background: linear-gradient(135deg, #3B82F6, #6366F1); }
.avatar.actor     { background: linear-gradient(135deg, #00BFA5, #059669); }
.avatar.skeptic   { background: linear-gradient(135deg, #F59E0B, #EF4444); }
.avatar.researcher{ background: linear-gradient(135deg, #8B5CF6, #6366F1); }
.avatar.system    { background: linear-gradient(135deg, #475569, #334155); }

.bubble {
    max-width: 78%;
    padding: 14px 18px;
    border-radius: 16px;
    line-height: 1.6;
    font-size: 0.92rem;
}
.bubble.user {
    background: linear-gradient(135deg, #1E3A5F, #1E40AF);
    border: 1px solid rgba(59,130,246,0.3);
    color: #E2E8F0;
    border-bottom-right-radius: 4px;
}
.bubble.actor {
    background: rgba(0,191,165,0.08);
    border: 1px solid rgba(0,191,165,0.2);
    color: #E2E8F0;
    border-bottom-left-radius: 4px;
}
.bubble.skeptic {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.25);
    color: #E2E8F0;
    border-bottom-left-radius: 4px;
}
.bubble.researcher {
    background: rgba(139,92,246,0.08);
    border: 1px solid rgba(139,92,246,0.2);
    color: #E2E8F0;
    border-bottom-left-radius: 4px;
}
.bubble.system {
    background: rgba(71,85,105,0.15);
    border: 1px solid rgba(71,85,105,0.3);
    color: #94A3B8;
    font-size: 0.82rem;
    border-bottom-left-radius: 4px;
}

.agent-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 4px;
    opacity: 0.7;
}

/* ── Input Area ── */
.stTextArea textarea {
    background: rgba(17,24,39,0.9) !important;
    border: 1px solid rgba(0,191,165,0.3) !important;
    border-radius: 12px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
    padding: 14px !important;
    resize: none !important;
    transition: border-color 0.2s !important;
}
.stTextArea textarea:focus {
    border-color: #00BFA5 !important;
    box-shadow: 0 0 0 3px rgba(0,191,165,0.1) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #00BFA5, #0891B2) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 8px 20px rgba(0,191,165,0.3) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── HITL Question Card ── */
.hitl-card {
    background: linear-gradient(135deg, rgba(245,158,11,0.1), rgba(239,68,68,0.05));
    border: 1px solid rgba(245,158,11,0.4);
    border-radius: 14px;
    padding: 20px 24px;
    margin: 16px 0;
    animation: pulse-border 2s infinite;
}
@keyframes pulse-border {
    0%, 100% { border-color: rgba(245,158,11,0.4); }
    50%       { border-color: rgba(245,158,11,0.8); }
}
.hitl-card h4 {
    color: #FBBF24;
    font-size: 0.85rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 10px 0;
}
.hitl-card p {
    color: #E2E8F0;
    font-size: 1rem;
    font-weight: 500;
    margin: 0;
}

/* ── Final Report ── */
.report-card {
    background: linear-gradient(135deg, rgba(0,191,165,0.06), rgba(59,130,246,0.04));
    border: 1px solid rgba(0,191,165,0.25);
    border-radius: 16px;
    padding: 28px 32px;
    margin-top: 24px;
}
.report-card h2 {
    color: #00BFA5;
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0 0 16px 0;
    display: flex;
    align-items: center;
    gap: 10px;
}

.dx-table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
}
.dx-table th {
    background: rgba(0,191,165,0.12);
    color: #00BFA5;
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    padding: 10px 14px;
    text-align: left;
    border-bottom: 1px solid rgba(0,191,165,0.2);
}
.dx-table td {
    padding: 10px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: #CBD5E1;
    font-size: 0.9rem;
    vertical-align: top;
}
.dx-table tr:last-child td { border-bottom: none; }
.dx-table tr:hover td { background: rgba(255,255,255,0.02); }

.confidence-bar-bg {
    background: rgba(255,255,255,0.08);
    border-radius: 99px;
    height: 6px;
    width: 100%;
    overflow: hidden;
    margin-top: 4px;
}
.confidence-bar {
    height: 100%;
    border-radius: 99px;
    background: linear-gradient(90deg, #00BFA5, #3B82F6);
    transition: width 1s ease;
}

.evidence-item {
    background: rgba(139,92,246,0.06);
    border: 1px solid rgba(139,92,246,0.15);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 10px;
}
.evidence-item a {
    color: #818CF8;
    text-decoration: none;
    font-weight: 500;
    font-size: 0.9rem;
}
.evidence-item a:hover { text-decoration: underline; }
.evidence-item p {
    color: #94A3B8;
    font-size: 0.82rem;
    margin: 6px 0 0 0;
    line-height: 1.5;
}
.evidence-item .key-quote {
    color: #C4B5FD;
    font-size: 0.82rem;
    font-style: italic;
    margin-top: 6px;
    padding-left: 10px;
    border-left: 2px solid rgba(139,92,246,0.5);
}

.next-step-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 8px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: #CBD5E1;
    font-size: 0.9rem;
    line-height: 1.5;
}
.next-step-item:last-child { border-bottom: none; }
.step-number {
    background: rgba(0,191,165,0.15);
    color: #00BFA5;
    border-radius: 50%;
    width: 22px;
    height: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.72rem;
    font-weight: 700;
    flex-shrink: 0;
    margin-top: 1px;
}

.disclaimer-box {
    background: rgba(239,68,68,0.06);
    border: 1px solid rgba(239,68,68,0.2);
    border-radius: 10px;
    padding: 12px 16px;
    color: #FCA5A5;
    font-size: 0.82rem;
    margin-top: 20px;
    line-height: 1.5;
}

/* ── Sidebar ── */
.sidebar-card {
    background: rgba(17,24,39,0.6);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 16px;
}
.sidebar-card h4 {
    color: #00BFA5;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 0 0 10px 0;
}
.stat-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    color: #94A3B8;
    font-size: 0.85rem;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.stat-item:last-child { border-bottom: none; }
.stat-value {
    color: #E2E8F0;
    font-weight: 600;
}

/* ── Spinner / Loading ── */
.stSpinner { color: #00BFA5 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: #0A0E1A; }
::-webkit-scrollbar-thumb {
    background: rgba(0,191,165,0.3);
    border-radius: 99px;
}
::-webkit-scrollbar-thumb:hover { background: rgba(0,191,165,0.5); }

/* ── Text Input ── */
.stTextInput input {
    background: rgba(17,24,39,0.9) !important;
    border: 1px solid rgba(0,191,165,0.3) !important;
    border-radius: 10px !important;
    color: #E2E8F0 !important;
    font-family: 'Inter', sans-serif !important;
}
.stTextInput input:focus {
    border-color: #00BFA5 !important;
    box-shadow: 0 0 0 3px rgba(0,191,165,0.1) !important;
}

/* Hide Streamlit branding */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; }
</style>
""",
    unsafe_allow_html=True,
)

# ─── Session State Init ─────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "thread_id": str(uuid.uuid4()),
        "messages": [],          # display messages: {role, content, agent}
        "graph": None,
        "graph_state": None,
        "running": False,
        "waiting_for_hitl": False,
        "hitl_question": "",
        "hitl_config": None,
        "final_report": None,
        "reflection_count": 0,
        "sources_found": 0,
        "questions_asked": 0,
        "session_done": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ─── Load LangGraph ─────────────────────────────────────────────────────────────
@st.cache_resource
def get_graph():
    try:
        from graph.graph import build_graph
        return build_graph()
    except Exception:
        # Lightweight MockGraph for LOCAL_DEMO mode or when langgraph isn't installed.
        class MockGraph:
            def __init__(self):
                self._state = None

            def stream(self, initial_state, config=None, stream_mode=None):
                # Simulate actor -> skeptic -> report flow using local agent mocks
                from graph.nodes import intake_node, actor_node, skeptic_node, researcher_node, report_node

                state = intake_node(initial_state)
                yield {"intake": {"messages": [{"content": "[System] Intake complete."}]}}

                a = actor_node(state)
                yield {"actor": {"messages": a.get("messages", [])}}
                state.update(a)

                s = skeptic_node(state)
                yield {"skeptic": {"messages": s.get("messages", [])}}
                state.update(s)

                if state.get("done"):
                    r = report_node(state)
                    yield {"report": {"messages": r.get("messages", []), "final_report": r.get("final_report")}}
                    state.update(r)

            def get_state(self, config=None):
                class Snapshot:
                    values = {}

                return Snapshot()

        return MockGraph()

# ─── Helper: Add display message ────────────────────────────────────────────────
def add_message(role: str, content: str, agent: str = "system"):
    st.session_state.messages.append({"role": role, "content": content, "agent": agent})

# ─── Helper: Render avatar HTML ─────────────────────────────────────────────────
AGENT_META = {
    "user":       ("👤", "user"),
    "actor":      ("🩺", "actor"),
    "skeptic":    ("🔍", "skeptic"),
    "researcher": ("📚", "researcher"),
    "system":     ("⚙️", "system"),
}
AGENT_LABELS = {
    "actor":      "Diagnostic Lead",
    "skeptic":    "Skeptical Specialist",
    "researcher": "Clinical Researcher",
    "system":     "System",
    "user":       "You",
}

def render_messages():
    for msg in st.session_state.messages:
        agent = msg.get("agent", "system")
        role  = msg.get("role", "assistant")
        content = msg.get("content", "")

        # Strip agent prefix from content
        for prefix in ["[Actor] ", "[Skeptic] ", "[Researcher] ", "[System] "]:
            if content.startswith(prefix):
                content = content[len(prefix):]
                break

        icon, css_class = AGENT_META.get(agent, ("⚙️", "system"))
        label = AGENT_LABELS.get(agent, agent.title())
        row_class = "user" if role == "user" else ""

        st.markdown(
            f"""
<div class="message-row {row_class}">
  <div class="avatar {css_class}">{icon}</div>
  <div>
    <div class="agent-label" style="color: {'#94A3B8' if agent=='user' else '#00BFA5' if agent=='actor' else '#FBBF24' if agent=='skeptic' else '#818CF8' if agent=='researcher' else '#64748B'}">
        {label}
    </div>
    <div class="bubble {css_class}">{content}</div>
  </div>
</div>
""",
            unsafe_allow_html=True,
        )


def render_report(report: dict):
    """Render the final structured medical report."""
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.markdown('<h2>📋 Medical Diagnostic Report</h2>', unsafe_allow_html=True)

    # Summary
    st.markdown("**Summary of Findings**")
    st.markdown(
        f'<div style="color:#CBD5E1;font-size:0.95rem;line-height:1.7;padding:12px 0;">'
        f'{report.get("summary_of_findings", "")}</div>',
        unsafe_allow_html=True,
    )

    # Differential Diagnosis Table
    dx = report.get("differential_diagnosis", [])
    if dx:
        st.markdown("---")
        st.markdown("**Differential Diagnosis**")
        table_rows = ""
        for i, d in enumerate(dx):
            conf = d.get("confidence", 0)
            color = "#00BFA5" if conf >= 70 else "#FBBF24" if conf >= 40 else "#EF4444"
            supporting = "<br>".join(f"✓ {e}" for e in d.get("supporting_evidence", [])[:3])
            against = "<br>".join(f"✗ {e}" for e in d.get("against", [])[:2])
            table_rows += f"""
<tr>
  <td>
    <span style="color:#E2E8F0;font-weight:600">{"🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else "•"} {d.get("condition","")}</span>
    <br><span style="color:#64748B;font-size:0.78rem;font-family:'JetBrains Mono',monospace">{d.get("icd_hint","")}</span>
  </td>
  <td>
    <span style="color:{color};font-weight:700;font-size:1rem">{conf}%</span>
    <div class="confidence-bar-bg"><div class="confidence-bar" style="width:{conf}%;background:linear-gradient(90deg,{color},{color}99)"></div></div>
  </td>
  <td style="font-size:0.82rem">{supporting}</td>
  <td style="font-size:0.82rem;color:#F87171">{against}</td>
</tr>"""

        st.markdown(
            f"""<table class="dx-table">
  <thead><tr><th>Condition</th><th>Confidence</th><th>Supporting Evidence</th><th>Against</th></tr></thead>
  <tbody>{table_rows}</tbody>
</table>""",
            unsafe_allow_html=True,
        )

    # Evidence Log
    evidence = report.get("evidence_log", [])
    if evidence:
        st.markdown("---")
        st.markdown("**Evidence Sources**")
        for e in evidence:
            kq = f'<div class="key-quote">"{e["key_quote"]}"</div>' if e.get("key_quote") else ""
            st.markdown(
                f"""<div class="evidence-item">
  <a href="{e.get("url","#")}" target="_blank">📎 {e.get("title","Source")}</a>
  <p>{e.get("snippet","")[:250]}</p>
  {kq}
</div>""",
                unsafe_allow_html=True,
            )

    # Recommended Next Steps
    steps = report.get("recommended_next_steps", [])
    if steps:
        st.markdown("---")
        st.markdown("**Recommended Next Steps**")
        items_html = ""
        for i, step in enumerate(steps, 1):
            items_html += f'<div class="next-step-item"><div class="step-number">{i}</div><div>{step}</div></div>'
        st.markdown(f'<div style="padding: 8px 0">{items_html}</div>', unsafe_allow_html=True)

    # Disclaimer
    meta = report.get("metadata", {})
    st.markdown(
        f'<div class="disclaimer-box">⚠️ {meta.get("disclaimer", "")}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


# ─── Run Graph (streaming) ──────────────────────────────────────────────────────
def run_graph(initial_message: str):
    """Invoke the LangGraph with the user's message and process all events."""
    graph = get_graph()
    config = {"configurable": {"thread_id": st.session_state.thread_id}}
    st.session_state.hitl_config = config

    initial_state = {
        "messages": [{"role": "user", "content": initial_message}],
        "symptoms": "",
        "clarifying_questions": [],
        "user_answers": [],
        "differential_diagnosis": [],
        "skeptic_critique": "",
        "research_results": [],
        "reflection_count": 0,
        "hitl_pending": False,
        "hitl_question": "",
        "final_report": None,
        "done": False,
    }

    try:
        for event in graph.stream(initial_state, config=config, stream_mode="updates"):
            for node_name, node_output in event.items():
                _process_node_output(node_name, node_output)

                # Check for HITL interrupt after skeptic
                if node_name == "skeptic" and node_output.get("hitl_pending") is False:
                    # LangGraph interrupt will surface as an exception; handled in outer try
                    pass

        # Check if done after streaming completes
        snapshot = graph.get_state(config)
        _finalize_from_snapshot(snapshot)

    except Exception as exc:
        err_str = str(exc)
        # LangGraph raises GraphInterrupt for HITL
        if "GraphInterrupt" in type(exc).__name__ or "interrupt" in err_str.lower():
            _handle_interrupt(graph, config)
        else:
            st.session_state.running = False
            add_message("assistant", f"❌ Error: {err_str}", "system")


def _process_node_output(node_name: str, output: dict):
    """Extract messages from a node output and add to display."""
    msgs = output.get("messages", [])
    for m in msgs:
        content = m.get("content", "") if isinstance(m, dict) else str(m)
        agent = _node_to_agent(node_name)
        add_message("assistant", content, agent)

    # Track stats
    if output.get("reflection_count"):
        st.session_state.reflection_count = output["reflection_count"]
    if output.get("research_results"):
        st.session_state.sources_found = len(output["research_results"])
    if output.get("clarifying_questions"):
        st.session_state.questions_asked = len(output["clarifying_questions"])


def _node_to_agent(node_name: str) -> str:
    return {
        "actor":      "actor",
        "skeptic":    "skeptic",
        "researcher": "researcher",
        "report":     "system",
        "intake":     "system",
    }.get(node_name, "system")


def _handle_interrupt(graph, config):
    """Handle HITL interrupt — extract the question from graph state."""
    try:
        snapshot = graph.get_state(config)
        # LangGraph stores interrupt info in snapshot.tasks
        question = ""
        for task in getattr(snapshot, "tasks", []):
            interrupts = getattr(task, "interrupts", [])
            for interrupt_obj in interrupts:
                payload = getattr(interrupt_obj, "value", {})
                if isinstance(payload, dict):
                    question = payload.get("question", "")
                    break

        if not question:
            # Fallback: get from state directly
            state_vals = snapshot.values if hasattr(snapshot, "values") else {}
            question = state_vals.get("hitl_question", "Please provide additional information.")

        st.session_state.waiting_for_hitl = True
        st.session_state.hitl_question = question
        st.session_state.running = False
    except Exception as e:
        st.session_state.running = False
        add_message("assistant", f"Awaiting clarification from you.", "skeptic")


def _finalize_from_snapshot(snapshot):
    """After streaming ends, check if report is ready."""
    try:
        state_vals = snapshot.values if hasattr(snapshot, "values") else {}
        report = state_vals.get("final_report")
        if report:
            st.session_state.final_report = report
            st.session_state.session_done = True
    except Exception:
        pass
    st.session_state.running = False


def resume_graph(user_answer: str):
    """Resume the graph after HITL with the user's answer."""
    graph = get_graph()
    config = st.session_state.hitl_config
    if not config:
        return

    try:
        for event in graph.stream(
            {"messages": [{"role": "user", "content": user_answer}]},
            config=config,
            stream_mode="updates",
        ):
            for node_name, node_output in event.items():
                _process_node_output(node_name, node_output)

        snapshot = graph.get_state(config)
        _finalize_from_snapshot(snapshot)

    except Exception as exc:
        err_str = str(exc)
        if "GraphInterrupt" in type(exc).__name__ or "interrupt" in err_str.lower():
            _handle_interrupt(graph, config)
        else:
            st.session_state.running = False
            add_message("assistant", f"❌ Error during resume: {err_str}", "system")


# ─── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        '<div style="text-align:center;padding:16px 0 8px"><span style="font-size:2.5rem">🩺</span>'
        '<div style="color:#00BFA5;font-weight:700;font-size:1.1rem;margin-top:6px">MyAIDoctor</div>'
        '<div style="color:#64748B;font-size:0.78rem">Multi-Agent Diagnostic AI</div></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-card"><h4>Session Stats</h4>', unsafe_allow_html=True)
    st.markdown(
        f"""<div class="stat-item"><span>Reflections</span><span class="stat-value">{st.session_state.reflection_count}</span></div>
<div class="stat-item"><span>Sources Found</span><span class="stat-value">{st.session_state.sources_found}</span></div>
<div class="stat-item"><span>Questions Asked</span><span class="stat-value">{st.session_state.questions_asked}</span></div>""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-card"><h4>Agent Roles</h4>', unsafe_allow_html=True)
    st.markdown(
        """<div style="color:#94A3B8;font-size:0.82rem;line-height:1.8">
🩺 <b style="color:#00BFA5">Diagnostic Lead</b><br>
<span style="padding-left:18px">Proposes differential diagnosis</span><br><br>
🔍 <b style="color:#FBBF24">Skeptical Specialist</b><br>
<span style="padding-left:18px">Challenges & stress-tests the diagnosis</span><br><br>
📚 <b style="color:#818CF8">Clinical Researcher</b><br>
<span style="padding-left:18px">Searches medical literature (Tavily + Firecrawl)</span>
</div>""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-card"><h4>How It Works</h4>', unsafe_allow_html=True)
    st.markdown(
        """<div style="color:#94A3B8;font-size:0.82rem;line-height:1.7">
<b style="color:#CBD5E1">1.</b> Describe your symptoms in detail<br>
<b style="color:#CBD5E1">2.</b> The AI agents analyze & debate<br>
<b style="color:#CBD5E1">3.</b> You answer clarifying questions<br>
<b style="color:#CBD5E1">4.</b> Research grounds the diagnosis<br>
<b style="color:#CBD5E1">5.</b> Receive a structured medical report
</div>""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    if st.button("🔄 New Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ─── Main Content ────────────────────────────────────────────────────────────────
st.markdown(
    """<div class="main-header">
  <h1>🩺 MyAIDoctor</h1>
  <p>Advanced Multi-Agent Medical Diagnostic System — Powered by Reflexion AI & Real-Time Medical Research</p>
</div>""",
    unsafe_allow_html=True,
)

# ── Message History ──
render_messages()

# ── HITL Question Card ──
if st.session_state.waiting_for_hitl and not st.session_state.session_done:
    st.markdown(
        f"""<div class="hitl-card">
  <h4>🔍 Skeptical Specialist needs clarification</h4>
  <p>{st.session_state.hitl_question}</p>
</div>""",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([5, 1])
    with col1:
        hitl_answer = st.text_input(
            "Your answer",
            key="hitl_input",
            label_visibility="collapsed",
            placeholder="Type your answer here...",
        )
    with col2:
        if st.button("Submit", key="hitl_submit"):
            if hitl_answer.strip():
                add_message("user", hitl_answer, "user")
                st.session_state.waiting_for_hitl = False
                st.session_state.hitl_question = ""
                st.session_state.running = True
                with st.spinner("🔄 Agents processing your answer..."):
                    resume_graph(hitl_answer.strip())
                st.rerun()

# ── Final Report ──
if st.session_state.final_report and st.session_state.session_done:
    render_report(st.session_state.final_report)

# ── Input Form ──
if not st.session_state.session_done and not st.session_state.waiting_for_hitl:
    st.markdown("---")
    if not st.session_state.messages:
        st.markdown(
            """<div style="text-align:center;padding:20px 0;color:#475569;font-size:0.9rem">
  <div style="font-size:2.5rem;margin-bottom:12px">💬</div>
  <div style="color:#CBD5E1;font-size:1rem;font-weight:500;margin-bottom:6px">Describe your symptoms</div>
  <div>Be as specific as possible — include duration, severity, location, and any related symptoms.</div>
  <div style="margin-top:16px;color:#334155;font-size:0.82rem">
    Example: "I've had a throbbing headache behind my right eye for 3 days. I'm sensitive to light, feel nauseous, and the pain is worse in the morning."
  </div>
</div>""",
            unsafe_allow_html=True,
        )

    with st.form(key="symptom_form", clear_on_submit=True):
        user_input = st.text_area(
            "Describe your symptoms",
            label_visibility="collapsed",
            placeholder="Describe your symptoms in detail — include when they started, severity (1-10), location, and any triggers...",
            height=110,
            key="symptom_input",
        )
        col_l, col_r = st.columns([5, 1])
        with col_r:
            submitted = st.form_submit_button("Analyze →", use_container_width=True)

    if submitted and user_input.strip():
        add_message("user", user_input.strip(), "user")
        st.session_state.running = True
        with st.spinner("🔄 Multi-agent diagnostic team is analyzing your symptoms..."):
            run_graph(user_input.strip())
        st.rerun()
    elif submitted:
        st.warning("Please describe your symptoms before submitting.")
