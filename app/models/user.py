# app/models/user.py
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    password = Column(String(255), nullable=True)   # ✅ allow null for Google users
    avatar = Column(String(500), nullable=True)     # optional – store profile picture
    role = Column(String(50), default="user")
    created_at = Column(DateTime, server_default="NOW()")  # if you have timestamps