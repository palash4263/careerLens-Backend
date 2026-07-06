# app/models/job_description.py
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime

class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(255), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)  # ✅ Use default=datetime.now
    
    def __repr__(self):
        return f"<JobDescription {self.title} at {self.company}>"