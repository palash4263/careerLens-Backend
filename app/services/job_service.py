# app/services/job_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime

from app.models.job_description import JobDescription
from app.schemas.job_description import JobDescriptionCreate

class JobService:
    
    @staticmethod
    async def create_job(
        db: AsyncSession,
        request: JobDescriptionCreate
    ) -> JobDescription:
        """Create a new job description"""
        job = JobDescription(
            company=request.company,
            title=request.title,
            description=request.description,
            created_at=datetime.now()  # ✅ Explicitly set created_at
        )
        
        db.add(job)
        await db.commit()
        await db.refresh(job)
        
        return job
    
    @staticmethod
    async def get_job_by_id(
        db: AsyncSession,
        job_id: int
    ) -> Optional[JobDescription]:
        """Get a job description by ID"""
        result = await db.execute(
            select(JobDescription).where(JobDescription.id == job_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_jobs(
        db: AsyncSession
    ) -> List[JobDescription]:
        """Get all job descriptions"""
        result = await db.execute(
            select(JobDescription)
            .order_by(desc(JobDescription.created_at))
        )
        return result.scalars().all()

    @staticmethod
    async def delete_job(
        db: AsyncSession,
        job_id: int
    ) -> bool:
        """Delete a job description by ID"""
        result = await db.execute(
            select(JobDescription).where(JobDescription.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return False
            
        await db.delete(job)
        await db.commit()
        return True