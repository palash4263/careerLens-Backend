# app/services/optimization_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging
from typing import Dict, Any, Optional
import json

from app.models.resume import Resume
from app.models.job_description import JobDescription
from app.models.ats import ATSScore
from app.services.groq_service import GroqService
from app.services.ats_service import ATSService
from app.utils.skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)

class OptimizationService:
    
    def __init__(self):
        self.groq_service = GroqService()
        self.ats_service = ATSService()
    
    async def optimize_resume(
        self,
        db: AsyncSession,
        resume_id: int,
        job_description_id: int
    ) -> Dict[str, Any]:
        """Optimize a resume for a specific job description targeting 90+ score"""
        
        try:
            # Get resume and job
            resume = await self._get_resume(db, resume_id)
            job = await self._get_job(db, job_description_id)
            
            if not resume:
                raise ValueError(f"Resume with ID {resume_id} not found")
            if not job:
                raise ValueError(f"Job Description with ID {job_description_id} not found")
            
            logger.info(f"📝 Optimizing resume {resume_id} for job {job_description_id}")
            
            # Get current ATS score
            current_ats = await self.ats_service.calculate_score(
                db, resume_id, job_description_id
            )
            
            logger.info(f"📊 Current ATS score: {current_ats.score}")
            
            # Optimize using Groq with aggressive prompt
            optimized_text = await self.groq_service.optimize_resume(
                resume.extracted_text or "",
                job.description
            )
            
            logger.info(f"✅ Resume optimized successfully")
            
            # Analyze improvements
            improvements = self._analyze_improvements(
                resume.extracted_text or "",
                optimized_text,
                job.description
            )
            
            # Calculate estimated new score (more accurate)
            job_skills = set(SkillExtractor.extract_skills(job.description))
            optimized_skills = set(SkillExtractor.extract_skills(optimized_text))
            matched_skills = optimized_skills & job_skills
            
            # Calculate score based on keyword coverage
            if job_skills:
                # More aggressive scoring
                keyword_score = min(int((len(matched_skills) / len(job_skills)) * 100) + 15, 95)
                # Add bonus for quantified achievements
                quantified_bonus = self._count_quantified_achievements(optimized_text) * 2
                final_score = min(keyword_score + quantified_bonus, 95)
            else:
                final_score = 0
            
            result = {
                "original_text": resume.extracted_text,
                "optimized_text": optimized_text,
                "current_score": current_ats.score,
                "estimated_new_score": final_score,
                "improvements": improvements,
                "resume_id": resume_id,
                "job_description_id": job_description_id,
                "keywords_added": list(optimized_skills - set(SkillExtractor.extract_skills(resume.extracted_text or ""))),
                "keyword_coverage": len(matched_skills) / len(job_skills) * 100 if job_skills else 0
            }
            
            logger.info(f"📊 Estimated new score: {final_score}%")
            logger.info(f"📊 Keyword coverage: {result['keyword_coverage']:.1f}%")
            
            # Save optimization result to database (optional)
            # await self._save_optimization_result(db, result)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Optimization failed: {str(e)}")
            raise
    
    def _count_quantified_achievements(self, text: str) -> int:
        """Count quantified achievements in text"""
        import re
        patterns = [
            r'\d+%',  # percentages
            r'\d+x',  # multiples
            r'\$\d+',  # dollar amounts
            r'\d+\s*(?:million|billion|thousand|k|m|b)',  # large numbers
            r'(?:over|more than|less than|about|approximately)\s*\d+',  # approximate numbers
        ]
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        return min(count, 10)  # Cap at 10
    
    async def _get_resume(self, db: AsyncSession, resume_id: int) -> Optional[Resume]:
        """Get resume by ID"""
        try:
            result = await db.execute(
                select(Resume).where(Resume.id == resume_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error fetching resume: {str(e)}")
            return None
    
    async def _get_job(self, db: AsyncSession, job_id: int) -> Optional[JobDescription]:
        """Get job description by ID"""
        try:
            result = await db.execute(
                select(JobDescription).where(JobDescription.id == job_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"❌ Error fetching job: {str(e)}")
            return None
    
    def _analyze_improvements(self, original: str, optimized: str, job_description: str) -> Dict[str, Any]:
        """Analyze improvements between original and optimized resume"""
        
        try:
            original_skills = set(SkillExtractor.extract_skills(original))
            optimized_skills = set(SkillExtractor.extract_skills(optimized))
            job_skills = set(SkillExtractor.extract_skills(job_description))
            
            added_skills = optimized_skills - original_skills
            removed_skills = original_skills - optimized_skills
            matched_job_skills = optimized_skills & job_skills
            
            return {
                "added_skills": list(added_skills),
                "removed_skills": list(removed_skills),
                "matched_job_skills": list(matched_job_skills),
                "total_optimized_skills": len(optimized_skills),
                "total_original_skills": len(original_skills),
                "skill_improvement": len(optimized_skills) - len(original_skills),
                "job_skill_coverage": len(matched_job_skills) / len(job_skills) * 100 if job_skills else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing improvements: {str(e)}")
            return {
                "added_skills": [],
                "removed_skills": [],
                "matched_job_skills": [],
                "total_optimized_skills": 0,
                "total_original_skills": 0,
                "skill_improvement": 0,
                "job_skill_coverage": 0
            }

    async def optimize_section(
        self,
        db: AsyncSession,
        resume_id: int,
        section_name: str,
        job_description_id: int,
        custom_prompt: str = ""
    ) -> Dict[str, Any]:
        """Optimize a specific section of a resume using AI"""
        try:
            resume = await self._get_resume(db, resume_id)
            job = await self._get_job(db, job_description_id)
            
            if not resume:
                raise ValueError(f"Resume with ID {resume_id} not found")
            if not job:
                raise ValueError(f"Job Description with ID {job_description_id} not found")
                
            logger.info(f"📝 Optimizing section {section_name} of resume {resume_id} for job {job_description_id}")
            
            optimized_content = await self.groq_service.optimize_section(
                resume.extracted_text or "",
                section_name,
                job.description,
                custom_prompt
            )
            
            return {
                "section_name": section_name,
                "optimized_text": optimized_content
            }
        except Exception as e:
            logger.error(f"❌ Section optimization failed: {str(e)}")
            raise