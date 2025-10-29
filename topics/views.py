from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response

from teams.models import Team
from .models import ThesisTopic
from .serializers import ThesisTopicSerializer
from rest_framework.exceptions import PermissionDenied
from .ai_enhancement import enhance_thesis_content, EnhancedThesisContent
from .throttles import AIEnhancementUserThrottle, AIEnhancementBurstThrottle
import logging

logger = logging.getLogger(__name__)


class ThesisTopicCreateView(generics.CreateAPIView):
    """ Allows students and supervisors to create a thesis topic. """
    queryset = ThesisTopic.objects.all()
    serializer_class = ThesisTopicSerializer
    permission_classes = [permissions.IsAuthenticated]


class ThesisTopicListView(generics.ListAPIView):
    """ Lists all thesis topics. """
    queryset = ThesisTopic.objects.all()
    serializer_class = ThesisTopicSerializer
    permission_classes = [permissions.AllowAny]


class ThesisTopicDetailView(generics.RetrieveAPIView):
    """ Retrieves a single thesis topic. """
    queryset = ThesisTopic.objects.all()
    serializer_class = ThesisTopicSerializer
    permission_classes = [permissions.AllowAny]

class ThesisTopicUpdateView(generics.RetrieveUpdateAPIView):
    queryset = ThesisTopic.objects.all()
    serializer_class = ThesisTopicSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        team = Team.objects.filter(thesis_topic=obj).first()
        # Проверка, что только owner может редактировать
        if not team or team.owner != user:
            raise PermissionDenied("You do not own this topic.")
        return obj


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([AIEnhancementUserThrottle, AIEnhancementBurstThrottle])
def enhance_description(request):
    """
    Enhance thesis topic titles and description using AI.
    
    Expected payload:
    {
        "description": "Original description text (required)",
        "title_en": "English title (optional)",
        "title_kz": "Kazakh title (optional)",
        "title_ru": "Russian title (optional)"
    }
    
    Returns:
    {
        "enhanced_title_en": "AI-enhanced English title",
        "enhanced_title_kz": "AI-enhanced Kazakh title",
        "enhanced_title_ru": "AI-enhanced Russian title",
        "enhanced_description": "AI-enhanced description"
    }
    """
    try:
        # Get all fields from request
        description = request.data.get('description', '').strip()
        title_en = request.data.get('title_en', '').strip() or None
        title_kz = request.data.get('title_kz', '').strip() or None
        title_ru = request.data.get('title_ru', '').strip() or None
        
        # Validate description (required)
        if not description:
            return Response(
                {'error': 'Description is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate description length
        if len(description) > 5000:
            return Response(
                {'error': 'Description is too long (maximum 5000 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(description) < 10:
            return Response(
                {'error': 'Description is too short (minimum 10 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate title lengths (optional fields)
        if title_en and len(title_en) > 500:
            return Response(
                {'error': 'English title is too long (maximum 500 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if title_kz and len(title_kz) > 500:
            return Response(
                {'error': 'Kazakh title is too long (maximum 500 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if title_ru and len(title_ru) > 500:
            return Response(
                {'error': 'Russian title is too long (maximum 500 characters)'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log the enhancement request
        logger.info(f"User {request.user.email} requested thesis content enhancement")
        if title_en:
            logger.info(f"With EN title: {title_en[:50]}...")
        if title_kz:
            logger.info(f"With KZ title: {title_kz[:50]}...")
        if title_ru:
            logger.info(f"With RU title: {title_ru[:50]}...")
        
        # Call AI service to enhance all content
        enhanced_content: EnhancedThesisContent = enhance_thesis_content(
            description=description,
            title_en=title_en,
            title_kz=title_kz,
            title_ru=title_ru
        )
        
        # Return all enhanced fields
        return Response(
            {
                'enhanced_title_en': enhanced_content.enhanced_title_en,
                'enhanced_title_kz': enhanced_content.enhanced_title_kz,
                'enhanced_title_ru': enhanced_content.enhanced_title_ru,
                'enhanced_description': enhanced_content.enhanced_description,
            },
            status=status.HTTP_200_OK
        )
        
    except ValueError as e:
        logger.error(f"Validation error in enhance_description: {str(e)}")
        return Response(
            {'error': str(e)},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Error in enhance_description: {str(e)}")
        return Response(
            {'error': 'Failed to enhance thesis content. Please try again later.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )