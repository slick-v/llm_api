from datetime import datetime, timedelta, timezone


import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
import sentry_sdk

from app.config import settings
from app.db import get_db
from app.models import User


password_hasher = PasswordHash.recommended() #argon2
# auto_error=False so we can send our own 401 message

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hasher.verify(password, hashed)

def create_access_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        db: Session = Depends(get_db)) -> User:
    """FastAPI dependency: the logged-in user , or a 401."""
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Please log in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try: 
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp", "sub"]},
        )
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, ValueError):
        raise unauthorized

    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    
    sentry_sdk.set_user({"id": str(user.id)})  # id only, never the email
    return user
