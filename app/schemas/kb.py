from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KBProjectResponse(BaseModel):
    projectId: str
    fileCount: int
    lastUpdated: datetime


class KBFileResponse(BaseModel):
    id: int
    filename: str
    project_id: Optional[str]
    created_at: datetime

    class Config:
        orm_mode = True


class KBMetadataResponse(BaseModel):
    id: int
    file_id: int
    name: Optional[str]
    description: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    created_at: datetime

    class Config:
        orm_mode = True


class KBAddContentRequest(BaseModel):
    file_id: int
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
