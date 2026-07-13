# app/services/resume_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import os
import shutil
from datetime import datetime
import logging

from app.models.resume import Resume
from app.schemas.resume import ResumeUploadResponse
from app.utils.pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)

class ResumeService:
    
    UPLOAD_DIR = "uploads/resumes"
    
    @staticmethod
    async def upload_resume(db: AsyncSession, user_id: int, file, file_name: str):
        os.makedirs(ResumeService.UPLOAD_DIR, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file_name.replace(' ', '_')}"
        file_path = os.path.join(ResumeService.UPLOAD_DIR, safe_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Extract text from PDF
        extracted_text = PDFExtractor.extract_text(file_path)
        
        # Create resume with uploaded_at set to now
        resume = Resume(
            user_id=user_id,
            file_name=file_name,
            file_path=file_path,
            extracted_text=extracted_text,
            uploaded_at=datetime.now()  # ✅ Explicitly set
        )
        
        db.add(resume)
        await db.commit()
        await db.refresh(resume)
        
        return ResumeUploadResponse(
            id=resume.id,
            file_name=resume.file_name,
            message="Resume uploaded successfully"
        )
    
    @staticmethod
    async def get_user_resumes(db: AsyncSession, user_id: int):
        result = await db.execute(
            select(Resume)
            .where(Resume.user_id == user_id)
            .order_by(desc(Resume.uploaded_at).nulls_last())  # ✅ Handle nulls
        )
        return result.scalars().all()
    
    @staticmethod
    async def get_resume_by_id(db: AsyncSession, resume_id: int, user_id: int):
        result = await db.execute(
            select(Resume)
            .where(Resume.id == resume_id)
            .where(Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        return resume
    
    @staticmethod
    async def delete_resume(db: AsyncSession, resume_id: int, user_id: int):
        result = await db.execute(
            select(Resume)
            .where(Resume.id == resume_id)
            .where(Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            return False
        
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
        
        await db.delete(resume)
        await db.commit()
        return True