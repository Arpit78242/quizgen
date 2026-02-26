from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from models.user import User
from services import quiz_service

router = APIRouter(prefix="/profile", tags=["profile"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def profile_page(
    request: Request,
    page: int = 1,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sessions, total = quiz_service.get_user_history(db, user, page=page, per_page=10)
    total_pages = (total + 9) // 10

    # Compute stats
    completed = [s for s in sessions if s.status in ["completed", "timed_out"]]
    avg_score = (
        round(sum(s.percentage for s in completed if s.percentage) / len(completed), 1)
        if completed else 0
    )

    return templates.TemplateResponse("profile/history.html", {
        "request": request,
        "user": user,
        "sessions": sessions,
        "total": total,
        "page": page,
        "total_pages": total_pages,
        "avg_score": avg_score,
    })
