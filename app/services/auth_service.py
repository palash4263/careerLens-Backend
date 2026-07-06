# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.core.security import get_password_hash, verify_password, create_access_token
import logging

logger = logging.getLogger(__name__)

class AuthService:
    
    @staticmethod
    async def register(db: AsyncSession, request: RegisterRequest) -> User:
        """Register a new user"""
        try:
            # Check if user already exists
            result = await db.execute(select(User).where(User.email == request.email))
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise ValueError("Email already registered")
            
            # Create new user
            user = User(
                name=request.name,
                email=request.email,
                password=get_password_hash(request.password)
            )
            
            db.add(user)
            await db.commit()
            await db.refresh(user)
            
            logger.info(f"✅ User registered successfully: {user.email}")
            return user
            
        except Exception as e:
            logger.error(f"❌ Registration failed: {str(e)}")
            await db.rollback()
            raise
    
    @staticmethod
    async def login(db: AsyncSession, email: str, password: str) -> dict:
        """Authenticate user and return token"""
        try:
            # Find user by email
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"❌ User not found: {email}")
                raise ValueError("Invalid credentials")
            
            # Verify password
            if not verify_password(password, user.password):
                logger.warning(f"❌ Invalid password for: {email}")
                raise ValueError("Invalid credentials")
            
            # Create access token
            token_data = {"sub": user.email}
            token = create_access_token(token_data)
            
            logger.info(f"✅ User logged in: {user.email}")
            
            return {
                "token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
            }
        except Exception as e:
            logger.error(f"❌ Login failed: {str(e)}")
            raise
    
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = await db.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Get user failed: {str(e)}")
            return None