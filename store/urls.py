from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/ai-size/', views.ai_size_api, name='ai_size_api'),
]
