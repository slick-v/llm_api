import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.rate_limit import RateLimiter
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut
from app.security import create_access_token, get_current_user, hash_password, verify_password

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])

login_limiter = RateLimiter(5, 60)       # 5 login tries per email per minute
register_limiter = RateLimiter(10, 60)   # 10 new accounts per minute, site-wide

# checked when the email doesn't exist, so "wrong email" takes as long as
# "wrong password" and an attacker can't tell which emails have accounts
DUMMY_HASH = hash_password("not-a-real-password")


def token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(user.id),
        user=UserOut.model_validate(user),
    )

@router.post("/register", response_model=TokenResponse,
            status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db:Session = Depends(get_db)):
    if not register_limiter.allow("all"):
        raise HTTPException(status_code=429, detail="Too many sign-ups right now. Try again in a minute.")

    user = User(email=body.email.lower(),
                password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    db.refresh(user)

    logger.info("New user registered: id=%s", user.id)
    return token_response(user)

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db:Session= Depends(get_db)):
    email = body.email.lower()
    if not login_limiter.allow(email):
        raise HTTPException(status_code=429, detail="Too many login attempts. Wait a minute and try again.")

    user = db.scalar(select(User).where(User.email == email))
    hashed = user.password_hash if user else DUMMY_HASH
    if not verify_password(body.password, hashed) or user is None:
         # same message for both cases on purpose
        raise HTTPException(status_code=401, detail="Wrong email or password.")

    return token_response(user)

@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

