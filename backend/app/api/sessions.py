# ruff: noqa: B008
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.models import ChatSession, User
from backend.app.db.session import get_db
from backend.app.schemas import SessionCreateRequest, SessionResponse
from backend.app.services.orchestrator import list_messages, refresh_session_title_if_placeholder

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
def create_session(
    payload: SessionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = ChatSession(user_id=current_user.id, title=payload.title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return SessionResponse(
        id=session.id,
        title=session.title,
        thread_id=session.thread_id,
        waiting_for_hitl=session.waiting_for_hitl,
        hitl_question=session.hitl_question,
        created_at=session.created_at,
    )


@router.get("", response_model=list[SessionResponse])
def list_sessions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )
    mutated = False
    for s in sessions:
        if refresh_session_title_if_placeholder(db, s):
            mutated = True
    if mutated:
        db.commit()
    return [
        SessionResponse(
            id=s.id,
            title=s.title,
            thread_id=s.thread_id,
            waiting_for_hitl=s.waiting_for_hitl,
            hitl_question=s.hitl_question,
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if refresh_session_title_if_placeholder(db, session):
        db.commit()
    return SessionResponse(
        id=session.id,
        title=session.title,
        thread_id=session.thread_id,
        waiting_for_hitl=session.waiting_for_hitl,
        hitl_question=session.hitl_question,
        created_at=session.created_at,
    )


@router.get("/{session_id}/messages")
def get_session_messages(
    session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": list_messages(db, session.id)}
