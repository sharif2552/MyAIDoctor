# ruff: noqa: B008
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from langgraph.errors import GraphInterrupt
from langgraph.types import Command
from langsmith import get_current_run_tree, traceable
from langsmith.run_helpers import LangSmithExtra
from langsmith.run_trees import RunTree
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.models import ChatSession, User
from backend.app.db.session import get_db
from backend.app.schemas import ChatResponse, HitlRequest, MessageOut, MessageRequest
from backend.app.services.orchestrator import (
    extract_interrupt_from_stream_event,
    get_graph,
    interrupt_args_to_messages,
    list_messages,
    plan_user_route,
    refresh_session_title_if_placeholder,
    run_diagnostic_flow,
    run_toolcalling_research,
    save_message,
)

router = APIRouter(prefix="/chat", tags=["chat"])
INTERRUPT_KEY = "__interrupt__"


def _chat_trace_process_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    s = inputs.get("session")
    if s is not None:
        out["session_id"] = str(s.id)
        out["thread_id"] = getattr(s, "thread_id", "")
    u = inputs.get("current_user")
    if u is not None:
        out["user_id"] = str(u.id)
    p = inputs.get("payload")
    if p is not None and hasattr(p, "message"):
        msg = p.message
        out["user_message_chars"] = len(msg)
        out["user_message_preview"] = msg[:3000] + ("..." if len(msg) > 3000 else "")
    return out


def _chat_trace_process_outputs(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"output_type": type(result).__name__}
    return {
        "assistant_message_count": len(result.get("assistant_messages", [])),
        "waiting_for_hitl": result.get("waiting_for_hitl"),
        "session_done": result.get("session_done"),
        "hitl_question_preview": (result.get("hitl_question") or "")[:400],
        "has_final_report": result.get("final_report") is not None,
    }


@traceable(
    name="chat_message",
    run_type="chain",
    tags=["myaidoctor", "api"],
    process_inputs=_chat_trace_process_inputs,
    process_outputs=_chat_trace_process_outputs,
)
def run_chat_message_traced(
    db: Session,
    session: ChatSession,
    payload: MessageRequest,
    current_user: User,
) -> dict[str, Any]:
    out: list[dict] = []
    final_report = None
    waiting = False
    question = ""
    session_done = False

    prior_messages = [m["content"] for m in list_messages(db, session.id) if m["role"] == "user"]
    decision = plan_user_route(payload.message, prior_messages)
    route = decision.get("route", "diagnostic_flow")

    if route == "direct_answer":
        reply = decision.get("reply", "").strip() or "Can you share more details so I can help better?"
        out.append({"role": "assistant", "agent": "system", "content": reply})
        save_message(db, session, "assistant", reply, "system")
    elif route == "tool_research":
        answer, results = run_toolcalling_research(payload.message)
        if answer.strip():
            save_message(db, session, "assistant", answer.strip(), "researcher")
            out.append({"role": "assistant", "agent": "researcher", "content": answer.strip()})
        if results:
            summary = f"I searched the web and found {len(results)} sources."
            save_message(db, session, "assistant", summary, "researcher")
            out.append({"role": "assistant", "agent": "researcher", "content": summary})
            for i, item in enumerate(results[:3], 1):
                line = f"{i}. {item.get('title','Source')}\n{item.get('url','')}\n{(item.get('snippet','') or '')[:200]}"
                save_message(db, session, "assistant", line, "researcher")
                out.append({"role": "assistant", "agent": "researcher", "content": line})
    else:
        out, waiting, question, session_done, final_report = run_diagnostic_flow(
            session, payload.message, db
        )
        for msg in out:
            save_message(db, session, msg["role"], msg["content"], msg["agent"])
        if waiting and question:
            q_msg = {"role": "assistant", "agent": "system", "content": question}
            out.append(q_msg)
            save_message(db, session, q_msg["role"], q_msg["content"], q_msg["agent"])

    run_id: str | None = None
    try:
        rt = get_current_run_tree()
        if rt is not None:
            run_id = str(rt.id)
    except Exception:
        pass

    return {
        "assistant_messages": out,
        "waiting_for_hitl": waiting,
        "hitl_question": question,
        "session_done": session_done,
        "final_report": final_report,
        "langsmith_run_id": run_id,
    }


def _hitl_trace_process_inputs(inputs: dict[str, Any]) -> dict[str, Any]:
    s = inputs.get("session")
    p = inputs.get("payload")
    return {
        "session_id": str(s.id) if s else "",
        "answer_chars": len(p.answer) if p and hasattr(p, "answer") else 0,
    }


def _hitl_trace_process_outputs(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict):
        return {"output_type": type(result).__name__}
    return {
        "assistant_message_count": len(result.get("assistant_messages", [])),
        "waiting_for_hitl": result.get("waiting_for_hitl"),
        "session_done": result.get("session_done"),
        "hitl_question_preview": (result.get("hitl_question") or "")[:400],
    }


