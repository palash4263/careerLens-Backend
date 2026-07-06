# app/models/ats.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base

class ATSScore(Base):  # ✅ Fixed: ATSScore (not ATSSCore)
    __tablename__ = "ats_scores"  # ✅ Fixed: __tablename__ (not _tablename_)

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description_id = Column(Integer, ForeignKey("job_descriptions.id"), nullable=True)
    score = Column(Integer, default=0)
    matched_skills = Column(Text, nullable=True)
    missing_skills = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())