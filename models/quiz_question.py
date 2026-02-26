import uuid
from sqlalchemy import Column, String, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from db.base import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(1), nullable=False)
    explanation = Column(Text, nullable=True)
    order_index = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("correct_option IN ('A','B','C','D')", name="ck_correct_option"),
    )

    # Relationships
    session = relationship("QuizSession", back_populates="questions")
    user_answers = relationship("UserAnswer", back_populates="question", cascade="all, delete-orphan")
