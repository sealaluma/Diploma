# Prompts for AI enhancement service

def get_enhancement_prompt(title_context: str, description: str) -> str:
    return f"""
        You are an expert academic advisor helping students improve their thesis topics.

        {title_context if title_context else "No title provided yet."}

        Current description:
        {description}

        Your task:
        1. Create or enhance an academic English title (10-15 words, clear and professional)
        2. Enhance the description (2-4 paragraphs, clear academic language, highlight research significance)
        3. Translate the enhanced English title to Kazakh (use proper academic Kazakh, not Russified)
        4. Translate the enhanced English title to Russian (use proper academic Russian)

        Requirements:
        - Keep the core research idea intact
        - Use appropriate academic tone for each language
        - Ensure consistency across all three language titles (same meaning)
        - Make description align with the enhanced English title
        - Focus on research significance and clarity

        Provide structured output with these exact fields.
    """