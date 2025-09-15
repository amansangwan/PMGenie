from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List

from app.db.session import get_db
from app.routes.deps import get_current_user_id
from app.services import kb_service
from app.schemas.kb import (
    KBProjectResponse,
    KBFileResponse,
    KBMetadataResponse,
    KBAddContentRequest,
)
from app.models.file import File

router = APIRouter(tags=["knowledge-base"])


# -----------------------
# List KB Projects
# -----------------------
@router.get("/projects", response_model=List[KBProjectResponse])
def list_projects(db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    return kb_service.list_projects(db)


# -----------------------
# List Uploaded KB Files
# -----------------------
@router.get("/upload", response_model=List[KBFileResponse])
def list_files(
    projectId: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    files = kb_service.list_files(db, project_id=projectId)
    return files


# -----------------------
# Filter KB Files
# -----------------------
@router.get("/filter", response_model=List[KBFileResponse])
def filter_files(
    projectId: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    filename: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    files = kb_service.filter_files(
        db=db,
        project_id=projectId,
        category=category,
        tag=tag,
        filename=filename,
    )
    return files


# -----------------------
# Add KB Metadata
# -----------------------
@router.post("/add-content", response_model=KBMetadataResponse)
def add_content(
    req: KBAddContentRequest,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id),
):
    file = db.query(File).filter(File.id == req.file_id, File.is_kb == True).first()
    if not file:
        raise HTTPException(status_code=404, detail="KB file not found")

    metadata = kb_service.add_metadata(
        db=db,
        file_id=req.file_id,
        name=req.name,
        description=req.description,
        category=req.category,
        tags=req.tags,
    )
    return metadata


# -----------------------
# Get KB Metadata for a File
# -----------------------
@router.get("/content/{file_id}", response_model=KBMetadataResponse)
def get_content(file_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    metadata = kb_service.get_metadata(db, file_id=file_id)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found for this file")
    return metadata


# -----------------------
# Delete KB Metadata for a File
# -----------------------
@router.delete("/content/{file_id}")
def delete_content(file_id: int, db: Session = Depends(get_db), user_id: int = Depends(get_current_user_id)):
    deleted = kb_service.delete_metadata(db, file_id=file_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Metadata not found for this file")
    return {"status": "success", "message": f"Metadata deleted for file_id {file_id}"}
