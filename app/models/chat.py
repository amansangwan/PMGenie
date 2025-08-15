from sqlalchemy import Column, Integer, String, DateTime, func
from app.models.base import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    project_id = Column(String, nullable=True)
    chat_session_id = Column(String, nullable=True)
    role = Column(String, nullable=False)  # "user" | "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
