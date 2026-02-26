from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
import json

from core.dependencies import get_db, get_current_user
from models.user import User
from schemas.quiz import QuizGenerateRequest, QuizSubmitRequest
from schemas.question import AnswerIn
from services import quiz_service, source_service

router = APIRouter(prefix="/quiz", tags=["quiz"])
templates = Jinja2Templates(directory="templates")


@router.get("/generate", response_class=HTMLResponse)
def generate_page(
    request: Request,
    source_id: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sources = source_service.get_user_sources(db, user)
    selected_source = None
    if source_id:
        from models.study_source import StudySource
        selected_source = db.query(StudySource).filter(
            StudySource.id == source_id,
            StudySource.user_id == user.id
        ).first()

    return templates.TemplateResponse("quiz/generate.html", {
        "request": request,
        "user": user,
        "sources": sources,
        "selected_source": selected_source,
    })


@router.post("/generate")
async def generate_quiz(
    request: Request,
    source_id: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    num_questions: int = Form(5),
    time_limit_seconds: int = Form(300),
    difficulty: str = Form("medium"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        from uuid import UUID
        data = QuizGenerateRequest(
            source_id=UUID(source_id) if source_id else None,
            topic=topic if topic else None,
            num_questions=num_questions,
            time_limit_seconds=time_limit_seconds,
            difficulty=difficulty,
        )
        session = await quiz_service.generate_quiz(db, user, data)
        return RedirectResponse(url=f"/quiz/{session.id}/attempt", status_code=302)
    except HTTPException as e:
        sources = source_service.get_user_sources(db, user)
        return templates.TemplateResponse("quiz/generate.html", {
            "request": request,
            "user": user,
            "sources": sources,
            "error": e.detail,
        }, status_code=e.status_code)
    except Exception as e:
        sources = source_service.get_user_sources(db, user)
        return templates.TemplateResponse("quiz/generate.html", {
            "request": request,
            "user": user,
            "sources": sources,
            "error": f"Something went wrong: {str(e)}",
        }, status_code=500)


@router.get("/{session_id}/attempt", response_class=HTMLResponse)
def attempt_page(
    session_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = quiz_service.get_quiz_for_attempt(db, user, session_id)
    if session.status in ["completed", "timed_out"]:
        return RedirectResponse(url=f"/quiz/{session_id}/review", status_code=302)

    # Start quiz if pending
    if session.status == "pending":
        session = quiz_service.start_quiz(db, user, session_id)

    questions = [
        {
            "id": str(q.id),
            "question_text": q.question_text,
            "option_a": q.option_a,
            "option_b": q.option_b,
            "option_c": q.option_c,
            "option_d": q.option_d,
            "order_index": q.order_index,
        }
        for q in session.questions
    ]

    return templates.TemplateResponse("quiz/attempt.html", {
        "request": request,
        "user": user,
        "session": session,
        "questions": questions,
        "questions_json": json.dumps(questions),
        "time_limit": session.time_limit_seconds,
    })


@router.post("/{session_id}/submit")
async def submit_quiz(
    session_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        body = await request.json()
        answers_raw = body.get("answers", [])
        time_taken = body.get("time_taken_seconds", 0)

        answers = [
            AnswerIn(
                question_id=a["question_id"],
                selected_option=a.get("selected_option"),
            )
            for a in answers_raw
        ]

        data = QuizSubmitRequest(answers=answers, time_taken_seconds=time_taken)
        session = quiz_service.submit_quiz(db, user, session_id, data)
        return {"redirect": f"/quiz/{session_id}/review"}
    except HTTPException as e:
        return {"error": e.detail}


@router.get("/{session_id}/review", response_class=HTMLResponse)
def review_page(
    session_id: str,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session, review_questions = quiz_service.get_quiz_review(db, user, session_id)
    return templates.TemplateResponse("quiz/review.html", {
        "request": request,
        "user": user,
        "session": session,
        "questions": review_questions,
    })
