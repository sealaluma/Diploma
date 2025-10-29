"""
Serializers for AI Chatbot API
"""

from rest_framework import serializers


class ChatRequestSerializer(serializers.Serializer):
    """
    Validates incoming chat requests.

    Fields:
        message (str): User's question/message (required, 1-2000 chars)
    """
    message = serializers.CharField(
        required=True,
        min_length=1,
        max_length=2000,
        help_text="User's question or message to the AI assistant"
    )

    def validate_message(self, value):
        """
        Validate message content.

        TODO:
            - Strip whitespace
            - Check for empty message
            - Optionally check for inappropriate content
            - Return cleaned message
        """
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Message cannot be empty")
        return value


class ChatResponseSerializer(serializers.Serializer):
    """
    Formats AI chatbot responses.

    Fields:
        message (str): AI's response text
        suggested_topics (list): Optional list of topic IDs
        suggested_supervisors (list): Optional list of supervisor IDs
    """
    message = serializers.CharField(
        help_text="AI assistant's response text"
    )
    suggested_topics = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of recommended topic IDs"
    )
    suggested_supervisors = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of recommended supervisor IDs"
    )


class ChatHistorySerializer(serializers.Serializer):
    """
    Serializer for chat history (future feature).

    TODO: Implement if we decide to store chat history in database
    """
    pass
