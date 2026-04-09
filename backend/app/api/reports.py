# ruff: noqa: B008
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.models import ChatSession, User
from backend.app.db.session import get_db

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{session_id}")
def get_report(session_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = (
        db.query(ChatSession)
        .filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": str(session.id), "final_report": session.final_report}
