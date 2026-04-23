from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.exceptions import ConflictError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User
from app.dependencies import get_current_user, get_db
from app.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserOut:
    # Check duplicate student_id
    dup = await db.execute(select(User).where(User.student_id == body.student_id))
    if dup.scalar_one_or_none():
        raise ConflictError("Student ID already registered")

    # Check duplicate email
    dup_email = await db.execute(select(User).where(User.email == body.email))
    if dup_email.scalar_one_or_none():
        raise ConflictError("Email already registered")

    user = User(
        student_id=body.student_id,
        email=body.email,
        password_hash=hash_password(body.password),
        full_name=body.full_name,
        role="student",
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    result = await db.execute(select(User).where(User.student_id == body.student_id))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(body.password, user.password_hash):
        raise UnauthorizedError("Invalid student ID or password")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")

    access_token = create_access_token(str(user.id), {"role": user.role})
    refresh_token = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    try:
        payload = decode_token(body.refresh_token)
    except ValueError:
        raise UnauthorizedError("Invalid refresh token")

    if payload.get("type") != "refresh":
        raise UnauthorizedError("Not a refresh token")

    user_id = payload["sub"]
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")

    access_token = create_access_token(str(user.id), {"role": user.role})
    new_refresh = create_refresh_token(str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/token", include_in_schema=False)
async def oauth2_token(form: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """OAuth2 form-data endpoint used by Swagger UI Authorize button."""
    result = await db.execute(select(User).where(User.student_id == form.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form.password, user.password_hash):
        raise UnauthorizedError("Invalid credentials")
    if not user.is_active:
        raise UnauthorizedError("Account is inactive")
    return {"access_token": create_access_token(str(user.id), {"role": user.role}), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)
