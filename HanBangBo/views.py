from django.shortcuts import render
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import RecentlyData

# AI -> BE
data_to_be_from_ai = {
    "type_value": "객관식 or 주관식",
    "source_value": "언론사 or 카테고리",
    "keyword": "탄핵",
    "quiz_content": "문제입니다~~",
    "correct": "문제에 대한 정답",
    "quiz_comment": "문제에 대한 해설",
    "choices": {
        "choice1": "첫번째 선택지",
        "choice2": "두번째 선택지",
        "choice3": "세번째 선택지",
        "choice4": "네번째 선택지",
    }
}


@csrf_exempt  # 🔥 CSRF 보호 비활성화 (운영 환경에서는 보안 고려 필요)
def receive_ai_data(request):
    if request.method == "GET":
        try:
            # 1️⃣ 요청된 JSON 데이터 파싱
            #data = json.loads(request.body.decode("utf-8"))
            data = data_to_be_from_ai

            # 2️⃣ JSON 데이터에서 개별 변수 추출
            type_value = data.get("type_value")  # 예: "언론사" or "카테고리"
            source_value = data.get("source_value")
            keyword = data.get("keyword")  # 예: "탄핵"
            quiz_content = data.get("quiz_content")  # 문제 텍스트
            correct_answer = data.get("correct")  # 정답
            quiz_comment = data.get("quiz_comment") # 해설
            choices = data.get("choices", [])  # 선택지 리스트

            # 3️⃣ 필수 필드 확인
            if not all([type_value, keyword, quiz_content, correct_answer, quiz_comment, choices]):
                return JsonResponse({"status": "error", "message": "Missing required fields"}, status=400)

            # 4️⃣ 데이터 저장 (중복 허용)
            recently_data = RecentlyData.objects.create(
                type_value=type_value,
                source_value=source_value,
                keyword=keyword,
                quiz_content=quiz_content,
                correct=correct_answer,
                quiz_comment=quiz_comment,
                choices=choices
            )

            # 5️⃣ 성공 응답 반환
            return JsonResponse({
                "status": "success",
                "message": "Data stored successfully",
                "data": {
                    "id": recently_data.id,
                    "type_value": recently_data.type_value,
                    "source_value": recently_data.source_value,
                    "keyword": recently_data.keyword,
                    "quiz_content": recently_data.quiz_content,
                    "correct": recently_data.correct,
                    "quiz_comment": recently_data.quiz_comment,
                    "choices": recently_data.choices
                }
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)

    return JsonResponse({"status": "error", "message": "Only POST method allowed"}, status=405)

# BE -> FE
data_to_fe_from_be = {
    "quiz_id": "퀴즈 식별자",
    "quiz": "문제입니다",
    "correct": "문제에 대한 정답",
    "options_quiz": {
        "choice1": "첫번째 선택지",
        "choice2": "두번째 선택지",
        "choice3": "세번째 선택지",
        "choice4": "네번째 선택지",
    }
}

# FE -> BE
data_to_be_from_fe = {
    "user_id": "사용자 난수",
    "quiz_id": "문제 식별(틀린 문제 식별)"
}

# BE -> AI
data_to_ai_from_be = {
    "type": "언론사 or 카테고리",
    "keyword": "많이 틀린 키워드",
    "date": "클라이언트가 선택한 날짜"
}