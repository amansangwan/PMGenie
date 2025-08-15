from dotenv import load_dotenv
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session

from app.routes.deps import get_current_user_id
from app.db.session import get_db
from app.models.chat import ChatMessage
from app.models.file import File as FileModel
from app.services.s3_service import upload_bytes
from app.services.qdrant_service import upsert_points, search
from app.services.ai_service import run_ai_message
from app.services.file_service import save_file_and_process

from openai import OpenAI
import os, uuid, time

load_dotenv("creds.env")
router = APIRouter()
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class MessageRequest(BaseModel):
    query: str
    projectId: Optional[str] = None
    chatSessionId: Optional[str] = None
    attachment_ids: Optional[List[int]] = None

@router.post("/messages")
async def send_message(req: MessageRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    # Persist user message
    print("ouside run_ai_message")


    # Optionally gather context docs from attachment_ids
    context_docs: List[str] = []
    if req.attachment_ids:
        files = db.query(FileModel).filter(FileModel.id.in_(req.attachment_ids)).all()
        for f in files:
            context_docs.append(f"[FILE:{f.filename}] available in KB/context")

    # Call AI agent (existing logic if available)

    print("ouside run_ai_message")
    answer = await run_ai_message(req.query, context_docs)

    # Persist assistant message


    return {"message": answer}

@router.get("/messages/history")
def get_history(projectId: Optional[str] = None, chatSessionId: Optional[str] = None, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    q = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)
    if projectId:
        q = q.filter(ChatMessage.project_id == projectId)
    if chatSessionId:
        q = q.filter(ChatMessage.chat_session_id == chatSessionId)
    msgs = q.order_by(ChatMessage.created_at.asc()).all()
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "projectId": m.project_id,
            "chatSessionId": m.chat_session_id,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]

class SearchResponse(BaseModel):
    id: str
    score: float
    payload: dict

@router.get("/messages/search")
def search_messages(q: str, projectId: Optional[str] = None, chatSessionId: Optional[str] = None):
    # embed query
    qemb = openai_client.embeddings.create(model="text-embedding-3-small", input=q).data[0].embedding
    filters = {}
    if projectId:
        filters["projectId"] = projectId
    if chatSessionId:
        filters["chatSessionId"] = chatSessionId
    results = search(qemb, limit=10, filters=filters)
    out = []
    for r in results:
        out.append({"id": r.id, "score": r.score, "payload": r.payload})
    return out

@router.post("/context/upload")
async def upload_context_file(
    background: BackgroundTasks,
    projectId: Optional[str] = None,
    chatSessionId: Optional[str] = None,
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    data = await file.read()
    key = f"uploads/{uuid.uuid4()}-{file.filename}"
    upload_bytes(key, data, file.content_type or "application/octet-stream")

    # persist metadata
    rec = FileModel(
        filename=file.filename,
        s3_key=key,
        uploaded_by=user_id,
        project_id=projectId,
        chat_session_id=chatSessionId,
        is_kb=False
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    background.add_task(
        save_file_and_process,
        data,
        file.filename,
        projectId,
        chatSessionId,
        rec.id,
        False
    )

    return {"file_id": rec.id, "filename": rec.filename, "s3_key": rec.s3_key}