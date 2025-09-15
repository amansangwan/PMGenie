from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class ProjectCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None


class EpicCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None


class StoryCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None


class SubtaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None


# -----------------------
# NEW response schemas
# -----------------------

class ProjectSummaryResponse(BaseModel):
    id: str
    key: str
    name: str


class ProjectDetailResponse(BaseModel):
    id: str
    key: str
    name: str
    description: Optional[str]
    projectTypeKey: Optional[str]
    counts: Dict[str, int]
    status_counts: Dict[str, int]
    progress: float
    members: List[Dict[str, Optional[str]]]
    messages_count: int
    last_activity: Optional[datetime]
    due_date: Optional[datetime]
