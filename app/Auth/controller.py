from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.Auth.database import get_db
from app.Auth.dependencies import get_current_user
from app.Auth.models import User
from app.Auth.schemas import Token, UserCreate, UserLogin, UserResponse
from app.Auth import service as auth_service

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing = auth_service.get_user_by_email(db, user.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    return auth_service.create_user(db, user)


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    user = auth_service.get_user_by_email(db, credentials.email)
    if user is None or not auth_service.verify_password(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    access_token = auth_service.create_access_token(user_id=user.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
