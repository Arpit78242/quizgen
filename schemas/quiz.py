from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional, List
from schemas.question import QuestionOut, QuestionReviewOut, AnswerIn


class QuizGenerateRequest(BaseModel):
    source_id: Optional[UUID] = None
    topic: Optional[str] = None
    num_questions: int = 5
    time_limit_seconds: int = 300  # default 5 minutes
    difficulty: str = "medium"

    @field_validator("num_questions")
    @classmethod
    def validate_num_questions(cls, v):
        if not 1 <= v <= 10:
            raise ValueError("Number of questions must be between 1 and 10")
        return v

    @field_validator("time_limit_seconds")
    @classmethod
    def validate_time_limit(cls, v):
        if not 30 <= v <= 3600:
            raise ValueError("Time limit must be between 30 seconds and 1 hour")
        return v

    @field_validator("difficulty")
    @classmethod
    def validate_difficulty(cls, v):
        if v not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty must be easy, medium, or hard")
        return v


class QuizSessionOut(BaseModel):
    id: UUID
    title: Optional[str]
    num_questions: int
    difficulty: str
    time_limit_seconds: int
    time_taken_seconds: Optional[int]
    score: int
    total_questions: int
    percentage: Optional[float]
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    questions: List[QuestionOut] = []

    class Config:
        from_attributes = True


class QuizSubmitRequest(BaseModel):
    answers: List[AnswerIn]
    time_taken_seconds: int


class QuizReviewOut(BaseModel):
    id: UUID
    title: Optional[str]
    score: int
    total_questions: int
    percentage: Optional[float]
    difficulty: str
    time_limit_seconds: int
    time_taken_seconds: Optional[int]
    status: str
    completed_at: Optional[datetime]
    questions: List[QuestionReviewOut] = []

    class Config:
        from_attributes = True


class QuizHistoryItem(BaseModel):
    id: UUID
    title: Optional[str]
    num_questions: int
    difficulty: str
    score: int
    total_questions: int
    percentage: Optional[float]
    status: str
    time_limit_seconds: int
    time_taken_seconds: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True
