from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.routes.deps import get_current_user_id
from app.models.chat_session import ChatSession

router = APIRouter(tags=["chats"])


@router.get("/chats/sessions")
def list_chat_sessions(
    projectId: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    q = db.query(ChatSession).filter(ChatSession.user_id == user_id)

    if projectId:
        q = q.filter(ChatSession.project_id == projectId)

    sessions = q.all()

    return [
        {
            "id": s.id,
            "projectId": s.project_id,
            "title": s.title or "Untitled Chat",
            "last_message": s.last_message,
            "unread_count": s.unread_count,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in sessions
    ]
