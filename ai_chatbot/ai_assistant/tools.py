"""
Tools for AI Chatbot - Database search functions.

These functions are called by the AI when it needs data from the database.
Can be tested independently without AI integration.

Usage in Django shell:
    from ai_chatbot.ai_assistant.tools import search_topics, search_supervisors
    results = search_topics(keywords=["machine learning"])
    print(results)
"""

from typing import List, Dict, Any, Optional
import logging

from topics.models import ThesisTopic
from profiles.models import SupervisorProfile, StudentProfile
from teams.models import Team
from django.db.models import Q

logger = logging.getLogger(__name__)


def search_topics(
    keywords: Optional[List[str]] = None,
    required_skills: Optional[List[str]] = None,
    available_only: bool = False,
    limit: int = 10
) -> List[Dict[str, Any]]:
    """
    Search for thesis topics by keywords and skills.

    Args:
        keywords: List of keywords to search in title/description
                 Example: ["machine learning", "AI", "ML"]
        required_skills: Filter by required skills
                        Example: ["Python", "TensorFlow"]
        available_only: Only return topics without teams (default: True)
        limit: Maximum number of results (default: 10)

    Returns:
        List of topic dictionaries with keys:
        - id: Topic ID
        - title: Topic title (English)
        - description: First 200 characters of description
        - required_skills: List of skill names
        - available: Boolean, True if no team assigned

    Example:
        >>> search_topics(keywords=["web", "development"], limit=5)
        [
            {
                "id": 1,
                "title": "E-commerce Platform",
                "description": "Build a full-stack web application...",
                "required_skills": ["Python", "Django", "React"],
                "available": True
            },
            ...
        ]
    """
    logger.info(f"search_topics called with keywords={keywords}, skills={required_skills}")

    queryset = ThesisTopic.objects.all()

    if available_only:
        queryset = queryset.filter(team__isnull=True)

    if keywords:
        q_objects = Q()
        for keyword in keywords:
            keyword_lower = keyword.lower()

            q_objects |= Q(title__icontains=keyword_lower)

            q_objects |= Q(description__icontains=keyword_lower)

            if hasattr(ThesisTopic, 'title_en'):
                q_objects |= Q(title_en__icontains=keyword_lower)
            if hasattr(ThesisTopic, 'title_kz'):
                q_objects |= Q(title_kz__icontains=keyword_lower)
            if hasattr(ThesisTopic, 'title_ru'):
                q_objects |= Q(title_ru__icontains=keyword_lower)

        queryset = queryset.filter(q_objects)

    if required_skills:
        for skill_name in required_skills:
            queryset = queryset.filter(
                required_skills__name__icontains=skill_name
            )

    queryset = queryset.distinct()[:limit]

    results = []
    for topic in queryset:
        skills = list(topic.required_skills.values_list('name', flat=True))

        is_available = not hasattr(topic, 'team')

        results.append({
            'id': topic.id,
            'title': topic.title,
            'description': topic.description[:200] + '...' if len(topic.description) > 200 else topic.description,
            'required_skills': skills,
            'available': is_available
        })

    logger.info(f"search_topics found {len(results)} results")
    return results


