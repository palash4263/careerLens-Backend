# app/api/routes/ats.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import json

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.ats import ATSScoreRequest, ATSAnalysisResponse, ATSScoreResponse
from app.services.ats_service import ATSService

router = APIRouter()

@router.post("/score", response_model=ATSAnalysisResponse)
async def calculate_ats_score(
    request: ATSScoreRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Calculate ATS score for a resume against a job description"""
    try:
        result = await ATSService.calculate_score(
            db,
            request.resume_id,
            request.job_description_id
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/history/{resume_id}", response_model=List[ATSScoreResponse])
async def get_ats_history(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get ATS score history for a resume"""
    try:
        scores = await ATSService.get_score_history(db, resume_id)
        
        result = []
        for score in scores:
            result.append(ATSScoreResponse(
                id=score.id,
                resume_id=score.resume_id,
                job_description_id=score.job_description_id,
                score=score.score,
                matched_skills=score.matched_skills.split(", ") if score.matched_skills else [],
                missing_skills=score.missing_skills.split(", ") if score.missing_skills else [],
                recommendations=json.loads(score.recommendations) if score.recommendations else [],
                created_at=score.created_at,
                updated_at=score.updated_at
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/test")
async def test_ats():
    return {"message": "ATS router is working!"}