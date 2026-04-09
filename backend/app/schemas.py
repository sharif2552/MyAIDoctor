from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionCreateRequest(BaseModel):
    title: str = "New Session"


class SessionResponse(BaseModel):
    id: UUID
    title: str
    thread_id: str
    waiting_for_hitl: bool
    hitl_question: str
    created_at: datetime


class MessageRequest(BaseModel):
    session_id: UUID
    message: str


class HitlRequest(BaseModel):
    session_id: UUID
    answer: str


class MessageOut(BaseModel):
    role: str
    agent: str
    content: str


class ChatResponse(BaseModel):
    messages: list[MessageOut]
    waiting_for_hitl: bool
    hitl_question: str
    session_done: bool
    final_report: dict | None = None
