from datetime import datetime, timezone
from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

from models.quiz_session import QuizSession
from models.quiz_question import QuizQuestion
from models.user_answer import UserAnswer
from models.study_source import StudySource
from models.user import User
from schemas.quiz import QuizGenerateRequest, QuizSubmitRequest
from services import ai_service


async def generate_quiz(db: Session, user: User, data: QuizGenerateRequest) -> QuizSession:
    if not data.source_id and not data.topic:
        raise HTTPException(status_code=400, detail="Provide either a source_id or a topic")

    source = None
    raw_text = None
    topic_label = None

    if data.source_id:
        source = db.query(StudySource).filter(
            StudySource.id == data.source_id,
            StudySource.user_id == user.id
        ).first()
        if not source:
            raise HTTPException(status_code=404, detail="Study source not found")

        if source.source_type == "topic":
            topic_label = source.topic
        else:
            raw_text = source.raw_text
            topic_label = source.file_name

    elif data.topic:
        topic_label = data.topic

    # Generate questions via AI
    try:
        if raw_text:
            questions_data = await ai_service.generate_questions_from_text(
                raw_text, data.num_questions, data.difficulty
            )
        else:
            questions_data = await ai_service.generate_questions_from_topic(
                topic_label, data.num_questions, data.difficulty
            )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {str(e)}")

    if not questions_data:
        raise HTTPException(status_code=502, detail="AI returned no valid questions. Please try again.")

    # Create session
    title = f"{topic_label} — {data.difficulty.capitalize()} Quiz"
    session = QuizSession(
        user_id=user.id,
        source_id=source.id if source else None,
        title=title[:255],
        num_questions=len(questions_data),
        difficulty=data.difficulty,
        time_limit_seconds=data.time_limit_seconds,
        total_questions=len(questions_data),
        status="pending",
    )
    db.add(session)
    db.flush()  # Get session.id before inserting questions

    # Insert questions
    for i, q in enumerate(questions_data):
        question = QuizQuestion(
            session_id=session.id,
            question_text=q["question"],
            option_a=q["option_a"],
            option_b=q["option_b"],
            option_c=q["option_c"],
            option_d=q["option_d"],
            correct_option=q["correct_option"],
            explanation=q.get("explanation", ""),
            order_index=i + 1,
        )
        db.add(question)

    db.commit()
    db.refresh(session)
    return session


def start_quiz(db: Session, user: User, session_id: str) -> QuizSession:
    session = _get_session(db, user, session_id)
    if session.status not in ["pending"]:
        raise HTTPException(status_code=400, detail="Quiz already started or completed")

    session.status = "in_progress"
    session.started_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


def submit_quiz(db: Session, user: User, session_id: str, data: QuizSubmitRequest) -> QuizSession:
    session = _get_session(db, user, session_id)
    if session.status == "completed" or session.status == "timed_out":
        raise HTTPException(status_code=400, detail="Quiz already submitted")

    questions = {str(q.id): q for q in session.questions}
    score = 0
    answers_map = {str(a.question_id): a for a in data.answers}

    for question_id, question in questions.items():
        answer_data = answers_map.get(question_id)
        selected = answer_data.selected_option.upper() if answer_data and answer_data.selected_option else None
        is_correct = selected == question.correct_option if selected else False

        if is_correct:
            score += 1

        user_answer = UserAnswer(
            session_id=session.id,
            question_id=question.id,
            user_id=user.id,
            selected_option=selected,
            is_correct=is_correct,
        )
        db.add(user_answer)

    percentage = round((score / session.total_questions) * 100, 2) if session.total_questions > 0 else 0

    # Determine if timed out
    timed_out = data.time_taken_seconds >= session.time_limit_seconds

    session.score = score
    session.percentage = percentage
    session.time_taken_seconds = data.time_taken_seconds
    session.status = "timed_out" if timed_out else "completed"
    session.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(session)
    return session


def get_quiz_for_attempt(db: Session, user: User, session_id: str) -> QuizSession:
    session = _get_session(db, user, session_id)
    return session


def get_quiz_review(db: Session, user: User, session_id: str):
    session = _get_session(db, user, session_id)
    if session.status not in ["completed", "timed_out"]:
        raise HTTPException(status_code=400, detail="Quiz not yet completed")

    # Build review with answers attached
    answers_map = {str(a.question_id): a for a in session.user_answers}
    review_questions = []
    for q in session.questions:
        answer = answers_map.get(str(q.id))
        review_questions.append({
            "id": q.id,
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "correct_option": q.correct_option,
            "explanation": q.explanation,
            "order_index": q.order_index,
            "selected_option": answer.selected_option if answer else None,
            "is_correct": answer.is_correct if answer else False,
        })

    return session, review_questions


def get_user_history(db: Session, user: User, page: int = 1, per_page: int = 10):
    offset = (page - 1) * per_page
    total = db.query(QuizSession).filter(QuizSession.user_id == user.id).count()
    sessions = (
        db.query(QuizSession)
        .filter(QuizSession.user_id == user.id)
        .order_by(QuizSession.created_at.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )
    return sessions, total


def _get_session(db: Session, user: User, session_id: str) -> QuizSession:
    session = db.query(QuizSession).filter(
        QuizSession.id == session_id,
        QuizSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Quiz session not found")
    return session
