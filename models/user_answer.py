import uuid
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.base import Base


class UserAnswer(Base):
    __tablename__ = "user_answers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(UUID(as_uuid=True), ForeignKey("quiz_questions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    selected_option = Column(String(1), nullable=True)  # NULL means skipped/timed out
    is_correct = Column(Boolean, nullable=True)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("selected_option IN ('A','B','C','D') OR selected_option IS NULL",
                        name="ck_selected_option"),
    )

    # Relationships
    session = relationship("QuizSession", back_populates="user_answers")
    question = relationship("QuizQuestion", back_populates="user_answers")
    user = relationship("User", back_populates="user_answers")
