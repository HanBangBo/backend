from django.urls import path
from .views import receive_ai_data  # views.py의 함수 가져오기

urlpatterns = [
    path('receive-ai-data/', receive_ai_data, name='receive_ai_data'),
]
