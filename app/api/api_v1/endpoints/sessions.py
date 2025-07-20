from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Dict, List
from datetime import datetime, timezone
import itertools

router = APIRouter()

# In-memory stores
session_store: Dict[int, Dict[str, str]] = {}
chat_store: Dict[int, List[Dict[str, str]]] = {}
session_id_counter = itertools.count(1)

class SessionCreate(BaseModel):
    session_user: str

class SessionOut(BaseModel):
    session_id: int
    session_user: str
    created_at: str

class MessageCreate(BaseModel):
    role: str
    content: str

    @field_validator("role")
    def validate_role(cls, v):
        if v not in {"user", "assistant"}:
            raise ValueError("Role must be 'user' or 'assistant'")
        return v

class MessageOut(BaseModel):
    role: str
    content: str
    timestamp: str

@router.post("/sessions", response_model=SessionOut)
def create_session(session: SessionCreate):
    """
    Create a new chat session.
    """
    username = session.session_user.strip().lower()
    if not username:
        raise HTTPException(status_code=400, detail="Username cannot be empty")
    session_id = next(session_id_counter)
    created_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    session_store[session_id] = {
        "session_user": username,
        "created_at": created_at
    }
    chat_store[session_id] = []
    return SessionOut(
        session_id=session_id,
        session_user=username,
        created_at=created_at
    )

@router.post("/sessions/{session_id}/messages", response_model=MessageOut)
def add_message(session_id: int, message: MessageCreate):
    """
    Add a message to a session.
    """
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    msg = {
        "role": message.role,
        "content": message.content,
        "timestamp": timestamp
    }
    chat_store[session_id].append(msg)
    return MessageOut(**msg)

@router.get("/sessions/{session_id}/messages", response_model=List[MessageOut])
def get_messages(session_id: int, role: Optional[str] = None):
    """
    Get messages for a session, optionally filtered by role.
    """
    if session_id not in session_store:
        raise HTTPException(status_code=404, detail="Session not found")
    messages = chat_store[session_id]
    if role:
        if role not in {"user", "assistant"}:
            raise HTTPException(status_code=400, detail="Role must be 'user' or 'assistant'")
        messages = [msg for msg in messages if msg.get("role") == role]
    return [MessageOut(**msg) for msg in messages]
