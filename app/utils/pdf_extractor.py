# app/utils/pdf_extractor.py
import PyPDF2
import pdfplumber
import logging

logger = logging.getLogger(__name__)

class PDFExtractor:
    
    @staticmethod
    def extract_text(file_path: str) -> str:
        """Extract text from PDF"""
        try:
            # Try pdfplumber first (better formatting)
            with pdfplumber.open(file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                if text.strip():
                    return text.strip()
        except Exception as e:
            logger.warning(f"pdfplumber failed: {e}")
        
        try:
            # Fallback to PyPDF2
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
                return text.strip()
        except Exception as e:
            logger.error(f"PyPDF2 failed: {e}")
        
        return "No text extracted from PDF"