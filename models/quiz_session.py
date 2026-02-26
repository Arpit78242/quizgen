import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("study_sources.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=True)
    num_questions = Column(Integer, nullable=False)
    difficulty = Column(String(20), default="medium")
    time_limit_seconds = Column(Integer, nullable=False)
    time_taken_seconds = Column(Integer, nullable=True)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, nullable=False)
    percentage = Column(Numeric(5, 2), nullable=True)
    status = Column(String(20), default="pending")  # pending, in_progress, completed, timed_out
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="quiz_sessions")
    source = relationship("StudySource", back_populates="quiz_sessions")
    questions = relationship("QuizQuestion", back_populates="session", cascade="all, delete-orphan",
                             order_by="QuizQuestion.order_index")
    user_answers = relationship("UserAnswer", back_populates="session", cascade="all, delete-orphan")
