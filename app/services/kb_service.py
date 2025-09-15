from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any

from app.models.file import File
from app.models.kb_metadata import KBMetadata


# -----------------------
# CRUD for KB Metadata
# -----------------------
def add_metadata(
    db: Session,
    file_id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> KBMetadata:
    """
    Create or update metadata for a given KB file.
    Enforces 1-to-1 relationship between File and KBMetadata.
    """
    metadata = db.query(KBMetadata).filter(KBMetadata.file_id == file_id).first()
    if metadata:
        # Update existing
        if name is not None:
            metadata.name = name
        if description is not None:
            metadata.description = description
        if category is not None:
            metadata.category = category
        if tags is not None:
            metadata.tags = tags
    else:
        # Create new
        metadata = KBMetadata(
            file_id=file_id,
            name=name,
            description=description,
            category=category,
            tags=tags,
        )
        db.add(metadata)

    db.commit()
    db.refresh(metadata)
    return metadata


def get_metadata(db: Session, file_id: int) -> Optional[KBMetadata]:
    return db.query(KBMetadata).filter(KBMetadata.file_id == file_id).first()


def delete_metadata(db: Session, file_id: int) -> bool:
    metadata = db.query(KBMetadata).filter(KBMetadata.file_id == file_id).first()
    if metadata:
        db.delete(metadata)
        db.commit()
        return True
    return False


# -----------------------
# Project & File Queries
# -----------------------
def list_projects(db: Session) -> List[Dict[str, Any]]:
    """
    Return distinct KB projects with metadata (file count, last updated).
    """
    results = (
        db.query(
            File.project_id,
            func.count(File.id).label("file_count"),
            func.max(File.created_at).label("last_updated"),
        )
        .filter(File.is_kb == True)
        .group_by(File.project_id)
        .all()
    )

    return [
        {
            "projectId": row.project_id,
            "fileCount": row.file_count,
            "lastUpdated": row.last_updated,
        }
        for row in results
        if row.project_id is not None
    ]


def list_files(db: Session, project_id: Optional[str] = None) -> List[File]:
    """
    Return KB files (optionally filtered by project).
    """
    q = db.query(File).filter(File.is_kb == True)
    if project_id:
        q = q.filter(File.project_id == project_id)
    return q.order_by(File.created_at.desc()).all()


def filter_files(
    db: Session,
    project_id: Optional[str] = None,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    filename: Optional[str] = None,
) -> List[File]:
    """
    Generalized filtering across KB.
    Supports filtering by project, category, tag, filename.
    """
    q = db.query(File).filter(File.is_kb == True).join(KBMetadata, KBMetadata.file_id == File.id, isouter=True)

    if project_id:
        q = q.filter(File.project_id == project_id)
    if category:
        q = q.filter(KBMetadata.category == category)
    if tag:
        q = q.filter(KBMetadata.tags.contains([tag]))
    if filename:
        q = q.filter(File.filename.ilike(f"%{filename}%"))

    return q.order_by(File.created_at.desc()).all()
