from __future__ import annotations

from typing import AsyncGenerator

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from domain.entities.user import User
from domain.value_objects import UserRole

log = structlog.get_logger()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with request.app.state.session_factory() as session:
        yield session


async def get_redis(request: Request):
    return request.app.state.redis


async def get_current_user(
    request: Request,
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        jwt_service = request.app.state.jwt_service
        claims = jwt_service.decode_token(token)
        if claims.get("scope") == "mfa_pending" or claims.get("type") == "refresh":
            raise credentials_exception
        user_id_str: str | None = claims.get("sub")
        if not user_id_str:
            raise credentials_exception
    except ValueError:
        raise credentials_exception

    import uuid

    user_repo = request.app.state.user_repo
    user = await user_repo.find_by_id(uuid.UUID(user_id_str))
    if not user or not user.is_active:
        raise credentials_exception
    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required.",
        )
    return user
