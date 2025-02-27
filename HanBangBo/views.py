import json
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from .models import RecentlyData, UserChoice, UserKeyword, UserValue
from django.views.decorators.http import require_http_methods


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
    "type_value": "주관식",
    "source_value": "경제",
    "keyword": "금리",
    "quiz_content": "문제 내용",
    "correct": "문제에 대한 정답",
    "quiz_comment": "문제에 대한 해설",
    "choices": {""
        
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



# ✅ GET 요청을 생성하는 함수
def create_get_request():
    request = HttpRequest()  # HttpRequest 객체 생성
    request.method = "GET"  # ✅ GET 요청으로 설정
    return request


# BE -> FE API
@csrf_exempt
def get_all_quiz_data(request, source_value):
    if request.method == "GET":
        try:
            # ✅ DB에서 모든 데이터를 id 기준으로 순차적으로 가져오기
            filtered_data = RecentlyData.objects.filter(source_value=source_value).order_by("id")

            # ✅ 응답 리스트 생성
            response_list = []

            for data in filtered_data:
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
            return JsonResponse({"quiz_data": response_list}, status=200, json_dumps_params={"ensure_ascii": False})


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
@require_http_methods(["POST", "OPTIONS"])  # ✅ POST & OPTIONS 요청 허용
def save_user_choice(request):
    if request.method == "POST":
        try:
            # ✅ JSON 데이터 로드
            data = json.loads(request.body.decode("utf-8"))

            # ✅ 필수 필드 확인
            required_fields = ["user", "type_value", "source_value", "period"]
            missing_fields = [field for field in required_fields if data.get(field) is None]
            if missing_fields:
                return JsonResponse({"error": f"Missing fields: {', '.join(missing_fields)}"}, status=400)

            # ✅ 데이터 변환
            user_id = data["user"]
            type_value = data["type_value"]
            source_value = data["source_value"]
            try:
                period = int(data["period"])
            except ValueError:
                return JsonResponse({"error": "Period must be an integer"}, status=400)

            # ✅ UserValue 가져오거나 없으면 생성
            user, created = UserValue.objects.get_or_create(user=user_id)

            # ✅ UserKeyword에서 source_value와 user가 같은 데이터 가져오기
            keywords = UserKeyword.objects.filter(user=user, source_value=source_value)

            # ✅ userKeyword JSON 데이터 구성 (키워드 3개 이상일 때만 저장)
            user_keyword_data = {
                kw.keyword: f"{(kw.incorrect_count / (kw.correct_count + kw.incorrect_count)) * 100:.2f}%"
                if (kw.correct_count + kw.incorrect_count) > 0 else "0.00%"
                for kw in keywords
            } if keywords.count() > 2 else {}

            # ✅ UserChoice 저장 또는 업데이트
            user_choice, created = UserChoice.objects.update_or_create(
                user=user, source_value=source_value,
                defaults={"type_value": type_value, "period": period, "userKeyword": user_keyword_data}
            )
            # ✅ GET 요청을 생성하여 `get_all_quiz_data` 호출
            get_request = HttpRequest()
            get_request.method = "GET"
            return get_all_quiz_data(get_request, source_value)  # ✅ JSON 응답 그대로 반환

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
                #required_fields = ["user", "source_value", "keyword", "is_correct"]
                required_fields = ["user", "quiz_id", "is_correct"]
                if not all(field in entry for field in required_fields):
                    return JsonResponse({"error": "Missing required fields"}, status=400)

                try:
                    # ✅ 프론트에서 받은 데이터
                    user = UserValue.objects.get(user=entry["user"])
                except UserValue.DoesNotExist:
                    return JsonResponse({"error": f"User '{entry['user']}' does not exist"}, status=404)

                quiz_data = RecentlyData.objects.get(id=entry["quiz_id"])
                source_value = quiz_data.source_value
                keyword = quiz_data.keyword
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