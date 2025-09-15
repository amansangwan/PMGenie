from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.models.base import Base
from sqlalchemy.orm import relationship

class File(Base):
    __tablename__ = "files"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    s3_key = Column(String, nullable=False)
    uploaded_by = Column(Integer, nullable=True)
    project_id = Column(String, nullable=True)
    chat_session_id = Column(String, nullable=True)
    is_kb = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    kb_metadata = relationship("KBMetadata", uselist=False, back_populates="file", cascade="all, delete-orphan")

