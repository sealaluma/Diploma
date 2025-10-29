"""
AI service for enhancing thesis topic descriptions using Google Gemini.
"""
import os
import logging
from google import genai
from google.genai import types
from typing import Optional
from .prompts import get_enhancement_prompt
from .models import EnhancedThesisContent

logger = logging.getLogger(__name__)


def get_gemini_client():
    """Get configured Gemini client."""
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)


def enhance_thesis_content(
    description: str,
    title_en: Optional[str] = None,
    title_kz: Optional[str] = None,
    title_ru: Optional[str] = None
) -> EnhancedThesisContent:
    """
    Enhance thesis topic titles and description using Google Gemini AI.
    
    This function enhances the English title and description, then translates
    the enhanced English title to Kazakh and Russian for consistency.
    
    Args:
        description: The original description text to enhance (required)
        title_en: English title (optional, will be generated if not provided)
        title_kz: Kazakh title (optional, used as reference)
        title_ru: Russian title (optional, used as reference)
        
    Returns:
        EnhancedThesisContent object with all enhanced fields
        
    Raises:
        ValueError: If the description is empty or API key is missing
        Exception: If the API call fails
    """
    if not description or not description.strip():
        raise ValueError("Description cannot be empty")
    
    try:
        client = get_gemini_client()
        
        title_context = ""
        if title_en:
            title_context += f"Current English title: {title_en}\n"
        if title_kz:
            title_context += f"Current Kazakh title: {title_kz}\n"
        if title_ru:
            title_context += f"Current Russian title: {title_ru}\n"
        
        prompt = get_enhancement_prompt(title_context, description)
        
        logger.info("Sending request to Gemini API for thesis content enhancement")
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json',
                response_schema=EnhancedThesisContent,
            ),
        )
        
        if not response or not response.text:
            raise Exception("No response received from Gemini API")
        
        enhanced_content = response.parsed
        
        logger.info("Successfully enhanced thesis content")
        logger.info(f"Enhanced EN title: {enhanced_content.enhanced_title_en[:50]}...")
        
        return enhanced_content
        
    except ValueError as ve:
        logger.error(f"Validation error: {str(ve)}")
        raise
    except Exception as e:
        logger.error(f"Error enhancing thesis content with AI: {str(e)}")
        raise Exception(f"Failed to enhance thesis content: {str(e)}")
