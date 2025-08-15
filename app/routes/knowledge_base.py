from dotenv import load_dotenv
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
import uuid, time, os
from openai import OpenAI

from app.routes.deps import get_current_user_id
from app.db.session import get_db
from app.models.file import File as FileModel
from app.services.s3_service import upload_bytes
from app.services.file_service import save_file_and_process

router = APIRouter()
load_dotenv("creds.env")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.get("/files")
def list_files(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    files = db.query(FileModel).filter(FileModel.is_kb == True).order_by(FileModel.created_at.desc()).all()  # noqa: E712
    return [
        {"id": f.id, "filename": f.filename, "s3_key": f.s3_key, "projectId": f.project_id, "chatSessionId": f.chat_session_id, "created_at": f.created_at.isoformat() if f.created_at else None}
        for f in files
    ]

@router.post("/upload")
async def kb_upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    projectId: Optional[str] = None,
    chatSessionId: Optional[str] = None,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    data = await file.read()
    key = f"kb/{uuid.uuid4()}-{file.filename}"
    upload_bytes(key, data, file.content_type or "application/octet-stream")

    rec = FileModel(
        filename=file.filename,
        s3_key=key,
        uploaded_by=user_id,
        project_id=projectId,
        chat_session_id=chatSessionId,
        is_kb=True
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
        True
    )

    return {"file_id": rec.id}