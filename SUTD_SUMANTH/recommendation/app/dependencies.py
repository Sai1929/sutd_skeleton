from typing import AsyncGenerator

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, UnauthorizedError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.db.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_rec_engine(request: Request):
    return request.app.state.rec_engine


async def get_reranker(request: Request):
    return request.app.state.reranker


async def get_azure_llm(request: Request):
    return request.app.state.azure_llm


async def get_azure_embedder(request: Request):
    return request.app.state.azure_embedder


async def get_rag_chain(request: Request):
    return request.app.state.rag_chain


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_token(token)
    except ValueError:
        raise UnauthorizedError("Could not validate credentials")

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject")

    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise NotFoundError("User not found")
    if not user.is_active:
        raise UnauthorizedError("Inactive user")
    return user


async def require_role(*roles: str):
    """Dependency factory — ensures current user has one of the given roles."""

    async def _check(current_user: User = Depends(get_current_user)) -> User:
        from app.core.exceptions import ForbiddenError

        if current_user.role not in roles:
            raise ForbiddenError(f"Required role(s): {roles}")
        return current_user

    return _check
