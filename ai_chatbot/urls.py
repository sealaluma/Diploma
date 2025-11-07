"""
URL Configuration for AI Chatbot
"""

from django.urls import path
from . import views

urlpatterns = [
    path('chat/', views.ai_chat, name='ai-chat'),
    path('health/', views.chat_health_check, name='ai-chat-health'),
    path('quota/', views.AIQuotaView.as_view(), name='ai-quota'),
]
