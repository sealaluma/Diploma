"""
Custom throttle classes for AI-powered endpoints.

These throttles use Redis-based rate limiting to protect expensive AI API calls
from abuse while allowing legitimate users to access the features.
"""

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
import logging

logger = logging.getLogger(__name__)


class AIEnhancementUserThrottle(UserRateThrottle):
    """
    Rate limiting for authenticated users making AI enhancement requests.

    Default: 10 requests per hour per user
    Can be configured in settings.py with REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']
    """
    scope = 'ai_enhancement_user'

    def throttle_failure(self):
        """Log throttle events for monitoring"""
        logger.warning(
            f"AI enhancement rate limit exceeded for user: "
            f"{getattr(self.request.user, 'email', 'Unknown')}"
        )
        return super().throttle_failure()


class AIEnhancementAnonThrottle(AnonRateThrottle):
    """
    Rate limiting for anonymous/unauthenticated requests to AI endpoints.

    Default: 3 requests per day per IP address
    Stricter than authenticated users to prevent abuse.
    """
    scope = 'ai_enhancement_anon'

    def throttle_failure(self):
        """Log throttle events for monitoring"""
        ip = self.get_ident()
        logger.warning(f"AI enhancement rate limit exceeded for anonymous IP: {ip}")
        return super().throttle_failure()


class AIEnhancementBurstThrottle(UserRateThrottle):
    """
    Burst rate limiting to prevent rapid successive requests.

    Default: 3 requests per minute per user
    Prevents users from spamming the AI endpoint in quick succession.
    """
    scope = 'ai_enhancement_burst'

    def throttle_failure(self):
        """Log throttle events for monitoring"""
        logger.warning(
            f"AI enhancement burst limit exceeded for user: "
            f"{getattr(self.request.user, 'email', 'Unknown')}"
        )
        return super().throttle_failure()
