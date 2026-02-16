from django.urls import path
from .views import quiz_ai

urlpatterns = [
    path("quiz-ai/", quiz_ai),
]
