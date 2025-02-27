
from django.contrib import admin
from .models import RecentlyData, UserChoice, UserKeyword

# RecentlyData 모델을 관리자 페이지에 등록
admin.site.register(RecentlyData)
admin.site.register(UserChoice)
admin.site.register(UserKeyword)