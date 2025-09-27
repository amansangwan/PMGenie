from dotenv import load_dotenv
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Query, Form
from sqlalchemy.orm import Session
from typing import Optional, List
import uuid, os
from openai import OpenAI

from app.routes.deps import get_current_user_id
from app.db.session import get_db
from app.models.file import File as FileModel
from app.services.s3_service import upload_fileobj
from app.services.file_service import save_file_and_process_from_s3
from app.services import kb_service
from app.schemas.kb import (
    KBProjectResponse,
    KBFileResponse,
    KBMetadataResponse,
    KBAddContentRequest,
)

router = APIRouter(tags=["knowledge-base"])
load_dotenv("creds.env")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# -----------------------
# Legacy: List KB Files (all)
# -----------------------
@router.get("/files")
def list_files(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    files = db.query(FileModel).filter(FileModel.is_kb == True).order_by(FileModel.created_at.desc()).all()  # noqa: E712
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "s3_key": f.s3_key,
            "projectId": f.project_id,
            "chatSessionId": f.chat_session_id,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in files
    ]


# -----------------------
# Legacy: Upload KB File
# -----------------------
@router.post("/upload")
async def kb_upload(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    projectId: Optional[str] = Form(None),
    chatSessionId: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    # Create S3 key
    key = f"kb/{uuid.uuid4()}-{file.filename}"

    # ✅ Stream upload to S3 (no full read into memory)
    upload_fileobj(key, file.file, content_type=file.content_type or "application/octet-stream")

    # Save DB record
    rec = FileModel(
        filename=file.filename,
        s3_key=key,
        uploaded_by=user_id,
        project_id=projectId,
        chat_session_id=chatSessionId,
        is_kb=True,
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    # Background task (S3 key only, not bytes)
    background.add_task(
        save_file_and_process_from_s3,
        rec.s3_key,
        rec.filename,
        projectId,
        chatSessionId,
        rec.id,
        True,
    )

    return {
        "id": rec.id,
        "filename": rec.filename,
        "s3_key": rec.s3_key,
        "projectId": rec.project_id,
        "chatSessionId": rec.chat_session_id,
        "created_at": rec.created_at.isoformat() if rec.created_at else None,
    }


# # -----------------------
# # New: List KB Projects
# # -----------------------
# @router.get("/projects", response_model=List[KBProjectResponse])
# def list_projects(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
#     return kb_service.list_projects(db)


# -----------------------
# New: List Uploaded KB Files (filter by projectId)
# -----------------------
@router.get("/upload", response_model=List[KBFileResponse])
def list_files_new(
    projectId: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    return kb_service.list_files(db, project_id=projectId)


# -----------------------
# New: Filter KB Files
# -----------------------
# @router.get("/filter", response_model=List[KBFileResponse])
# def filter_files(
#     projectId: Optional[str] = Query(None),
#     category: Optional[str] = Query(None),
#     tag: Optional[str] = Query(None),
#     filename: Optional[str] = Query(None),
#     db: Session = Depends(get_db),
#     user_id: int = Depends(get_current_user_id),
# ):
#     return kb_service.filter_files(
#         db=db,
#         project_id=projectId,
#         category=category,
#         tag=tag,
#         filename=filename,
#     )


# -----------------------
# New: Add KB Metadata
# -----------------------
@router.post("/add-content", response_model=KBMetadataResponse)
def add_content(
    req: KBAddContentRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    file = (
        db.query(FileModel)
        .filter(
            FileModel.id == req.file_id,
            FileModel.is_kb == True,  # must be KB file
            FileModel.uploaded_by == user_id,  # must belong to current user
        )
        .first()
    )
    if not file:
        raise HTTPException(
            status_code=404,
            detail="KB file not found or you do not have permission to modify it",
        )

    return kb_service.add_metadata(
        db=db,
        file_id=req.file_id,
        name=req.name,
        description=req.description,
        category=req.category,
        tags=req.tags,
    )


# -----------------------
# New: Get KB Metadata
# -----------------------
@router.get("/content/{file_id}", response_model=KBMetadataResponse)
def get_content(file_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    metadata = kb_service.get_metadata(db, file_id=file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found for this file")
    return metadata


# -----------------------
# New: Delete KB Metadata
# -----------------------
@router.delete("/content/{file_id}")
def delete_content(file_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    deleted = kb_service.delete_metadata(db, file_id=file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Metadata not found for this file")
    return {"status": "success", "message": f"Metadata deleted for file_id {file_id}"}