@traceable(
    name="chat_hitl",
    run_type="chain",
    tags=["myaidoctor", "api"],
    process_inputs=_hitl_trace_process_inputs,
    process_outputs=_hitl_trace_process_outputs,
)
def run_chat_hitl_traced(
    db: Session,
    session: ChatSession,
    payload: HitlRequest,
    graph: Any,
    config: dict,
) -> dict[str, Any]:
    out: list[dict] = []
    waiting = False
    question = ""
    done = False
    report = None

    try:
        for raw in graph.stream(Command(resume=payload.answer), config=config, stream_mode="updates"):
            event = raw
            if isinstance(raw, tuple):
                event = raw[-1] if len(raw) in (2, 3) else raw
            if not isinstance(event, dict):
                continue
            extra, q = extract_interrupt_from_stream_event(event)
            if q or extra:
                waiting = True
                for row in extra:
                    out.append(row)
                    save_message(db, session, row["role"], row["content"], row["agent"])
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
                    row = {"role": "assistant", "agent": agent, "content": content}
                    out.append(row)
                    save_message(db, session, row["role"], row["content"], row["agent"])
        snapshot = graph.get_state(config)
        values = getattr(snapshot, "values", {}) or {}
        report = values.get("final_report")
        done = bool(report)
    except GraphInterrupt as exc:
        waiting = True
        if exc.args and exc.args[0]:
            extra, q = interrupt_args_to_messages(tuple(exc.args[0]))
            for row in extra:
                out.append(row)
                save_message(db, session, row["role"], row["content"], row["agent"])
            if q:
                question = q
    except Exception as exc:
        if "interrupt" in str(exc).lower():
            waiting = True
            snapshot = graph.get_state(config)
            for task in getattr(snapshot, "tasks", []) or []:
                for interrupt_obj in getattr(task, "interrupts", []):
                    payload_data = getattr(interrupt_obj, "value", {})
                    if isinstance(payload_data, dict) and payload_data.get("question"):
                        question = str(payload_data["question"])
                        crit = str(payload_data.get("critique", "")).strip()
                        if crit:
                            row = {"role": "assistant", "agent": "skeptic", "content": f"[Skeptic] {crit}"}
                            out.append(row)
                            save_message(db, session, row["role"], row["content"], row["agent"])
                        break
        else:
            msg = {"role": "assistant", "agent": "system", "content": f"Error: {exc}"}
            out.append(msg)
            save_message(db, session, msg["role"], msg["content"], msg["agent"])

    if waiting and question:
        q_msg = {"role": "assistant", "agent": "system", "content": question}
        out.append(q_msg)
        save_message(db, session, q_msg["role"], q_msg["content"], q_msg["agent"])

    return {
        "assistant_messages": out,
        "waiting_for_hitl": waiting,
        "hitl_question": question,
        "session_done": done,
        "final_report": report,
    }


@router.post("/message", response_model=ChatResponse)
def send_message(
    payload: MessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    save_message(db, session, "user", payload.message, "user")
    refresh_session_title_if_placeholder(db, session)

    traced = run_chat_message_traced(db, session, payload, current_user)
    out = traced["assistant_messages"]
    waiting = traced["waiting_for_hitl"]
    question = traced["hitl_question"]
    session_done = traced["session_done"]
    final_report = traced["final_report"]

    session.waiting_for_hitl = waiting
    session.hitl_question = question
    session.final_report = final_report
    session.updated_at = datetime.utcnow()
    if traced.get("langsmith_run_id"):
        session.langsmith_run_id = traced["langsmith_run_id"]
    db.commit()

    return ChatResponse(
        messages=[MessageOut(**m) for m in out],
        waiting_for_hitl=waiting,
        hitl_question=question,
        session_done=session_done,
        final_report=final_report,
    )


@router.post("/hitl", response_model=ChatResponse)
def resume_hitl(
    payload: HitlRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == payload.session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.waiting_for_hitl:
        raise HTTPException(status_code=400, detail="Session not waiting for HITL answer")

    save_message(db, session, "user", payload.answer, "user")
    refresh_session_title_if_placeholder(db, session)
    graph = get_graph()
    config = {"configurable": {"thread_id": session.thread_id}}

    langsmith_extra: LangSmithExtra | None = None
    if session.langsmith_run_id:
        try:
            parent = RunTree(
                name="chat_message",
                run_type="chain",
                id=UUID(session.langsmith_run_id.strip()),
            )
            langsmith_extra = LangSmithExtra(parent=parent)
        except (ValueError, TypeError):
            pass

    traced = run_chat_hitl_traced(
        db, session, payload, graph, config, langsmith_extra=langsmith_extra
    )
    out = traced["assistant_messages"]
    waiting = traced["waiting_for_hitl"]
    question = traced["hitl_question"]
    done = traced["session_done"]
    report = traced["final_report"]

    session.waiting_for_hitl = waiting
    session.hitl_question = question
    session.final_report = report
    session.updated_at = datetime.utcnow()
    db.commit()
    return ChatResponse(
        messages=[MessageOut(**m) for m in out],
        waiting_for_hitl=waiting,
        hitl_question=question,
        session_done=done,
        final_report=report,
    )
