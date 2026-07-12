# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import os

from app.api.routes import auth, resumes, ats, jobs, optimization, payments  # ✅ Make sure payments is imported
from app.core.database import init_db
from app.config import settings

# Create upload directories
os.makedirs("uploads/resumes", exist_ok=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Powered Resume Optimization Platform",
    version=settings.APP_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Include ALL routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(resumes.router, prefix="/api/resumes", tags=["Resumes"])
app.include_router(ats.router, prefix="/api/ats", tags=["ATS"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(optimization.router, prefix="/api/optimization", tags=["Optimization"])  # ✅ Add this
app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])  # ✅ Razorpay integration

@app.on_event("startup")
async def startup_event():
    try:
        logger.info("🚀 Starting up...")
        await init_db()
        logger.info("✅ Application startup complete!")
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

@app.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs"
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )