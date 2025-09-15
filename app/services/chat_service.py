import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models.chat_session import ChatSession

def _new_uuid_str() -> str:
    return str(uuid.uuid4())

def create_chat_session(db: Session, user_id: int, project_id: Optional[str] = None, title: Optional[str] = None) -> ChatSession:
    session = ChatSession(
        id=_new_uuid_str(),
        user_id=user_id,
        project_id=project_id,
        title=title,
        last_message=None,
        unread_count=0,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session

def get_chat_session(db: Session, session_id: str) -> Optional[ChatSession]:
    if session_id is None:
        return None
    return db.query(ChatSession).get(session_id)

def update_session_metadata(
    db: Session,
    session_id: str,
    message_text: Optional[str] = None,
    is_assistant: bool = False,
    increment_unread: bool = True,
    set_title_if_empty: Optional[str] = None,
):
    """
    Update last_message, updated_at and unread_count for the session.
    - message_text: text to set as last_message (truncated).
    - is_assistant: True when the assistant produces the message (this increments unread_count).
    - increment_unread: whether to increment unread_count (defaults True for assistant replies).
    - set_title_if_empty: if provided and session.title is empty, set it (useful for first user message).
    """
    session = db.query(ChatSession).get(session_id)
    if not session:
        return None

    if message_text is not None:
        session.last_message = message_text[:3000]

    if set_title_if_empty and (not session.title or session.title.strip() == ""):
        session.title = set_title_if_empty[:250]

    session.updated_at = datetime.utcnow()

    if is_assistant and increment_unread:
        session.unread_count = (session.unread_count or 0) + 1

    if not is_assistant:
        session.unread_count = 0

    db.commit()
    db.refresh(session)
    return session
