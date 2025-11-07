"""
Throttle classes for AI Chatbot endpoint.

Reuses the same rate limiting strategy as AI enhancement endpoint
to prevent abuse of expensive AI API calls.
"""

from rest_framework.throttling import UserRateThrottle
import logging

logger = logging.getLogger(__name__)


class AIChatbotThrottle(UserRateThrottle):
    """
    Rate limiting for AI chatbot requests.

    Default: Same as AI enhancement (10/hour, 3/minute)
    Configured in settings.py REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    """
    scope = 'ai_enhancement_user'  # Reuse existing scope

    def allow_request(self, request, view):
        """Store request for logging and call parent"""
        self.request = request
        return super().allow_request(request, view)

    def throttle_failure(self):
        """Log throttle events for monitoring"""
        user_email = getattr(self.request.user, 'email', 'Unknown') if hasattr(self, 'request') else 'Unknown'
        logger.warning(f"AI chatbot rate limit exceeded for user: {user_email}")
        return super().throttle_failure()


class AIChatbotBurstThrottle(UserRateThrottle):
    """
    Burst protection for chatbot (3 requests per minute).
    """
    scope = 'ai_enhancement_burst'  # Reuse existing burst scope

    def allow_request(self, request, view):
        """Store request for logging and call parent"""
        self.request = request
        return super().allow_request(request, view)

    def throttle_failure(self):
        """Log throttle events for monitoring"""
        user_email = getattr(self.request.user, 'email', 'Unknown') if hasattr(self, 'request') else 'Unknown'
        logger.warning(f"AI chatbot burst limit exceeded for user: {user_email}")
        return super().throttle_failure()
