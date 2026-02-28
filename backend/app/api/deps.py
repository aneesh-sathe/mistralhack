from __future__ import annotations

import uuid

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import SESSION_COOKIE, decode_access_token
from app.core.settings import get_settings
from app.db.models import User
from app.db.session import get_db

DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def ensure_dev_user(db: Session) -> User:
    user = db.get(User, DEV_USER_ID)
    if user:
        return user

    user = User(
        id=DEV_USER_ID,
        google_sub="dev-bypass",
        email="dev@example.com",
        name="Dev User",
        avatar_url=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    if settings.dev_auth_bypass:
        return ensure_dev_user(db)

    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    payload = decode_access_token(token)
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    try:
        user_id = uuid.UUID(str(sub))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session") from exc

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user
