from django.db import models


class RecentlyData(models.Model):
    type_value = models.TextField()
    source_value = models.TextField()
    keyword = models.TextField()
    quiz_content = models.TextField()
    correct = models.TextField()
    quiz_comment = models.TextField()
    choices = models.JSONField(default=list)  # 리스트를 JSON 형태로 저장


#class UserResult(models.Model) :



# BE -> FE
# 

# 사용자 id (난수)
# 언론사
# 카테고리(정치, 경제 등등)
# 키워드
# 문제 수
# 오답 수
# 해설
