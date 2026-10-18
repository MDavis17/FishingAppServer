from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import jwt
from sqlalchemy.orm import Session

from app.Auth.config import JWT_ALGORITHM, JWT_EXPIRY_MINUTES, JWT_SECRET_KEY
from app.Auth.models import User
from app.Auth.schemas import UserCreate


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email.lower()).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(
        email=user_data.email.lower(),
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_access_token(
    *, user_id: int, expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=JWT_EXPIRY_MINUTES)
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
