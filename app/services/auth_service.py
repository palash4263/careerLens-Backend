# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import os
import logging

from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.core.security import get_password_hash, verify_password, create_access_token

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
            token_data = {"sub": str(user.id)}
            token = create_access_token(token_data)
            
            logger.info(f"✅ User logged in: {user.email}")
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "avatar": getattr(user, "avatar", None),
                    "role": getattr(user, "role", None),
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

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Get user by id failed: {str(e)}")
            return None
    
    # ========== GOOGLE SIGN-IN ==========
    
    @staticmethod
    async def google_auth(db: AsyncSession, credential: str) -> dict:
        """
        Authenticate using Google ID token.
        Creates a new user if one doesn't exist.
        """
        try:
            # Verify the Google ID token
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
                raise ValueError("Email not verified by Google")

            # Check if user exists
            result = await db.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

            if not user:
                # Create a new user (password is None for Google users)
                user = User(
                    email=email,
                    name=name,
                    avatar=picture,
                    # password remains None (make sure your User model allows nullable password)
                )
                db.add(user)
                await db.commit()
                await db.refresh(user)
                logger.info(f"✅ New user created via Google: {user.email}")

            # Generate JWT token
            token_data = {"sub": str(user.id)}
            access_token = create_access_token(token_data)

            logger.info(f"✅ Google login successful: {user.email}")

            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "avatar": getattr(user, "avatar", None),
                    "role": getattr(user, "role", None),
                }
            }

        except ValueError as e:
            logger.warning(f"⚠️ Google auth failed: {str(e)}")
            raise ValueError("Invalid Google token: " + str(e))
        except Exception as e:
            logger.error(f"❌ Google auth error: {str(e)}")
            raise