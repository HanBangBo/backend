from django.db import models

class RecentlyData(models.Model):
    type_value = models.TextField()
    source_value = models.CharField(max_length=255)
    keyword = models.CharField(max_length=255)
    quiz_content = models.TextField()
    correct = models.TextField()
    quiz_comment = models.TextField()
    choices = models.JSONField(default=list)  # ✅ 리스트를 JSON 형태로 저장


class UserChoice(models.Model):
    user = models.CharField(max_length=255)
    type_value = models.TextField()
    source_value = models.CharField(max_length=255)
    period = models.IntegerField()
    userKeyword = models.JSONField(default=dict)  # ✅ JSON 필드 유지 (MySQL 사용 시 default 제거)


class UserKeyword(models.Model):
    user = models.CharField(max_length=255)  # ✅ VARCHAR(255)
    source_value = models.CharField(max_length=255)  # ✅ TEXT → VARCHAR(255) 변경
    keyword = models.CharField(max_length=255)  # ✅ TEXT → VARCHAR(255) 변경
    correct_count = models.IntegerField(default=0)
    incorrect_count = models.IntegerField(default=0)

    class Meta:
        unique_together = ('user', 'source_value', 'keyword')  # ✅ 중복 방지