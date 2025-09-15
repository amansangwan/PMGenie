from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatSessionResponse(BaseModel):
    chatSessionId: str
    userId: int
    projectId: Optional[str] = None
    title: Optional[str] = None
    lastMessage: Optional[str] = None
    unreadCount: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
