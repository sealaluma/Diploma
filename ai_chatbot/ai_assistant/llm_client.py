import logging
import os
from typing import Dict, Any
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


def get_gemini_client():
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)

FUNCTION_DECLARATIONS = [
    types.FunctionDeclaration(
        name="search_topics",
        description=(
            "Search for thesis topics by keywords and required skills. "
            "Use when student asks about topics in specific areas like ML, web dev, etc. "
            "IMPORTANT: Include both full terms AND abbreviations in keywords."
        ),
        parameters={
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Keywords to search. Include both full terms and abbreviations. "
                        "Examples: ['machine learning', 'ML'], ['AI', 'artificial intelligence']"
                    )
                },
                "required_skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by skills (e.g., ['Python', 'TensorFlow'])"
                },
                "available_only": {
                    "type": "boolean",
                    "description": "Only available topics (default: true)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 10)"
                }
            },
            "required": []
        }
    ),
    types.FunctionDeclaration(
        name="search_supervisors",
        description=(
            "Search for thesis supervisors by research interests. "
            "Use when student asks about finding supervisors for specific areas. "
            "IMPORTANT: Include both full terms AND abbreviations in keywords. "
            "For example, for 'machine learning' also include 'ML', for 'artificial intelligence' include 'AI'."
        ),
        parameters={
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": (
                        "Keywords for research interests. Include both full terms and abbreviations. "
                        "Examples: ['machine learning', 'ML'], ['artificial intelligence', 'AI'], "
                        "['natural language processing', 'NLP']"
                    )
                },
                "skills": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Skills to match"
                },
                "available_only": {
                    "type": "boolean",
                    "description": "Only available supervisors (default: true)"
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default: 5)"
                }
            },
            "required": []
        }
    ),
    types.FunctionDeclaration(
        name="recommend_topics_by_skills",
        description=(
            "Get personalized topic recommendations based on student's skills. "
            "Use when student asks for recommendations or what matches their profile. "
            "This function already knows the student's skills, so call it directly - "
            "no need to call get_student_profile first."
        ),
        parameters={
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "integer",
                    "description": "Student ID"
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of recommendations (default: 5)"
                }
            },
            "required": ["student_id"]
        }
    ),
    types.FunctionDeclaration(
        name="get_student_profile",
        description=(
            "Get student's profile with skills, specialization, GPA. "
            "Use before making recommendations or when student asks about their profile."
        ),
        parameters={
            "type": "object",
            "properties": {
                "student_id": {
                    "type": "integer",
                    "description": "Student ID"
                }
            },
            "required": ["student_id"]
        }
    )
]

TOOLS = types.Tool(function_declarations=FUNCTION_DECLARATIONS)

def call_gemini_with_functions(
    prompt: str,
    student_id: int,
    temperature: float = 0.7
) -> Dict[str, Any]:
    """
    Call Gemini API with function calling enabled.

    Args:
        prompt: User's message/question
        student_id: ID of the student asking
        temperature: Creativity level (0.0-1.0)

    Returns:
        dict: {
            'has_function_calls': bool,
            'function_calls': list,  # [{name, args}, ...]
            'text_response': str,
            'chat_session': chat object for follow-up
        }
    """
    logger.info(f"Calling Gemini for student {student_id}")
    logger.info(f"Message: {prompt[:100]}...")

    try:
        client = get_gemini_client()

        system_instruction = f"""You are a helpful AI assistant for KBTU thesis management.
            Help students find thesis topics, supervisors, and get recommendations.

            Current student ID: {student_id}

            Guidelines:
            - Be helpful, friendly, and concise
            - Use functions to get real database data
            - For recommendations, call get_student_profile first
            - Present info clearly with lists
            - Mention skill matches when relevant"""

        chat = client.chats.create(
            model='gemini-2.5-flash',
            config=types.GenerateContentConfig(
                temperature=temperature,
                tools=[TOOLS],
                system_instruction=system_instruction
            )
        )

        response = chat.send_message(prompt)

        function_calls = []
        text_response = ""

        if response.candidates and response.candidates[0].content:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    fc = part.function_call
                    function_calls.append({
                        'name': fc.name,
                        'args': dict(fc.args) if fc.args else {}
                    })
                    logger.info(f"Function call: {fc.name} with {fc.args}")

                if hasattr(part, 'text') and part.text:
                    text_response = part.text

        logger.info(f"Response: {len(function_calls)} function calls, text: {bool(text_response)}")

        return {
            'has_function_calls': len(function_calls) > 0,
            'function_calls': function_calls,
            'text_response': text_response,
            'chat_session': chat,
            'client': client  # Keep client alive
        }

    except Exception as e:
        logger.error(f"Gemini API error: {str(e)}")
        raise

