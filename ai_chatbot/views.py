"""
AI Chatbot API Views

Provides REST API endpoint for AI chatbot interactions.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

from .ai_assistant.chatbot import chat_with_ai
from .serializers import ChatRequestSerializer, ChatResponseSerializer
from .throttles import AIChatbotThrottle
from .rate_limiter import require_ai_quota, get_user_quota_status
from profiles.models import StudentProfile

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@require_ai_quota('chatbot_message')
# @throttle_classes([AIChatbotThrottle])  # Disabled for testing
def ai_chat(request):
    """
    AI Chatbot endpoint for thesis project assistance.

    Request body:
    {
        "message": "I'm looking for machine learning projects"
    }

    Response:
    {
        "message": "AI response text",
        "function_calls_made": [...]  # Debug info (optional)
    }

    Authentication: JWT token required
    Rate limit: Currently disabled for testing

    Only available to students with completed profiles.
    """
    logger.info(f"AI chat request from user: {request.user.email}")

    # 1. Validate request
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Invalid request from {request.user.email}: {serializer.errors}")
        return Response(
            {"error": "Invalid request", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    message = serializer.validated_data['message']
    logger.info(f"Message: {message[:100]}...")

    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        logger.error(f"Student profile not found for user: {request.user.email}")
        return Response(
            {"error": "Student profile not found. Please complete your profile first."},
            status=status.HTTP_404_NOT_FOUND
        )

    if not request.user.is_profile_completed:
        logger.warning(f"Incomplete profile for user: {request.user.email}")
        return Response(
            {"error": "Please complete your profile before using the AI assistant."},
            status=status.HTTP_403_FORBIDDEN
        )

    # 4. Call AI chatbot
    try:
        ai_response = chat_with_ai(
            user_message=message,
            user_profile=student_profile
        )

        # 5. Format response
        response_data = {
            "message": ai_response.get('message', 'Sorry, I could not process your request.')
        }

        # Include debug info in development (optional)
        if request.query_params.get('debug') == 'true':
            response_data['function_calls_made'] = ai_response.get('function_calls_made', [])

        logger.info(f"AI response sent to {request.user.email}")
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return Response(
            {"error": "An error occurred while processing your request. Please try again later."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def chat_health_check(request):
    """
    Health check endpoint for AI chatbot service.

    Returns:
    {
        "status": "ok" | "warning" | "error",
        "message": "Status message",
        "checks": {
            "gemini_api_key": bool,
            "database": bool,
            "student_profile": bool
        }
    }
    """
    import os
    from django.db import connection

    checks = {}
    warnings = []

    # Check 1: GEMINI_API_KEY configured
    checks['gemini_api_key'] = bool(os.getenv('GEMINI_API_KEY'))
    if not checks['gemini_api_key']:
        warnings.append("GEMINI_API_KEY not configured")

    # Check 2: Database accessible
    try:
        connection.ensure_connection()
        checks['database'] = True
    except Exception as e:
        checks['database'] = False
        warnings.append(f"Database error: {str(e)}")

    # Check 3: Student profile exists
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        checks['student_profile'] = True
        checks['profile_completed'] = request.user.is_profile_completed
        if not request.user.is_profile_completed:
            warnings.append("Student profile is incomplete")
    except StudentProfile.DoesNotExist:
        checks['student_profile'] = False
        checks['profile_completed'] = False
        warnings.append("Student profile not found")

    # Determine overall status
    if all(checks.values()):
        overall_status = "ok"
        message = "AI Chatbot is fully operational"
    elif checks.get('gemini_api_key') and checks.get('database'):
        overall_status = "warning"
        message = f"AI Chatbot available with warnings: {', '.join(warnings)}"
    else:
        overall_status = "error"
        message = f"AI Chatbot not available: {', '.join(warnings)}"

    return Response({
        "status": overall_status,
        "message": message,
        "checks": checks,
        "warnings": warnings if warnings else None
    })


class AIQuotaView(APIView):
    """
    GET /api/quota/
    Returns current AI usage quota for authenticated user
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        quota_status = get_user_quota_status(request.user)

        return Response({
            'topic_enhancements': {
                'used': quota_status['topic_enhancements']['used'],
                'limit': quota_status['topic_enhancements']['limit'],
                'remaining': quota_status['topic_enhancements']['remaining'],
                'resets_at': quota_status['topic_enhancements']['resets_at'].isoformat(),
            },
            'chatbot_messages': {
                'used': quota_status['chatbot_messages']['used'],
                'limit': quota_status['chatbot_messages']['limit'],
                'remaining': quota_status['chatbot_messages']['remaining'],
                'resets_at': quota_status['chatbot_messages']['resets_at'].isoformat(),
            }
        })
