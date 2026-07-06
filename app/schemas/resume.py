# app/schemas/resume.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResumeResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    uploaded_at: Optional[datetime] = None  # ✅ Make optional
    extracted_text: Optional[str] = None
    
    class Config:
        from_attributes = True

class ResumeUploadResponse(BaseModel):
    id: int
    file_name: str
    message: str

class ResumeDetailResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    uploaded_at: Optional[datetime] = None  # ✅ Make optional
    extracted_text: Optional[str] = None
    
    class Config:
        from_attributes = True