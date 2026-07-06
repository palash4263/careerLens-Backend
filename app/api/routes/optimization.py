# app/api/routes/optimization.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.optimization_service import OptimizationService

router = APIRouter()

@router.post("/optimize")
async def optimize_resume(
    resume_id: int,
    job_description_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Optimize a resume for a specific job description using AI"""
    try:
        service = OptimizationService()
        result = await service.optimize_resume(db, resume_id, job_description_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/optimize-section")
async def optimize_section(
    resume_id: int,
    section_name: str,
    job_description_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Optimize a specific section of a resume"""
    try:
        service = OptimizationService()
        result = await service.optimize_section(db, resume_id, section_name, job_description_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/test")
async def test_optimization():
    """Test endpoint to verify optimization router is working"""
    return {"message": "Optimization router is working!"}