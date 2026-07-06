# app/api/routes/jobs.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionResponse
from app.services.job_service import JobService

router = APIRouter()

@router.post("/", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description(
    request: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job description"""
    try:
        job = await JobService.create_job(db, request)
        
        # ✅ Ensure created_at is a datetime object
        created_at = job.created_at if hasattr(job, 'created_at') else datetime.now()
        
        return JobDescriptionResponse(
            id=job.id,
            title=job.title,
            company=job.company,
            description=job.description,
            created_at=created_at
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/", response_model=List[JobDescriptionResponse])
async def get_job_descriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all job descriptions"""
    try:
        jobs = await JobService.get_all_jobs(db)
        
        return [
            JobDescriptionResponse(
                id=job.id,
                title=job.title,
                company=job.company,
                description=job.description,
                created_at=job.created_at if hasattr(job, 'created_at') else None
            )
            for job in jobs
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))