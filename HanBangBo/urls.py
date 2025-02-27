from django.urls import path
from .views import *

urlpatterns = [
    path('receive_ai_data/', receive_ai_data, name='receive_ai_data'),
    path('save_user_choice/', save_user_choice, name='save_user_choice'),
    path('get_all_quiz_data/', get_all_quiz_data, name='get_all_quiz_data'),
    path('process_quiz_result/', process_quiz_result, name='process_quiz_result'),
    path("assign_user_value/", assign_user_value, name="assign_user_value"),

]
