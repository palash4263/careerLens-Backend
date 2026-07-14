from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.job_description import JobDescriptionCreate
from app.services.job_service import JobService

router = APIRouter()


# --- Extra request schema for URL-based job import ---

class JobUrlRequest(BaseModel):
    url: str


# --- Helper to serialize a JobDescription ORM object ---

def serialize_job(job) -> dict:
    return {
        "id": job.id,
        "user_id": job.user_id,
        "company": job.company,
        "title": job.title,
        "description": job.description,
        "created_at": job.created_at,
    }


# --- Endpoints ---

@router.get("")
@router.get("/")
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all job descriptions for the current user"""
    jobs = await JobService.get_all_jobs(db, current_user.id)
    return [serialize_job(job) for job in jobs]


@router.post("")
@router.post("/")
async def create_job(
    payload: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new job description"""
    job = await JobService.create_job(db, payload, current_user.id)
    return serialize_job(job)


@router.get("/{job_id}")
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a single job description by ID"""
    job = await JobService.get_job_by_id(db, job_id, current_user.id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return serialize_job(job)


@router.delete("/{job_id}")
async def delete_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a job description by ID"""
    success = await JobService.delete_job(db, job_id, current_user.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return {"message": "Job deleted successfully"}


@router.post("/fetch-from-url")
async def fetch_job_from_url(
    payload: JobUrlRequest,
    current_user: User = Depends(get_current_user)
):
    """Scrape and parse a job posting from a URL using AI"""
    try:
        data = await JobService.fetch_job_from_url(payload.url)
        return data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))