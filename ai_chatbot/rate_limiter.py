from functools import wraps
from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status

from ai_chatbot.models import AIUsageWindow


def get_daily_limit(feature_type):
    """Get daily limit for a feature type from settings"""
    return settings.AI_RATE_LIMITS.get(feature_type, 0)


def get_or_create_today_window(user, feature_type):
    """Get or create today's usage window for user and feature"""
    today = timezone.now().date()
    window, created = AIUsageWindow.objects.get_or_create(
        user=user,
        feature_type=feature_type,
        date=today,
        defaults={'usage_count': 0}
    )
    return window


def check_rate_limit(user, feature_type):
    """
    Check if user has quota remaining for today.

    Args:
        user: CustomUser instance
        feature_type: str ('topic_enhancement' or 'chatbot_message')

    Returns:
        dict: {
            'allowed': bool,
            'used': int,
            'limit': int,
            'remaining': int,
            'resets_at': datetime (midnight tonight)
        }
    """
    window = get_or_create_today_window(user, feature_type)
    limit = get_daily_limit(feature_type)
    used = window.usage_count
    remaining = max(0, limit - used)
    allowed = used < limit

    # Calculate midnight tonight (when it resets)
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    midnight_tonight = timezone.make_aware(datetime.combine(tomorrow, time.min))

    return {
        'allowed': allowed,
        'used': used,
        'limit': limit,
        'remaining': remaining,
        'resets_at': midnight_tonight,
    }


def record_usage(user, feature_type):
    """
    Record AI usage by incrementing today's counter.

    Args:
        user: CustomUser instance
        feature_type: str ('topic_enhancement' or 'chatbot_message')

    Returns:
        bool: True if recorded successfully
    """
    window = get_or_create_today_window(user, feature_type)
    window.usage_count += 1
    window.save()
    return True


def get_user_quota_status(user):
    """
    Get quota status for all AI features.

    Args:
        user: CustomUser instance

    Returns:
        dict with status for each feature
    """
    return {
        'topic_enhancements': check_rate_limit(user, 'topic_enhancement'),
        'chatbot_messages': check_rate_limit(user, 'chatbot_message'),
    }


def require_ai_quota(feature_type):
    """
    Decorator to enforce daily rate limiting on views.
    Returns 429 if quota exceeded.

    Usage:
        @require_ai_quota('topic_enhancement')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            user = request.user

            # Check quota
            quota = check_rate_limit(user, feature_type)

            if not quota['allowed']:
                feature_name = feature_type.replace('_', ' ').title()
                return Response({
                    'error': 'Rate limit exceeded',
                    'detail': f"Daily limit reached ({quota['used']}/{quota['limit']} {feature_name}s used). Resets at midnight.",
                    'used': quota['used'],
                    'limit': quota['limit'],
                    'remaining': quota['remaining'],
                    'resets_at': quota['resets_at'].isoformat(),
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Record usage BEFORE executing view
            record_usage(user, feature_type)

            # Execute the actual view
            return view_func(request, *args, **kwargs)

        return wrapped_view
    return decorator
