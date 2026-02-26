from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from core.dependencies import get_db
from schemas.user import UserCreate
from services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        token = auth_service.login_user(db, email, password)
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            max_age=7 * 24 * 60 * 60,  # 7 days
            samesite="lax",
        )
        return response
    except HTTPException as e:
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": e.detail},
            status_code=400,
        )


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    token = request.cookies.get("access_token")
    if token:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
def register(
    request: Request,
    email: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        auth_service.register_user(db, UserCreate(email=email, username=username, password=password))
        return RedirectResponse(url="/auth/login?registered=true", status_code=302)
    except HTTPException as e:
        return templates.TemplateResponse(
            "auth/register.html",
            {"request": request, "error": e.detail},
            status_code=400,
        )


@router.get("/logout")
def logout():
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response
