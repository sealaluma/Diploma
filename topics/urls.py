from django.urls import path
from .views import (
    ThesisTopicCreateView,
    ThesisTopicListView,
    ThesisTopicDetailView,
    ThesisTopicUpdateView,
    enhance_description
)

urlpatterns = [
    path('create/', ThesisTopicCreateView.as_view(), name='create-topic'),
    path('', ThesisTopicListView.as_view(), name='list-topics'),
    path('<int:pk>/', ThesisTopicDetailView.as_view(), name='topic-detail'),
    path('<int:pk>/edit/', ThesisTopicUpdateView.as_view(), name='topic-edit'),
    path('enhance-description/', enhance_description, name='enhance-description'),
]
