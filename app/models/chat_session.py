from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.base import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(String(64), nullable=True, index=True)
    title = Column(String(512), nullable=True)
    last_message = Column(Text, nullable=True)
    unread_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", backref="chat_sessions")
