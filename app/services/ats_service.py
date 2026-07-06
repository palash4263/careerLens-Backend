# app/services/ats_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List
import json
import logging

from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.ats import ATSScore
from app.schemas.ats import ATSAnalysisResponse
from app.utils.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)

class ATSService:
    
    @staticmethod
    async def calculate_score(
        db: AsyncSession,
        resume_id: int,
        job_description_id: int
    ) -> ATSAnalysisResponse:
        """Calculate ATS score for a resume against a job description"""
        
        # Get resume
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        
        if not resume:
            raise ValueError(f"Resume with ID {resume_id} not found")
        
        # Get job description
        result = await db.execute(
            select(JobDescription).where(JobDescription.id == job_description_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            raise ValueError(f"Job Description with ID {job_description_id} not found")
        
        # Extract skills from description
        resume_skills = SkillExtractor.extract_skills(resume.extracted_text or "")
        job_skills = SkillExtractor.extract_skills(job.description)  # ✅ Extract from description directly
        
        # Calculate match
        matched_skills = [s for s in job_skills if s in resume_skills]
        missing_skills = [s for s in job_skills if s not in resume_skills]
        
        # Calculate score
        if job_skills:
            score = int((len(matched_skills) / len(job_skills)) * 100)
        else:
            score = 0
        
        # Generate recommendations
        recommendations = []
        if missing_skills:
            recommendations.append(f"Add these skills: {', '.join(missing_skills[:5])}")
        if score < 60:
            recommendations.append("Add more keywords from the job description")
        if score < 40:
            recommendations.append("Significant improvement needed for this role")
        if not recommendations:
            recommendations.append("Great match! Your resume aligns well with this role")
        
        # Save to database
        ats_score = ATSScore(
            resume_id=resume_id,
            job_description_id=job_description_id,
            score=score,
            matched_skills=", ".join(matched_skills),
            missing_skills=", ".join(missing_skills),
            recommendations=json.dumps(recommendations)
        )
        
        db.add(ats_score)
        await db.commit()
        await db.refresh(ats_score)
        
        return ATSAnalysisResponse(
            resume_id=resume_id,
            job_description_id=job_description_id,
            score=score,
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            recommendations=recommendations,
            keyword_match_percentage=score
        )
    
    @staticmethod
    async def get_score_history(
        db: AsyncSession,
        resume_id: int
    ) -> List[ATSScore]:
        """Get ATS score history for a resume"""
        result = await db.execute(
            select(ATSScore)
            .where(ATSScore.resume_id == resume_id)
            .order_by(desc(ATSScore.created_at))
        )
        return result.scalars().all()