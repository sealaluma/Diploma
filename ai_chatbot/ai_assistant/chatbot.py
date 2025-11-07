"""
Main Chatbot Logic

Orchestrates AI chatbot with Gemini function calling:
1. Receive user message
2. Call Gemini with function calling enabled
3. Execute any function calls Gemini requests
4. Send results back to Gemini
5. Return final response
"""

import logging
from google.genai import types

from .llm_client import call_gemini_with_functions
from .tools import call_tool

logger = logging.getLogger(__name__)


def chat_with_ai(user_message: str, user_profile) -> dict:
    """
    Main entry point for AI chatbot with function calling.

    Flow:
    1. Call Gemini with user message
    2. If Gemini requests function calls, execute them
    3. Send function results back to Gemini
    4. Get final response
    5. Return formatted response

    Args:
        user_message: The user's question
        user_profile: StudentProfile instance

    Returns:
        dict: {
            'message': str,  # Final AI response
            'function_calls_made': list,  # List of functions called
            'error': str  # Error message if any
        }
    """
    logger.info(f"Chat request from: {user_profile.user.email}")
    logger.info(f"Message: {user_message}")

    try:
        student_id = user_profile.user.id

        gemini_response = call_gemini_with_functions(
            prompt=user_message,
            student_id=student_id,
            temperature=0.7
        )

        function_calls_made = []

        if gemini_response['has_function_calls']:
            logger.info(f"Gemini requested {len(gemini_response['function_calls'])} function calls")

            function_responses = []

            for fc in gemini_response['function_calls']:
                func_name = fc['name']
                func_args = fc['args']

                logger.info(f"Executing: {func_name}({func_args})")

                try:
                    result = call_tool(func_name, **func_args)

                    function_calls_made.append({
                        'name': func_name,
                        'args': func_args,
                        'result': result
                    })

                    function_responses.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=func_name,
                                response={'result': result}
                            )
                        )
                    )

                    logger.info(f"Function {func_name} returned {len(result) if isinstance(result, list) else 'data'}")

                except Exception as e:
                    logger.error(f"Error executing {func_name}: {str(e)}")
                    function_responses.append(
                        types.Part(
                            function_response=types.FunctionResponse(
                                name=func_name,
                                response={'error': str(e)}
                            )
                        )
                    )


            chat = gemini_response['chat_session']
            final_response = chat.send_message(function_responses)

            final_text = ""
            if final_response.candidates and final_response.candidates[0].content:
                for part in final_response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        final_text = part.text
                        break

            logger.info(f"Final response length: {len(final_text)}")

            return {
                'message': final_text,
                'function_calls_made': function_calls_made
            }

        else:
            logger.info("No function calls requested")
            return {
                'message': gemini_response['text_response'],
                'function_calls_made': []
            }

    except Exception as e:
        logger.error(f"Error in chat_with_ai: {str(e)}")
        return {
            'message': 'Sorry, I encountered an error processing your request.',
            'error': str(e),
            'function_calls_made': []
        }
