import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import RecentlyData, UserChoice, UserKeyword, UserValue


current_value = 1
assigned_values = {}

# 유저 식별값 할당
data_user = {
    "user" : "1"
}

# 유저 생성
@csrf_exempt
def assign_user_value(request):
    if request.method == "POST":
        try:
            # ✅ 실제 요청 데이터 받기
            #data = json.loads(request.body)
            data = data_user
            user = data.get("user")  # 사용자 식별 ID

            if not user:
                return JsonResponse({"error": "User ID is required."}, status=400)

            # ✅ 데이터베이스에서 해당 사용자 값이 있는지 확인
            user_value, created = UserValue.objects.get_or_create(
                user=user,
            )

            return JsonResponse({"user_id": user_value.user}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format."}, status=400)

    return JsonResponse({"error": "Only POST method allowed."}, status=405)


# AI -> BE
data_to_be_from_ai = {
    "type_value": "객관식",
    "source_value": "한국",
    "keyword": "돈",
    "quiz_content": "문제 내용",
    "correct": "문제에 대한 정답",
    "quiz_comment": "문제에 대한 해설",
    "choices": {""
        "첫번째 선택지",
        "두번째 선택지",
        "세번째 선택지",
        "네번째 선택지",
    }
}
# AI -> BE API
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


# BE -> FE API
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

# BE -> AI
data_to_ai_from_be = {
    "user": "2",
    "type_value": "객관식",
    "source_value": "헤럴드",
    "period": 1,
    "keyword": {
    }
}
@csrf_exempt
def save_user_choice(request):
    if request.method == "POST":  # ✅ POST 요청으로 변경
        try:
            # ✅ 더미 데이터 대신 실제 request.body 사용
            #data = json.loads(request.body.decode("utf-8"))
            data = data_to_ai_from_be

            # ✅ 요청 데이터 가져오기
            user = UserValue.objects.get(user=data.get("user"))  # ❌ 여기서 값이 없으면 예외 발생
            type_value = data.get("type_value")
            source_value = data.get("source_value")
            period = data.get("period")

            # ✅ period를 int로 변환
            try:
                period = int(period)
            except (ValueError, TypeError):
                return JsonResponse({"error": "Period must be an integer"}, status=400)

            # ✅ 필수 필드 확인
            if not all([user, type_value, source_value, period is not None]):
                return JsonResponse({"error": "Missing required fields"}, status=400)

            # ✅ UserKeyword에서 source_value와 user가 같은 데이터 가져오기
            keywords = UserKeyword.objects.filter(user=user, source_value=source_value)

            # ✅ userKeyword JSON 데이터 구성 (항상 dict 형태 보장)
            user_keyword_data = {}
            for kw in keywords:
                total_attempts = kw.correct_count + kw.incorrect_count
                if total_attempts > 0:
                    incorrect_rate = (kw.incorrect_count / total_attempts) * 100
                    user_keyword_data[kw.keyword] = f"{incorrect_rate:.2f}%"
                else:
                    user_keyword_data[kw.keyword] = "0.00%"

            user = UserValue.objects.get(user=data.get("user"))

            user_choice, _ = UserChoice.objects.update_or_create(
                user=user,  # ❌ ForeignKey로 받은 UserValue 객체를 그대로 사용 → JSON 변환 불가능
                source_value=source_value,
                defaults={
                    "type_value": type_value,
                    "period": period,
                    "userKeyword": user_keyword_data  # ✅ 딕셔너리 형태로 저장
                }
            )


            return JsonResponse({
                "message": "UserChoice saved successfully",
                "type_value": user_choice.type_value,
                "source_value": user_choice.source_value,
                "period": user_choice.period,
                "userKeyword": user_choice.userKeyword  # ✅ 응답에 userKeyword 포함
            }, status=201)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)

# FE -> BE
data_to_be_from_fe = {
    "user" : "1",
    "source_value" : "한국",
    "keyword" : "돈",
    "is_correct" : False
}
@csrf_exempt
def process_quiz_result(request):
    if request.method == "POST":
        try:
            # ✅ JSON 데이터 받아오기 (POST 요청에서 request.body 사용)
            data = json.loads(request.body.decode("utf-8"))

            # ✅ data가 리스트인지 확인하고 리스트가 아니면 리스트로 변환
            if not isinstance(data, list):
                data = [data]  # 단일 객체일 경우 리스트로 변환

            results = []  # 처리 결과 저장

            for entry in data:
                # ✅ 필수 필드 확인
                required_fields = ["user", "source_value", "keyword", "is_correct"]
                if not all(field in entry for field in required_fields):
                    return JsonResponse({"error": "Missing required fields"}, status=400)

                try:
                    # ✅ 프론트에서 받은 데이터
                    user = UserValue.objects.get(user=entry["user"])
                except UserValue.DoesNotExist:
                    return JsonResponse({"error": f"User '{entry['user']}' does not exist"}, status=404)

                source_value = entry["source_value"]
                keyword = entry["keyword"]
                is_correct = entry["is_correct"]

                # ✅ UserKeyword에서 user + source_value + keyword 필터링
                user_keyword, created = UserKeyword.objects.get_or_create(
                    user=user,
                    source_value=source_value,
                    keyword=keyword,
                    defaults={"correct_count": 0, "incorrect_count": 0}
                )

                # ✅ 정답 여부에 따라 정답/오답 개수 업데이트
                if is_correct:
                    user_keyword.correct_count += 1
                else:
                    user_keyword.incorrect_count += 1

                user_keyword.save()

                # ✅ 결과 저장
                results.append({
                    "user": user.user,
                    "source_value": source_value,
                    "keyword": keyword,
                    "correct_count": user_keyword.correct_count,
                    "incorrect_count": user_keyword.incorrect_count,
                    "created": created  # 새로운 데이터 생성 여부
                })

            return JsonResponse({
                "message": "Quiz results processed successfully",
                "results": results
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)