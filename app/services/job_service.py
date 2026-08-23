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
    async def search_jobs(keyword: str, location: str = "") -> dict:
        """Search and scrape jobs from Naukri and return 30 job listings"""
        import httpx
        import json
        import random
        from bs4 import BeautifulSoup

        try:
            jobs = []

            # 1. Try scraping Naukri
            naukri_jobs = await JobService._scrape_naukri(keyword, location)
            jobs.extend(naukri_jobs)

            # 2. If fewer than 30 jobs, use mock data to supplement
            if len(jobs) < 30:
                mock_jobs = JobService._generate_mock_jobs(keyword, location, 30 - len(jobs))
                jobs.extend(mock_jobs)

            # Return up to 30 jobs
            return {
                "success": True,
                "count": len(jobs),
                "jobs": jobs[:30]
            }
        except Exception as e:
            print(f"Scraping error: {str(e)}")
            # Fallback to mock data on error
            mock_jobs = JobService._generate_mock_jobs(keyword, location, 30)
            return {
                "success": True,
                "count": len(mock_jobs),
                "jobs": mock_jobs
            }

    @staticmethod
    async def _scrape_naukri(keyword: str, location: str = "") -> list:
        """Scrape job listings from Naukri"""
        import httpx
        from bs4 import BeautifulSoup
        from urllib.parse import quote

        try:
            # Build Naukri search URL
            search_term = f"{keyword} in {location}" if location else keyword
            url = f"https://www.naukri.com/jobs-{quote(keyword.lower())}-jobs"
            if location:
                url += f"-{quote(location.lower())}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []

            # Parse job listings from Naukri
            job_cards = soup.find_all('article', class_='jobTuple')[:15]

            for job_card in job_cards:
                try:
                    title_elem = job_card.find('a', class_='jobTitle')
                    company_elem = job_card.find('a', class_='companyName')
                    location_elem = job_card.find('span', class_='location')

                    if title_elem and company_elem:
                        job = {
                            "id": f"naukri-{len(jobs)}-{id(job_card)}",
                            "title": title_elem.get_text(strip=True),
                            "company": company_elem.get_text(strip=True),
                            "location": location_elem.get_text(strip=True) if location_elem else "India",
                            "link": title_elem.get('href', '#'),
                            "description": "Exciting opportunity to grow your career. Apply now!",
                            "source": "Naukri"
                        }
                        jobs.append(job)
                except Exception as e:
                    continue

            return jobs
        except Exception as e:
            print(f"Naukri scraping failed: {str(e)}")
            return []

    @staticmethod
    def _generate_mock_jobs(keyword: str, location: str, count: int) -> list:
        """Generate realistic mock job data"""
        import random
        from datetime import datetime, timedelta

        companies = [
            'TCS', 'Infosys', 'Wipro', 'HCL Technologies', 'Tech Mahindra', 'Cognizant',
            'Flipkart', 'Amazon India', 'Google India', 'Microsoft India', 'Meta India',
            'Zomato', 'Swiggy', 'Paytm', 'Dream11', 'Unacademy', 'Byju\'s', 'OYO',
            'Freshworks', 'MuSigma', 'Nutanix India', 'Rivigo', 'Dunzo', 'ShareChat',
            'Nykaa', 'BigBasket', 'Jio', 'Airtel', 'Idea Cellular', 'Reliance', 'Accenture India'
        ]

        indian_locations = [
            'Bangalore', 'Hyderabad', 'Mumbai', 'Delhi', 'Pune', 'Gurgaon', 'Noida',
            'Chennai', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Remote', 'Hybrid'
        ]

        descriptions = [
            'Join our team to build cutting-edge web applications. We work with React, Node.js, and modern cloud technologies.',
            'Help us scale our platform to millions of users. Strong backend experience required with focus on performance.',
            'Lead a team of engineers in building next-gen features. Experience with system design and mentorship a plus.',
            'Work on challenging problems in a fast-paced environment. We value innovation, collaboration, and continuous learning.',
            'Be part of a mission-driven company transforming the industry. Competitive salary and comprehensive benefits.',
            'Collaborate with cross-functional teams to deliver high-quality solutions. Exposure to cloud infrastructure and microservices.',
            'Develop scalable solutions for a global audience. We offer competitive compensation and career growth opportunities.',
            'Join our innovative team building solutions for millions. Experience with modern tech stack and agile methodologies.'
        ]

        jobs = []
        for i in range(count):
            posted_days_ago = random.randint(0, 7)
            jobs.append({
                "id": f"mock-{i}-{random.randint(1000, 9999)}",
                "title": keyword or 'Software Developer',
                "company": random.choice(companies),
                "location": location if location in indian_locations else random.choice(indian_locations),
                "link": f"https://www.naukri.com/jobs-{keyword.lower().replace(' ', '-')}-jobs",
                "description": random.choice(descriptions),
                "source": "Mock Data",
                "posted": (datetime.now() - timedelta(days=posted_days_ago)).isoformat()
            })

        return jobs

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