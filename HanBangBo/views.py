from django.shortcuts import render
import json
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import RecentlyData, UserChoice, UserKeyword


# AI -> BE
data_to_be_from_ai = {
    "type_value": "객관식 or 주관식",
    "source_value": "언론사 or 카테고리",
    "keyword": "탄핵",
    "quiz_content": "문제입니다~~",
    "correct": "문제에 대한 정답",
    "quiz_comment": "문제에 대한 해설",
    "choices": {
        "첫번째 선택지",
        "두번째 선택지",
        "세번째 선택지",
        "네번째 선택지",
    }
}
# BE -> AI
data_to_ai_from_be = {
    "type": "언론사 or 카테고리",
    "keyword": "많이 틀린 키워드",
    "date": "클라이언트가 선택한 날짜"
}
# FE -> BE
data_to_be_from_fe = {
    "type_value" : "객관식",
    "source_value" : "한국",
    "period" : 1,
    "keyword" : "탄핵"

}
# FE -> BE
data_to_be_from_fe2 = {
    "user_id" : "유저입니다",
    "source_value" : "한국",
    "keyword" : "탄핵",
    "is_correct" : True
}
# BE -> FE
data_to_fe_from_be = {
    "quiz_id": "퀴즈 식별자",
    "quiz": "문제입니다",
    "correct": "문제에 대한 정답",
    "quiz_comment": "문제에 대한 해설",
    "options_quiz": {
        "첫번째 선택지",
        "두번째 선택지",
        "세번째 선택지",
        "네번째 선택지",
    }
}
@csrf_exempt  # 🔥 CSRF 보호 비활성화 (운영 환경에서는 보안 고려 필요)
def receive_ai_data(request):
    if request.method == "POST":
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

            # ✅ choices가 set이면 list로 변환 (JSON 직렬화 오류 방지)
            if isinstance(choices, set):
                choices = list(choices)

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


@csrf_exempt
def save_user_choice(request):
    if request.method == "POST":  # ✅ POST 요청으로 변경
        try:
            # ✅ request.body에서 데이터를 받아오기
            data = json.loads(request.body.decode("utf-8"))

            # ✅ 요청 데이터 가져오기
            type_value = data.get("type_value")
            source_value = data.get("source_value")
            period = data.get("period")

            # ✅ period를 int로 변환
            try:
                period = int(period)
            except (ValueError, TypeError):
                return JsonResponse({"error": "Period must be an integer"}, status=400)

            # ✅ 필수 필드 확인
            if not all([type_value, source_value, period is not None]):
                return JsonResponse({"error": "Missing required fields (type_value, source_value, period)"}, status=400)

            # ✅ UserKeyword에서 source_value가 같은 데이터 가져오기
            keywords = UserKeyword.objects.filter(source_value=source_value)

            # ✅ userKeyword JSON 데이터 구성 (항상 dict 형태 보장)
            user_keyword_data = {}
            for kw in keywords:
                total_attempts = kw.correct_count + kw.incorrect_count
                if total_attempts > 0:
                    incorrect_weight = (kw.incorrect_count / total_attempts) * 100
                    user_keyword_data[kw.keyword] = f"{incorrect_weight:.2f}%"
                else:
                    user_keyword_data[kw.keyword] = "0.00%"

            # ✅ dict인지 확인 후 저장 (set을 방지)
            if not isinstance(user_keyword_data, dict):
                return JsonResponse({"error": "userKeyword must be a dictionary"}, status=400)

            # ✅ UserChoice 저장
            user_choice = UserChoice.objects.create(
                type_value=type_value,
                source_value=source_value,
                period=period,
                userKeyword=user_keyword_data  # ✅ dict로 저장됨
            )

            return JsonResponse({
                "message": "UserChoice saved successfully",
                "id": user_choice.id,
                "userKeyword": user_choice.userKeyword  # ✅ 응답에 userKeyword 포함
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)


@csrf_exempt
def get_all_quiz_data(request):
    if request.method == "GET":
        try:
            # ✅ DB에서 모든 데이터를 id 기준으로 순차적으로 가져오기
            all_data = RecentlyData.objects.order_by("id")

            # ✅ 응답 리스트 생성
            response_list = []

            for data in all_data:
                # 기본 데이터 추가 (식별자 포함)
                response_data = {
                    "id": data.id,  # ✅ 식별자 포함
                    "quiz_content": data.quiz_content,
                    "correct": data.correct,
                    "quiz_comment": data.quiz_comment,
                }

                # ✅ choices가 2개 이상이면 포함, 1개 이하이면 제외
                if len(data.choices) > 1:
                    response_data["choices"] = data.choices

                response_list.append(response_data)

            # ✅ 최종 JSON 응답 반환
            return JsonResponse({"quiz_data": response_list}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only GET method allowed"}, status=405)

@csrf_exempt
def process_quiz_result(request):
    if request.method == "POST":
        try:
            # ✅ JSON 데이터 받아오기
            #data = json.loads(request.body.decode("utf-8"))
            data = data_to_be_from_fe2

            # ✅ 프론트에서 받은 데이터
            user_id = data.get("user_id")  # 사용자 식별자
            source_value = data.get("source_value")  # 출처 정보
            keyword = data.get("keyword")  # 키워드
            is_correct = data.get("is_correct")  # 정답 여부 (True/False)

            if not all([user_id, source_value, keyword, is_correct is not None]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # ✅ 1단계: user_id로 필터링
            user_keywords = UserKeyword.objects.filter(user=user_id)

            # ✅ 2단계: source_value로 필터링
            user_keywords = user_keywords.filter(source_value=source_value)

            # ✅ 3단계: keyword로 필터링 (최종적으로 1개의 데이터 선택)
            user_keyword, created = UserKeyword.objects.get_or_create(
                user=user_id,  # ✅ 기존 user_id에서 user로 변경
                source_value=source_value,
                keyword=keyword,
                defaults={"correct_count": 0, "incorrect_count": 0}
            )


            # ✅ 4단계: 정답 여부에 따라 정답/오답 개수 업데이트
            if is_correct:
                user_keyword.correct_count += 1
            else:
                user_keyword.incorrect_count += 1

            user_keyword.save()

            # ✅ 5단계: 해당 source_value의 모든 사용자 데이터를 가져와 오답률 계산
            keywords = UserKeyword.objects.filter(user=user_id, source_value=source_value)

            user_keyword_data = {}
            for kw in keywords:
                total_attempts = kw.correct_count + kw.incorrect_count
                if total_attempts > 0:
                    incorrect_rate = (kw.incorrect_count / total_attempts) * 100
                    user_keyword_data[kw.keyword] = f"{incorrect_rate:.2f}%"
                else:
                    user_keyword_data[kw.keyword] = "0.00%"

            # # ✅ 6단계: UserChoice 업데이트 또는 생성 (source_value 기준)
            # user_choice, _ = UserChoice.objects.update_or_create(
            #     source_value=source_value,
            #     defaults={"userKeyword": user_keyword_data}
            # )

            return JsonResponse({
                "message": "Quiz result processed successfully",
                #"userKeyword": user_choice.userKeyword
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)
