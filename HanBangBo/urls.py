from django.urls import path
from .views import *

urlpatterns = [
    path('ai/data/', receive_ai_data, name='receive_ai_data'),  # ✅ AI가 데이터를 보낼 엔드포인트
    path('user/choice/', save_user_choice, name='save_user_choice'),  # ✅ 사용자의 선택 저장
    path('quiz/', get_all_quiz_data, name='get_all_quiz_data'),  # ✅ 모든 퀴즈 데이터를 가져옴
    path('quiz/result/', process_quiz_result, name='process_quiz_result'),  # ✅ 퀴즈 결과 처리

]
