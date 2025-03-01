from django.db import models

# DB 최적화는 진행하지 못했습니다..ㅎㅎ

# 사용자 아이디 저장
class UserValue(models.Model) :
    user = models.CharField(max_length=255, unique=True) # ✅ 사용자 아이디


# AI에게 받은 문제 데이터
class RecentlyData(models.Model):
    type_value = models.CharField(max_length=255)       # ✅ 객관식 or 주관식
    source_value = models.CharField(max_length=255)     # ✅ 언론사 or 카테고리 (헤럴드경제, 한국경제, 정치, 사회 등등)
    keyword = models.CharField(max_length=255)          # ✅ 문제 생성에 사용된 키워드 (탄핵, IT 등등)
    quiz_content = models.TextField()                   # ✅ 문제 내용
    correct = models.CharField(max_length=255)          # ✅ 문제 정답
    quiz_comment = models.TextField()                   # ✅ 문제 해설
    choices = models.JSONField(default=list)            # ✅ 객관식 문제에서 선택지 4개, 리스트를 JSON 형태로 저장


# 사용자가 문제 풀이 전 선택한 옵션
class UserChoice(models.Model):
    user = models.ForeignKey(UserValue, on_delete=models.CASCADE)       # ✅ 사용자
    type_value = models.CharField(max_length=255)                       # ✅ 객관식 or 주관식
    source_value = models.CharField(max_length=255)                     # ✅ 언론사 or 카테고리 (헤럴드경제, 한국경제, 정치, 사회 등등)
    source_type = models.CharField(max_length=255)                      # ✅ 언론사인지 카테고리인지
    period = models.IntegerField()                                      # ✅ 기사 생성 기간
    userKeyword = models.JSONField(default=dict)                        # ✅ 사용자 취약 키워드, JSON 필드 유지 (MySQL 사용 시 default 제거)
    

# 사용자의 문제 풀이 결과를 저장하기 위한 테이블
class UserKeyword(models.Model):
    user = models.ForeignKey(UserValue, on_delete=models.CASCADE)       # ✅ 사용자
    source_value = models.CharField(max_length=255)                     # ✅ 언론사 or 카테고리 (헤럴드경제, 한국경제, 정치, 사회 등등)
    keyword = models.CharField(max_length=255)                          # ✅ 사용자 취약 키워드
    correct_count = models.IntegerField(default=0)                      # ✅ 정답 수
    incorrect_count = models.IntegerField(default=0)                    # ✅ 오답 수

    class Meta:
        unique_together = ('user', 'source_value', 'keyword')  # ✅ 중복 방지