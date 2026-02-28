from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import ensure_dev_user, get_current_user
from app.core.oauth_google import build_google_auth_url, exchange_code_for_tokens, fetch_google_userinfo
from app.core.security import create_access_token, set_auth_cookie
from app.core.settings import get_settings
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "google_sub": user.google_sub,
        "email": user.email,
        "name": user.name,
        "avatar_url": user.avatar_url,
    }


@router.get("/google/login")
async def google_login(db: Session = Depends(get_db)):
    settings = get_settings()
    if settings.dev_auth_bypass:
        user = ensure_dev_user(db)
        token = create_access_token(str(user.id), user.email)
        response = RedirectResponse(url=f"{settings.config.app.frontend_url}/documents")
        set_auth_cookie(response, token)
        return response

    google_cfg = settings.config.auth.google
    if not google_cfg.client_id or not google_cfg.client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth is not configured")

    state = str(uuid.uuid4())
    redirect = RedirectResponse(url=build_google_auth_url(state))
    redirect.set_cookie("google_oauth_state", state, httponly=True, max_age=600, samesite="lax")
    return redirect


@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()

    if settings.dev_auth_bypass:
        user = ensure_dev_user(db)
        token = create_access_token(str(user.id), user.email)
        response = RedirectResponse(url=f"{settings.config.app.frontend_url}/documents")
        set_auth_cookie(response, token)
        return response

    if not code:
        raise HTTPException(status_code=400, detail="Missing OAuth code")

    stored_state = request.cookies.get("google_oauth_state")
    if not state or state != stored_state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    token_payload = await exchange_code_for_tokens(code)
    access_token = token_payload.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Google token exchange failed")

    profile = await fetch_google_userinfo(access_token)
    google_sub = profile.get("sub")
    email = profile.get("email")
    name = profile.get("name") or (email or "Google User")
    avatar_url = profile.get("picture")

    if not google_sub or not email:
        raise HTTPException(status_code=400, detail="Google profile is missing required fields")

    user = db.query(User).filter(User.google_sub == google_sub).first()
    if user is None:
        user = User(google_sub=google_sub, email=email, name=name, avatar_url=avatar_url)
        db.add(user)
    else:
        user.email = email
        user.name = name
        user.avatar_url = avatar_url

    db.commit()
    db.refresh(user)

    jwt_token = create_access_token(str(user.id), user.email)
    response = RedirectResponse(url=f"{settings.config.app.frontend_url}/documents")
    set_auth_cookie(response, jwt_token)
    return response


@router.get("/me")
def auth_me(user: User = Depends(get_current_user)):
    settings = get_settings()
    return JSONResponse({"user": _serialize_user(user), "dev_auth_bypass": settings.dev_auth_bypass})
