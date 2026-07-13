# app/services/groq_service.py
from groq import AsyncGroq
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class GroqService:
    
    def __init__(self):
        if not settings.GROQ_API_KEY:
            logger.warning("⚠️ GROQ_API_KEY not set in environment variables")
        
        self.client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.temperature = settings.GROQ_TEMPERATURE
        self.max_tokens = 8192  # ✅ Increased for longer responses
    
    async def optimize_resume(
        self, 
        resume_text: str, 
        job_description: str
    ) -> str:
        """Optimize resume using Groq AI with detailed content"""
        try:
            prompt = self._build_detailed_optimization_prompt(resume_text, job_description)
            
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_detailed_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.85,
                max_tokens=8192,  # ✅ Maximum tokens for detailed response
            )
            
            optimized_text = response.choices[0].message.content
            logger.info(f"✅ Resume optimized using Groq model: {self.model}")
            logger.info(f"📝 Optimized text length: {len(optimized_text)} characters")
            
            return optimized_text
            
        except Exception as e:
            logger.error(f"❌ Groq optimization failed: {str(e)}")
            return resume_text
    
    def _get_detailed_system_prompt(self) -> str:
        return """You are an elite ATS (Applicant Tracking System) resume optimization expert. 
        Your goal is to create a comprehensive, detailed, and highly optimized resume.

        CRITICAL REQUIREMENTS:
        1. EXPAND EVERY SECTION:
           - Summary: Write 4-6 lines with specific achievements and skills
           - Experience: Write 8-12 bullet points per job with quantified achievements
           - Projects: Write 5-8 bullet points per project with technical details
           - Education: Include CGPA, specializations, relevant coursework
           - Skills: Organize by category (Languages, Frameworks, Tools, Cloud, etc.)
           - Add Certifications section if applicable
           - Add Languages section

        2. QUANTIFY EVERYTHING:
           - Use specific numbers: % improvements, time saved, cost reduction
           - Example: "Reduced response time by 40%" (not just "Reduced response time")
           - Example: "Improved system efficiency by 30%" (not just "Improved efficiency")

        3. USE POWERFUL ACTION VERBS:
           - Architected, Designed, Implemented, Developed, Optimized
           - Built, Deployed, Integrated, Automated, Streamlined
           - Led, Managed, Coordinated, Delivered, Achieved

        4. INCLUDE TECHNICAL DETAILS:
           - Specific technologies, frameworks, and tools used
           - Architecture patterns (Microservices, Layered, Event-Driven)
           - Security implementations (JWT, OAuth, RBAC, SSL)
           - Performance optimizations (Caching, Query Optimization)

        5. ADD CERTIFICATIONS AND LANGUAGES:
           - Include relevant certifications
           - Add language proficiency levels

        IMPORTANT: The resume should be comprehensive, detailed, and ATS-friendly.
        Do NOT invent experience or qualifications.
        Only use information present in the original resume."""
    
    def _build_detailed_optimization_prompt(self, resume_text: str, job_description: str) -> str:
        return f"""
        🎯 TARGET: Create a comprehensive, detailed resume with maximum ATS compatibility
        
        JOB DESCRIPTION (Extract ALL keywords):
        {job_description}
        
        ORIGINAL RESUME:
        {resume_text}
        
        INSTRUCTIONS:
        1. ✅ EXPAND SUMMARY: Write a compelling 4-6 line professional summary
        2. ✅ EXPAND EXPERIENCE: Write 8-12 detailed bullet points per job with:
           - Quantified achievements (%, numbers, time saved)
           - Specific technologies used
           - Architecture and design decisions
           - Security implementations
           - Performance improvements
        3. ✅ EXPAND PROJECTS: Write 5-8 bullet points per project with:
           - Technical implementation details
           - Technologies and frameworks used
           - Quantified results and impact
           - Architecture patterns
        4. ✅ ENHANCE EDUCATION: Include CGPA, specializations, relevant coursework
        5. ✅ ORGANIZE SKILLS: Group by category (Languages, Frameworks, Tools, Cloud, etc.)
        6. ✅ ADD CERTIFICATIONS: Include relevant certifications if mentioned
        7. ✅ ADD LANGUAGES: Include language proficiency levels
        
        FORMAT:
        - Use clear section headings
        - Use bullet points for experience and projects
        - Keep a professional, clean format
        
        Return ONLY the optimized resume text.
        Make it comprehensive and detailed.
        """

    async def optimize_section(
        self,
        resume_text: str,
        section_name: str,
        job_description: str,
        custom_prompt: str = ""
    ) -> str:
        """Optimize a specific section of a resume using Groq AI"""
        try:
            prompt = f"""
            🎯 TARGET: Optimize the "{section_name}" section of a resume for maximum ATS compatibility.
            
            JOB DESCRIPTION (Target keywords and skills):
            {job_description}
            
            ORIGINAL RESUME CONTENT:
            {resume_text}
            
            INSTRUCTIONS:
            1. Rewrite and optimize only the "{section_name}" section.
            2. Integrate relevant keywords and skills from the job description naturally.
            3. Quantify achievements (percentages, numbers, impact) where possible.
            4. Keep the output professional, detailed, and clean.
            5. Return ONLY the rewritten content for the "{section_name}" section. Do NOT include any intro, outro, headers, markdown tags like ``` or explanation. Just return the optimized text.
            """
            
            if custom_prompt:
                prompt += f"\nADDITIONAL CUSTOMIZATION INSTRUCTIONS FROM USER:\n{custom_prompt}\n"
                
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an elite ATS resume optimization expert. Write optimized resume sections based on job descriptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=2048,
            )
            
            optimized_text = response.choices[0].message.content.strip()
            if optimized_text.startswith("```"):
                lines = optimized_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                optimized_text = "\n".join(lines).strip()
                
            return optimized_text
        except Exception as e:
            logger.error(f"❌ Groq section optimization failed: {str(e)}")
            return ""