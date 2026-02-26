from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os

from db.base import create_tables
from routers import auth, sources, quiz, profile
from core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    create_tables()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="QuizGen",
    description="AI-powered quiz generation platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Routers
app.include_router(auth.router)
app.include_router(sources.router)
app.include_router(quiz.router)
app.include_router(profile.router)


@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    from core.dependencies import get_current_user
    from db.base import SessionLocal
    db = SessionLocal()
    try:
        from core.security import decode_access_token
        from models.user import User
        from models.quiz_session import QuizSession

        token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse(url="/auth/login", status_code=302)

        payload = decode_access_token(token)
        if not payload:
            return RedirectResponse(url="/auth/login", status_code=302)

        user = db.query(User).filter(User.id == payload.get("sub")).first()
        if not user:
            return RedirectResponse(url="/auth/login", status_code=302)

        recent_sessions = (
            db.query(QuizSession)
            .filter(QuizSession.user_id == user.id)
            .order_by(QuizSession.created_at.desc())
            .limit(5)
            .all()
        )

        total_quizzes = db.query(QuizSession).filter(QuizSession.user_id == user.id).count()
        completed = db.query(QuizSession).filter(
            QuizSession.user_id == user.id,
            QuizSession.status.in_(["completed", "timed_out"])
        ).all()
        avg_score = (
            round(sum(s.percentage for s in completed if s.percentage) / len(completed), 1)
            if completed else 0
        )

        return templates.TemplateResponse("dashboard/index.html", {
            "request": request,
            "user": user,
            "recent_sessions": recent_sessions,
            "total_quizzes": total_quizzes,
            "avg_score": avg_score,
            "completed_count": len(completed),
        })
    finally:
        db.close()