def search_supervisors(
    keywords: Optional[List[str]] = None,
    skills: Optional[List[str]] = None,
    available_only: bool = True,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Search for supervisors by research interests and skills.

    Args:
        keywords: Keywords to search in research_interests field
                 Example: ["machine learning", "computer vision"]
        skills: Skills to match with supervisor skills
               Example: ["Python", "TensorFlow"]
        available_only: Only supervisors with < 10 teams (default: True)
        limit: Maximum results (default: 5)

    Returns:
        List of supervisor dictionaries with keys:
        - id: Supervisor user ID
        - name: Full name
        - email: Email address
        - research_interests: Research areas (first 300 chars)
        - skills: List of skill names
        - current_teams: Number of current teams
        - max_teams: Maximum teams (10)
        - available: Boolean, True if can take more teams

    Example:
        >>> search_supervisors(keywords=["AI", "machine learning"])
        [
            {
                "id": 5,
                "name": "Jaylet Olivier",
                "email": "o.jaylet@kbtu.kz",
                "research_interests": "Machine learning, Data Analysis...",
                "skills": ["Python", "ML", "Computer Vision"],
                "current_teams": 3,
                "max_teams": 10,
                "available": True
            },
            ...
        ]
    """
    logger.info(f"search_supervisors called with keywords={keywords}, skills={skills}")

    queryset = SupervisorProfile.objects.all()

    if keywords:
        q_objects = Q()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            q_objects |= Q(research_interests__icontains=keyword_lower)

        queryset = queryset.filter(q_objects)

    if skills:
        for skill_name in skills:
            queryset = queryset.filter(
                skills__name__icontains=skill_name
            )

    queryset = queryset.distinct()

    results = []
    for supervisor in queryset:
        team_count = Team.objects.filter(supervisor=supervisor).count()

        is_available = team_count < 10

        if available_only and not is_available:
            continue

        supervisor_skills = list(supervisor.skills.values_list('name', flat=True))

        research = supervisor.research_interests or 'Not specified'
        if len(research) > 300:
            research = research[:300] + '...'

        first = supervisor.first_name if supervisor.first_name and supervisor.first_name != 'None' else ''
        last = supervisor.last_name if supervisor.last_name and supervisor.last_name != 'None' else ''
        full_name = f"{first} {last}".strip()

        if not full_name:
            full_name = supervisor.user.email.split('@')[0].replace('.', ' ').title()

        results.append({
            'id': supervisor.user.id,
            'name': full_name,
            'email': supervisor.user.email,
            'research_interests': research,
            'skills': supervisor_skills,
            'current_teams': team_count,
            'max_teams': 10,
            'available': is_available
        })

        if len(results) >= limit:
            break

    logger.info(f"search_supervisors found {len(results)} results")
    return results


def recommend_topics_by_skills(
    student_id: int,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Recommend topics based on student's skills using algorithmic scoring.

    Scoring algorithm:
    - Match percentage = (matching_skills / total_required_skills) * 100
    - Higher score = better match

    Args:
        student_id: Student user ID
        limit: Number of recommendations (default: 5)

    Returns:
        List of recommended topics with match scores:
        - id: Topic ID
        - title: Topic title
        - match_score: Percentage match (0-100)
        - matching_skills: Skills student has that topic needs
        - missing_skills: Skills student needs to acquire
        - required_skills: All required skills for the topic

    Example:
        >>> recommend_topics_by_skills(student_id=123, limit=3)
        [
            {
                "id": 15,
                "title": "Image Classification",
                "match_score": 75,
                "matching_skills": ["Python", "TensorFlow"],
                "missing_skills": ["Computer Vision"],
                "required_skills": ["Python", "TensorFlow", "Computer Vision"]
            },
            ...
        ]
    """
    logger.info(f"recommend_topics_by_skills called for student_id={student_id}")

    try:
        student = StudentProfile.objects.get(user_id=student_id)
    except StudentProfile.DoesNotExist:
        logger.error(f"Student {student_id} not found")
        return []

    student_skills = set(student.skills.values_list('name', flat=True))

    if not student_skills:
        logger.warning(f"Student {student_id} has no skills in profile")
        return []

    # Get all topics (not just available ones)
    # Students benefit from seeing what topics match their skills,
    # even if currently taken - useful for inspiration and planning
    topics = ThesisTopic.objects.all()

    scored_topics = []
    for topic in topics:
        required_skills = set(topic.required_skills.values_list('name', flat=True))

        if not required_skills:
            continue

        # Calculate matching and missing skills
        matching_skills = student_skills & required_skills
        missing_skills = required_skills - student_skills

        match_ratio = len(matching_skills) / len(required_skills)
        score = int(match_ratio * 100)

        if score > 0:
            # Check if topic is available
            is_available = not hasattr(topic, 'team')

            scored_topics.append({
                'id': topic.id,
                'title': topic.title,
                'match_score': score,
                'matching_skills': sorted(list(matching_skills)),
                'missing_skills': sorted(list(missing_skills)),
                'required_skills': sorted(list(required_skills)),
                'available': is_available
            })

    # Sort by score (highest first)
    scored_topics.sort(key=lambda x: x['match_score'], reverse=True)

    logger.info(f"recommend_topics_by_skills found {len(scored_topics)} matches")

    # Return top N
    return scored_topics[:limit]


def get_student_profile(student_id: int) -> Dict[str, Any]:
    """
    Get student profile information.

    Args:
        student_id: Student user ID

    Returns:
        Dictionary with student info:
        - name: Full name
        - email: Email address
        - skills: List of skill names
        - specialization: Major/specialization
        - gpa: GPA (if available)

    Example:
        >>> get_student_profile(student_id=123)
        {
            "name": "John Doe",
            "email": "john.doe@kbtu.kz",
            "skills": ["Python", "JavaScript", "React"],
            "specialization": "Computer Systems and Software",
            "gpa": 3.8
        }
    """
    logger.info(f"get_student_profile called for student_id={student_id}")

    try:
        student = StudentProfile.objects.get(user_id=student_id)

        skills = list(student.skills.values_list('name', flat=True))

        # Format name - handle None/empty names
        first = student.first_name if student.first_name and student.first_name != 'None' else ''
        last = student.last_name if student.last_name and student.last_name != 'None' else ''
        full_name = f"{first} {last}".strip()

        # If no valid name, use email username
        if not full_name:
            full_name = student.user.email.split('@')[0].replace('.', ' ').title()

        return {
            'name': full_name,
            'email': student.user.email,
            'skills': skills,
            'specialization': student.specialization or 'Not specified',
            'gpa': student.gpa
        }

    except StudentProfile.DoesNotExist:
        logger.error(f"Student {student_id} not found")
        return {
            'error': f'Student with ID {student_id} not found'
        }


# Tool registry for easy access by name
AVAILABLE_TOOLS = {
    'search_topics': search_topics,
    'search_supervisors': search_supervisors,
    'recommend_topics_by_skills': recommend_topics_by_skills,
    'get_student_profile': get_student_profile,
}


def call_tool(tool_name: str, **kwargs) -> Any:
    """
    Helper function to call a tool by name.

    Args:
        tool_name: Name of the tool to call
        **kwargs: Arguments to pass to the tool

    Returns:
        Tool result

    Raises:
        ValueError: If tool not found

    Example:
        >>> call_tool('search_topics', keywords=['AI'], limit=3)
        [...]
    """
    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Tool '{tool_name}' not found. Available: {list(AVAILABLE_TOOLS.keys())}")

    tool_function = AVAILABLE_TOOLS[tool_name]
    return tool_function(**kwargs)
