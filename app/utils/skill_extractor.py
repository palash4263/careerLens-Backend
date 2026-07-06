# app/utils/skill_extractor.py
import re
from typing import List, Set
import logging

logger = logging.getLogger(__name__)

class SkillExtractor:
    
    # Common tech skills
    COMMON_SKILLS = {
        # Programming Languages
        "python", "java", "javascript", "typescript", "c++", "c#", "ruby", "go", "rust",
        "swift", "kotlin", "php", "scala", "perl", "r", "matlab", "sql", "nosql",
        
        # Frameworks
        "spring boot", "django", "flask", "react", "angular", "vue", "node.js", "express",
        "rails", "laravel", "asp.net", "fastapi", "tornado", "bootstrap", "tailwind",
        
        # Databases
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra", "dynamodb",
        "oracle", "sql server", "sqlite", "firebase", "neo4j",
        
        # Cloud & DevOps
        "aws", "azure", "gcp", "docker", "kubernetes", "jenkins", "git", "github actions",
        "terraform", "ansible", "chef", "puppet", "prometheus", "grafana", "elk",
        
        # AI/ML
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy", "opencv", "nlp",
        "langchain", "openai", "huggingface", "transformers", "llama", "chatgpt",
        
        # Other
        "rest api", "graphql", "microservices", "ci/cd", "agile", "scrum", "jira",
        "confluence", "leadership", "communication", "problem solving"
    }
    
    @staticmethod
    def extract_skills(text: str) -> List[str]:
        """Extract skills from text"""
        if not text:
            return []
        
        text_lower = text.lower()
        found_skills = set()
        
        for skill in SkillExtractor.COMMON_SKILLS:
            if skill in text_lower:
                found_skills.add(skill)
        
        return sorted(list(found_skills))