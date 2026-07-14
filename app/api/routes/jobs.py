from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.optimization_service import OptimizationService

router = APIRouter()

# --- Request Data Schemas ---

class OptimizeResumeRequest(BaseModel):
    resume_id: int
    job_description_id: int

class OptimizeSectionRequest(BaseModel):
    resume_id: int
    section_name: str
    job_description_id: int
    prompt: Optional[str] = None
    instructions: Optional[str] = None


# --- Endpoints ---

@router.post("/optimize")
async def optimize_resume(
    payload: OptimizeResumeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Optimize a resume for a specific job description using AI"""
    try:
        service = OptimizationService()
        result = await service.optimize_resume(db, payload.resume_id, payload.job_description_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/optimize-section")
async def optimize_section(
    payload: OptimizeSectionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Optimize a specific section of a resume"""
    try:
        service = OptimizationService()
        # Fall back gracefully through prompt definitions
        custom_prompt = payload.prompt or payload.instructions or ""
        
        result = await service.optimize_section(
            db, 
            payload.resume_id, 
            payload.section_name, 
            payload.job_description_id, 
            custom_prompt
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/test")
async def test_optimization():
    """Test endpoint to verify optimization router is working"""
    return {"message": "Optimization router is working!"}