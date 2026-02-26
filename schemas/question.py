from pydantic import BaseModel
from uuid import UUID
from typing import Optional


class QuestionOut(BaseModel):
    id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    order_index: int

    class Config:
        from_attributes = True


class QuestionReviewOut(BaseModel):
    id: UUID
    question_text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_option: str
    explanation: Optional[str]
    order_index: int
    selected_option: Optional[str]  # what the user chose
    is_correct: Optional[bool]

    class Config:
        from_attributes = True


class AnswerIn(BaseModel):
    question_id: UUID
    selected_option: Optional[str]  # A, B, C, D or None
