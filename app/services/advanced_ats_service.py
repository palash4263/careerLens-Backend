# app/services/advanced_ats_service.py
import re
from typing import Dict, List, Set
from app.utils.skill_extractor import SkillExtractor

class AdvancedATSService:
    """Advanced ATS scoring with multiple metrics"""
    
    @staticmethod
    def calculate_detailed_score(resume_text: str, job_description: str) -> Dict:
        """Calculate detailed ATS score with breakdown"""
        
        # Extract skills
        resume_skills = set(SkillExtractor.extract_skills(resume_text))
        job_skills = set(SkillExtractor.extract_skills(job_description))
        
        # 1. Skill Match Score (40% weight)
        matched_skills = resume_skills & job_skills
        skill_match_score = (len(matched_skills) / len(job_skills) * 100) if job_skills else 0
        
        # 2. Keyword Density Score (30% weight)
        keyword_density_score = AdvancedATSService._calculate_keyword_density(resume_text, job_description)
        
        # 3. Quantified Achievements Score (20% weight)
        quantified_score = AdvancedATSService._calculate_quantified_score(resume_text)
        
        # 4. Formatting Score (10% weight)
        formatting_score = AdvancedATSService._calculate_formatting_score(resume_text)
        
        # Weighted total
        total_score = (
            skill_match_score * 0.40 +
            keyword_density_score * 0.30 +
            quantified_score * 0.20 +
            formatting_score * 0.10
        )
        
        return {
            "total_score": min(int(total_score), 100),
            "skill_match_score": int(skill_match_score),
            "keyword_density_score": int(keyword_density_score),
            "quantified_score": int(quantified_score),
            "formatting_score": int(formatting_score),
            "matched_skills": list(matched_skills),
            "missing_skills": list(job_skills - resume_skills),
            "skill_coverage": len(matched_skills) / len(job_skills) * 100 if job_skills else 0
        }
    
    @staticmethod
    def _calculate_keyword_density(text: str, job_description: str) -> float:
        """Calculate keyword density score"""
        # Extract keywords from job description
        words = re.findall(r'\b[a-zA-Z]{3,}\b', job_description.lower())
        job_keywords = set([w for w in words if len(w) > 3])
        
        if not job_keywords:
            return 0
        
        # Count occurrences in resume
        resume_words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        resume_word_count = len(resume_words)
        
        if resume_word_count == 0:
            return 0
        
        matches = sum(1 for word in resume_words if word in job_keywords)
        density = (matches / resume_word_count) * 100
        
        # Scale to 0-100
        return min(density * 2, 100)  # 50% density = 100 score
    
    @staticmethod
    def _calculate_quantified_score(text: str) -> float:
        """Calculate score based on quantified achievements"""
        patterns = [
            r'\d+%',
            r'\d+x',
            r'\$\d+',
            r'\d+\s*(?:million|billion|thousand|k|m|b)',
            r'(?:over|more than|less than|about|approximately)\s*\d+',
        ]
        
        count = 0
        for pattern in patterns:
            count += len(re.findall(pattern, text, re.IGNORECASE))
        
        # 10+ quantified achievements = 100 score
        return min(count * 10, 100)
    
    @staticmethod
    def _calculate_formatting_score(text: str) -> float:
        """Calculate formatting score"""
        score = 0
        
        # Check for bullet points
        if re.search(r'[•·●◦◆▶■]', text):
            score += 30
        
        # Check for proper sections
        sections = ['summary', 'experience', 'education', 'skills']
        for section in sections:
            if re.search(rf'\b{section}\b', text.lower()):
                score += 10
        
        # Check for numbers in experience
        if re.search(r'\d+', text):
            score += 20
        
        # Check for consistent formatting
        if text.count('\n') > 20:  # Proper line breaks
            score += 20
        
        return min(score, 100)