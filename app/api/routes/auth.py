# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import logging
import traceback

from app.core.database import get_db
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
    GoogleAuthRequest,
)
from app.services.auth_service import AuthService
from app.core.deps import get_current_user
from app.core.security import create_access_token
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# -------------------------------------------------------------------
# Existing endpoints
# -------------------------------------------------------------------

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    try:
        logger.info(f"📝 Registering user: {request.email}")
        user = await AuthService.register(db, request)
        return RegisterResponse(
            id=user.id,
            name=user.name,
            email=user.email
        )
    except ValueError as e:
        logger.warning(f"⚠️ Registration failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Registration error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """Login user and return JWT token"""
    try:
        logger.info(f"🔑 Login attempt for: {request.email}")
        result = await AuthService.login(db, request.email, request.password)
        logger.info(f"🔑 Manual login successful for: {request.email}")
        return LoginResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current authenticated user info"""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email
    )


@router.get("/protected")
async def protected_route(
    current_user: User = Depends(get_current_user)
):
    """Protected route example - requires authentication"""
    return {
        "message": "You are authorized!",
        "user": current_user.email
    }


@router.get("/test")
async def test_auth():
    """Test endpoint to verify auth router is working"""
    return {"message": "Auth router is working!"}


# -------------------------------------------------------------------
# Google Sign‑In endpoint (FIXED)
# -------------------------------------------------------------------

@router.post("/google", response_model=LoginResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate using Google ID token.
    Returns the same shape as /login (access_token, token_type, user).
    """
    credential = request.credential
    if not credential:
        raise HTTPException(status_code=400, detail="Missing credential")

    try:
        # 1. Verify the Google ID token
        info = id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID")
        )

        email = info.get("email")
        name = info.get("name")
        picture = info.get("picture")
        email_verified = info.get("email_verified")

        if not email_verified:
            raise HTTPException(status_code=400, detail="Email not verified")

    except ValueError as e:
        logger.warning(f"⚠️ Invalid Google token: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # 2. Find or create user
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            email=email,
            name=name,
            avatar=picture,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 3. Generate JWT token
    access_token = create_access_token(data={"sub": str(user.id)})

    # 4. ✅ Build UserResponse object
    user_response = UserResponse(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar=getattr(user, "avatar", None),
        role=getattr(user, "role", None),
        created_at=getattr(user, "created_at", None),
    )

    # 5. ✅ Return LoginResponse with the UserResponse object (FIXED typo)
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_response,   # ✅ Fixed: was 'user_res' before
    )


# -------------------------------------------------------------------
# Password Reset Endpoints
# -------------------------------------------------------------------
from pydantic import BaseModel, EmailStr
from datetime import timedelta
from app.core.security import get_password_hash, decode_token

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    password: str

@router.post("/forgot-password")
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Generate stateless reset token and print reset link to console log"""
    email = payload.email
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    # Stateless token generation (expires in 15 minutes)
    expires = timedelta(minutes=15)
    reset_token = create_access_token(
        data={"sub": email, "purpose": "reset"},
        expires_delta=expires
    )
    
    # Build local testing link
    reset_link = f"http://localhost:5173/reset-password?token={reset_token}"
    logger.info(f"🔑 PASSWORD RESET REQUESTED FOR: {email}")
    logger.info(f"🔗 RESET LINK FOR DEVELOPER: {reset_link}")
    
    return {
        "status": "success",
        "message": "If the email is registered, a password reset link has been logged in the backend console."
    }

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
):
    """Verify reset token and update database password"""
    token_data = decode_token(payload.token)
    if not token_data or token_data.get("purpose") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    email = token_data.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token payload")
        
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.password = get_password_hash(payload.password)
    await db.commit()
    
    logger.info(f"✅ Password reset successfully for: {email}")
    return {
        "status": "success",
        "message": "Password has been reset successfully. You can now log in."
    }