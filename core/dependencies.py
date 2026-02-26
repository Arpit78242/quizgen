from fastapi import Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from db.base import SessionLocal
from core.security import decode_access_token
from models.user import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    """Returns user or None — used for pages accessible to both auth and unauth users."""
    try:
        return get_current_user(request, db)
    except HTTPException:
        return None


def require_auth(request: Request, db: Session = Depends(get_db)) -> User:
    """Use in page routes — redirects to login instead of raising 401."""
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/auth/login", status_code=302)

    payload = decode_access_token(token)
    if not payload:
        return RedirectResponse(url="/auth/login", status_code=302)

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return RedirectResponse(url="/auth/login", status_code=302)

    return user
