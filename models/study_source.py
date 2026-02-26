import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base


class StudySource(Base):
    __tablename__ = "study_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_type = Column(String(50), nullable=False)  # pdf, docx, topic, image
    file_name = Column(String(255), nullable=True)
    file_path = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    topic = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="study_sources")
    quiz_sessions = relationship("QuizSession", back_populates="source")
