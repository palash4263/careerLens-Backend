# app/schemas/ats.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ATSScoreRequest(BaseModel):
    resume_id: int
    job_description_id: int

class ATSScoreResponse(BaseModel):
    id: int
    resume_id: int
    job_description_id: Optional[int] = None
    score: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    recommendations: List[str] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

class ATSAnalysisResponse(BaseModel):
    resume_id: int
    job_description_id: Optional[int] = None
    score: int
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    keyword_match_percentage: float