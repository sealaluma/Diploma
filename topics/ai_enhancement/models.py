from pydantic import BaseModel

class EnhancedThesisContent(BaseModel):
    """Pydantic model for structured AI response."""
    enhanced_title_en: str
    enhanced_title_kz: str
    enhanced_title_ru: str
    enhanced_description: str
