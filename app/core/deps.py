# app/core/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError
from app.core.database import get_db
from app.core.security import decode_token
from app.services.auth_service import AuthService

import logging

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decode_token(token)
    user_id = payload.get("sub")

    if user_id is None:
        raise credentials_exception

    try:
        user = await AuthService.get_user_by_id(db, int(user_id))
    except (ValueError, TypeError):
        raise credentials_exception

    if user is None:
        raise credentials_exception

    logger.info(f"👤 Active user session: {user.email} (ID: {user.id})")
    return user