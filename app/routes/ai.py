from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status, Form
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.routes.deps import get_current_user_id
from app.db.session import get_db
from app.models.chat import ChatMessage
from app.models.file import File as FileModel
from app.services.s3_service import upload_fileobj
from app.services.file_service import save_file_and_process_from_s3
from app.services.ai_service import run_ai_message
from app.services.chat_service import create_chat_session, update_session_metadata, get_chat_session

router = APIRouter(tags=["ai"])

# --------------- Pydantic requests ---------------
class MessageRequest(BaseModel):
    query: str
    projectId: Optional[str] = None
    chatSessionId: Optional[str] = None
    attachment_ids: Optional[List[int]] = None

class NewChatRequest(BaseModel):
    projectId: Optional[str] = None
    title: Optional[str] = None

# --------------- helpers ---------------
def _session_to_dict(s):
    return {
        "chatSessionId": s.id,
        "userId": s.user_id,
        "projectId": s.project_id,
        "title": s.title,
        "lastMessage": s.last_message,
        "unreadCount": s.unread_count,
        "created_at": s.created_at,
        "updated_at": s.updated_at,
    }

def _message_to_dict(m: ChatMessage):
    return {
        "id": m.id,
        "userId": m.user_id,
        "projectId": m.project_id,
        "chatSessionId": m.chat_session_id,
        "role": m.role,
        "content": m.content,
        "created_at": m.created_at,
    }

# --------------- new chat endpoints ---------------
@router.post("/new-chat", status_code=status.HTTP_201_CREATED)
def new_chat_post(req: NewChatRequest, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    session = create_chat_session(db=db, user_id=user_id, project_id=req.projectId, title=req.title)
    return _session_to_dict(session)

@router.get("/new-chat")
def new_chat_get(projectId: Optional[str] = None, title: Optional[str] = None, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    session = create_chat_session(db=db, user_id=user_id, project_id=projectId, title=title)
    return _session_to_dict(session)

# --------------- send message (user -> assistant) ---------------
@router.post("/messages")
async def send_message(req: MessageRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    """
    1) Create session if not provided
    2) Save user message in chat_messages
    3) Update session metadata (title if empty, last_message, reset unread_count)
    4) Run AI to generate assistant response
    5) Save assistant response
    6) Update session metadata (last_message, increment unread_count)
    7) Return assistant answer and chatSessionId
    """
    # 1) ensure chat session exists
    chat_session_id = req.chatSessionId
    if not chat_session_id:
        s = create_chat_session(db=db, user_id=user_id, project_id=req.projectId, title=None)
        chat_session_id = s.id

    # 2) persist user message
    user_message = ChatMessage(
        user_id=user_id,
        project_id=req.projectId,
        chat_session_id=chat_session_id,
        role="user",
        content=req.query,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # 3) update session metadata (set title if empty)
    title_candidate = (req.query or "")[:80]
    update_session_metadata(db=db, session_id=chat_session_id, message_text=req.query, is_assistant=False, set_title_if_empty=title_candidate)

    # 4) gather context documents if provided
    context_docs: List[str] = []
    if req.attachment_ids:
        files = db.query(FileModel).filter(FileModel.id.in_(req.attachment_ids)).all()
        for f in files:
            # minimal reference; your agent can fetch file content via File.s3_key if needed
            context_docs.append(f"[FILE:{f.filename}]")

    # 5) run AI agent (expects string answer); adapt if your ai_service returns structured response
    answer = await run_ai_message(req.query, context_docs)

    # 6) persist assistant message
    assistant_message = ChatMessage(
        user_id=user_id,
        project_id=req.projectId,
        chat_session_id=chat_session_id,
        role="assistant",
        content=answer,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # 7) update session metadata for assistant reply (increment unread)
    update_session_metadata(db=db, session_id=chat_session_id, message_text=answer, is_assistant=True, increment_unread=True)

    return {"chatSessionId": chat_session_id, "answer": answer}

# --------------- message history ---------------
@router.get("/messages/history")
def messages_history(projectId: Optional[str] = None, chatSessionId: Optional[str] = None, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    q = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)
    if projectId:
        q = q.filter(ChatMessage.project_id == projectId)
    if chatSessionId:
        q = q.filter(ChatMessage.chat_session_id == chatSessionId)
    msgs = q.order_by(ChatMessage.created_at.asc()).all()
    return [_message_to_dict(m) for m in msgs]

# --------------- file upload (preserve existing behavior) ---------------
@router.post("/context/upload")
async def upload_context_file(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    projectId: Optional[str] = Form(None),
    chatSessionId: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # Generate S3 key
    key = f"uploads/{uuid.uuid4()}-{file.filename}"

    # ✅ Stream upload to S3
    upload_fileobj(key, file.file, content_type=file.content_type or "application/octet-stream")

    # Save DB record
    rec = FileModel(
        filename=file.filename,
        s3_key=key,
        uploaded_by=user_id,
        project_id=projectId,
        chat_session_id=chatSessionId,
        is_kb=False,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Schedule background processing (by S3 key only, not bytes)
    background.add_task(
        save_file_and_process_from_s3,
        rec.s3_key,
        rec.filename,
        projectId,
        chatSessionId,
        rec.id,
        False,
    )

    return {"file_id": rec.id, "filename": rec.filename, "s3_key": rec.s3_key}