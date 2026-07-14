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
        request: JobDescriptionCreate,
        user_id: int
    ) -> JobDescription:
        """Create a new job description"""
        job = JobDescription(
            user_id=user_id,
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
        job_id: int,
        user_id: int
    ) -> Optional[JobDescription]:
        """Get a job description by ID"""
        result = await db.execute(
            select(JobDescription)
            .where(JobDescription.id == job_id)
            .where(JobDescription.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_all_jobs(
        db: AsyncSession,
        user_id: int
    ) -> List[JobDescription]:
        """Get all job descriptions"""
        result = await db.execute(
            select(JobDescription)
            .where(JobDescription.user_id == user_id)
            .order_by(desc(JobDescription.created_at))
        )
        return result.scalars().all()

    @staticmethod
    async def delete_job(
        db: AsyncSession,
        job_id: int,
        user_id: int
    ) -> bool:
        """Delete a job description by ID"""
        result = await db.execute(
            select(JobDescription)
            .where(JobDescription.id == job_id)
            .where(JobDescription.user_id == user_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            return False
            
        await db.delete(job)
        await db.commit()
        return True

    @staticmethod
    async def fetch_job_from_url(url: str) -> dict:
        """Fetch job page from URL, parse text with BeautifulSoup and extract fields with Groq LLM"""
        import httpx
        import json
        import re
        from bs4 import BeautifulSoup
        from app.services.groq_service import GroqService

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        
        # 1. Fetch HTML content
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                html_content = response.text
            except Exception as e:
                raise Exception(f"Failed to retrieve page content: {str(e)}")

        # 2. Parse HTML text with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Strip script, style and navigation tags
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
            
        raw_text = soup.get_text(separator=" ")
        # Clean whitespaces
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        
        # Cap length to stay safe under token limits
        clean_text = clean_text[:12000]

        # 3. Call Groq AI to parse fields
        groq_service = GroqService()
        
        system_prompt = (
            "You are an expert job description parser. Analyze the scraped text from a job board and extract: "
            "Job Title, Company Name, and the full Job Description/requirements. "
            "Return ONLY a valid JSON object matching this schema:\n"
            "{\n"
            '  "title": "Job Title",\n'
            '  "company": "Company Name",\n'
            '  "description": "Formatted markdown job description, listing duties, technologies, and candidate criteria."\n'
            "}\n"
            "Do NOT return any other text, markdown block formatting (like ```json), introduction, or explanations. Return raw JSON text only."
        )
        
        user_prompt = f"Scraped job posting text:\n\n{clean_text}"

        try:
            completion = await groq_service.client.chat.completions.create(
                model=groq_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2048,
            )
            
            content = completion.choices[0].message.content.strip()
            
            # Clean markdown code wrapper blocks if present
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
                
            data = json.loads(content)
            title = data.get("title", "").strip()
            company = data.get("company", "").strip()
            description = data.get("description", "").strip()

            if not title and not description:
                raise Exception("This job site is protected by anti-bot firewalls (like Cloudflare/CAPTCHA) or requires JavaScript to load. Please copy and paste the job details manually.")

            return {
                "title": title,
                "company": company,
                "description": description
            }
        except Exception as e:
            raise Exception(f"AI parsing of job page failed: {str(e)}")