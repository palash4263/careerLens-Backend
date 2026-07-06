# app/schemas/auth.py
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)

class RegisterResponse(BaseModel):
    id: int
    name: str
    email: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    token_type: str = "bearer"
    user: Optional[dict] = None

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None