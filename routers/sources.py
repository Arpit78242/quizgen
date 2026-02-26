from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.dependencies import get_db, get_current_user
from models.user import User
from services import source_service

router = APIRouter(prefix="/sources", tags=["sources"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def sources_page(request: Request, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sources = source_service.get_user_sources(db, user)
    return templates.TemplateResponse("sources/upload.html", {
        "request": request,
        "user": user,
        "sources": sources,
    })


@router.post("/upload")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        source = await source_service.save_file_source(db, user, file)
        return RedirectResponse(url=f"/quiz/generate?source_id={source.id}", status_code=302)
    except HTTPException as e:
        sources = source_service.get_user_sources(db, user)
        return templates.TemplateResponse("sources/upload.html", {
            "request": request,
            "user": user,
            "sources": sources,
            "error": e.detail,
        }, status_code=e.status_code)


@router.post("/topic")
def create_topic(
    request: Request,
    topic: str = Form(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        source = source_service.save_topic_source(db, user, topic)
        return RedirectResponse(url=f"/quiz/generate?source_id={source.id}", status_code=302)
    except HTTPException as e:
        sources = source_service.get_user_sources(db, user)
        return templates.TemplateResponse("sources/upload.html", {
            "request": request,
            "user": user,
            "sources": sources,
            "error": e.detail,
        }, status_code=e.status_code)


@router.post("/delete/{source_id}")
def delete_source(
    source_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    source_service.delete_source(db, user, source_id)
    return RedirectResponse(url="/sources/", status_code=302)
