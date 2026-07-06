# app/schemas/job_description.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class JobDescriptionCreate(BaseModel):
    title: str
    company: str
    description: str

class JobDescriptionResponse(BaseModel):
    id: int
    title: str
    company: str
    description: str
    created_at: Optional[datetime] = None  # ✅ Make it optional
    
    class Config:
        from_attributes = True
        # ✅ Allow conversion from string to datetime
        coerce_numbers_to_str = True