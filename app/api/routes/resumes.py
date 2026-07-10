# app/api/routes/resumes.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.resume import ResumeResponse, ResumeUploadResponse, ResumeDetailResponse
from app.services.resume_service import ResumeService

router = APIRouter()

@router.post("/upload", response_model=ResumeUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a resume PDF"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    return await ResumeService.upload_resume(db, current_user.id, file, file.filename)

@router.get("/", response_model=List[ResumeResponse])
async def get_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all resumes"""
    resumes = await ResumeService.get_user_resumes(db, current_user.id)
    
    # ✅ Handle None values for uploaded_at
    for resume in resumes:
        if resume.uploaded_at is None:
            resume.uploaded_at = datetime.now()  # Set default if None
    
    return resumes

@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific resume by ID"""
    resume = await ResumeService.get_resume_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    # ✅ Handle None value for uploaded_at
    if resume.uploaded_at is None:
        resume.uploaded_at = datetime.now()
    
    return resume

@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a resume"""
    deleted = await ResumeService.delete_resume(db, resume_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Resume not found")

@router.get("/{resume_id}/file")
async def get_resume_file(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the physical PDF file of a resume"""
    import os
    from fastapi.responses import FileResponse
    
    resume = await ResumeService.get_resume_by_id(db, resume_id, current_user.id)
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    if not os.path.exists(resume.file_path):
        raise HTTPException(status_code=404, detail="Physical file not found")
    
    return FileResponse(
        path=resume.file_path,
        media_type="application/pdf",
        filename=resume.file_name
    )