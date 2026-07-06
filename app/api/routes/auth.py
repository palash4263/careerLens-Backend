# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    UserResponse
)
from app.services.auth_service import AuthService
from app.core.deps import get_current_user
from app.models.user import User
import logging
import traceback

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    try:
        logger.info(f"📝 Registering user: {request.email}")
        user = await AuthService.register(db, request)
        
        # ✅ Only return fields that exist
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
    # ✅ Only return fields that exist
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