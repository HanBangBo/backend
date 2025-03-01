import json, requests
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from .models import RecentlyData, UserChoice, UserKeyword, UserValue
from django.views.decorators.http import require_http_methods

# AI -> BE API
@csrf_exempt
def receive_ai_data(external_response):
    try:
        # external_response가 이미 파싱된 JSON 객체(딕셔너리 또는 리스트)라고 가정
        data = external_response

        # 만약 단일 객체라면 리스트로 변환
        if not isinstance(data, list):
            data = [data]

        stored_entries = []  # 저장된 데이터 결과를 담을 리스트

        for entry in data:
            # JSON 데이터에서 개별 변수 추출
            type_value = entry.get("type_value")        # 예: "객관식" or "주관식"
            source_value = entry.get("source_value")    # 예: "언론사" or "카테고리"
            keyword = entry.get("keyword")              # 예: "탄핵"
            quiz_content = entry.get("quiz_content")    # 문제 텍스트
            correct_answer = entry.get("correct")       # 정답
            quiz_comment = entry.get("quiz_comment")    # 해설
            choices = entry.get("choices", [])          # 선택지 리스트

            # choices가 set이면 list로 변환 (JSON 직렬화 오류 방지)
            if isinstance(choices, set):
                choices = list(choices)

            # 필수 필드 확인 (모든 필드가 존재해야 함)
            if not all([type_value, keyword, quiz_content, correct_answer, quiz_comment, choices]):
                return JsonResponse(
                    {"status": "error", "message": "Missing required fields in one or more entries"},
                    status=400
                )

            # RecentlyData 테이블에 저장 (중복 허용)
            recently_data = RecentlyData.objects.create(
                type_value=type_value, 
                source_value=source_value,
                keyword=keyword,
                quiz_content=quiz_content,
                correct=correct_answer,
                quiz_comment=quiz_comment,
                choices=choices
            )

            # 저장한 데이터의 정보를 결과 리스트에 추가, 콘솔로 확인하기 위해
            stored_entries.append({
                "id": recently_data.id,
                "type_value": recently_data.type_value,
                "source_value": recently_data.source_value,
                "keyword": recently_data.keyword,
                "quiz_content": recently_data.quiz_content,
                "correct": recently_data.correct,
                "quiz_comment": recently_data.quiz_comment,
                "choices": recently_data.choices
            })

        # 모든 데이터 저장 후 성공 응답 반환
        return JsonResponse({
            "status": "success",
            "message": "Data stored successfully",
            "data": stored_entries
        }, status=201, json_dumps_params={"ensure_ascii": False})

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON format"}, status=400)


# ✅ GET 요청을 생성하는 함수, 사용자에게 문제 풀이를 위한 선택지를 받고 ai에게 함수를 호출했을 때 get 요청을 위함
def create_get_request():
    request = HttpRequest()  # HttpRequest 객체 생성
    request.method = "GET"  # ✅ GET 요청으로 설정
    return request


# BE -> FE API
# ✅ AI에게 받은 문제 중 문제 풀이에 필요한 데이터를 FE에게 전달
@csrf_exempt
def get_all_quiz_data(source_value):  # ✅ request 제거
    try:
        # ✅ DB에서 모든 데이터를 source_value(ex. 헤럴드경제) 기준으로 순차적으로 가져오기
        filtered_data = RecentlyData.objects.filter(source_value=source_value).order_by("id")

        # ✅ 응답 리스트 생성
        response_list = []

        for data in filtered_data:
            # 클라이언트에게 전달한 문제 1개
            response_data = {
                "id": data.id,  # ✅ 식별자 포함
                "quiz_content": data.quiz_content,
                "correct": data.correct,
                "quiz_comment": data.quiz_comment,
            }

            # ✅ choices가 2개 이상이면 포함, 1개 이하이면 제외 -> 객관식, 주관식을 판단
            if len(data.choices) > 1:
                response_data["choices"] = data.choices

            # 문제가 저장된 리스트(10개)
            response_list.append(response_data)

        # ✅ 최종 JSON 응답 반환
        return JsonResponse({"quiz_data": response_list}, status=200, json_dumps_params={"ensure_ascii": False})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

# BE -> AI
# ✅ 사용자에게 받은 데이터를 AI에게 전달
def send_data_to_external_api(user_choice):
    url = "#"
    
    # UserChoice 데이터에서 필요한 필드만 추출하여 딕셔너리로 구성
    payload = {
        "type_value": user_choice.type_value,       # 객관식 or 주관식
        "source_value": user_choice.source_value,   # ex. 헤럴드경제
        "period": user_choice.period,               # 문제 풀이에 필요한 기사의 작성 기간
        "userKeyword": user_choice.userKeyword,     # 사용자 취약점
        "source_type": user_choice.source_type      # 만약 해당 필드가 있다면
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        # json 인수를 사용하면 payload가 자동으로 JSON으로 직렬화됨
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}



# FE <-> BE
# 사용자가 문제 풀이의 형식, 종류를 받고 해당 문제를 전달하는 일련의 과정
@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])  # ✅ POST & OPTIONS 요청 허용
def save_user_choice(request):

    if request.method == "POST":
        try:
            # ✅ JSON 데이터 로드
            data = json.loads(request.body.decode("utf-8"))

            company = ["헤럴드경제", "한국경제"]
            category = ["정치", "경제", "사회", "국제", "문화", "과학"]


            # ✅ 필수 필드 확인
            required_fields = ["user", "type_value", "source_value", "period"]
            missing_fields = [field for field in required_fields if data.get(field) is None]

            # 필수 데이터 중 전달되지 않은 데이터가 있다면
            if missing_fields:
                return JsonResponse({"error": f"Missing fields: {', '.join(missing_fields)}"}, status=400)

            # ✅ 데이터 변환, 사용자가 전달한 데이터
            user_id = data["user"]
            type_value = data["type_value"]
            source_value = data["source_value"]

            if source_value in company:
                source_type = "언론사"
            elif source_value in category:
                source_type = "카테고리"

            try:
                period = int(data["period"])
            except ValueError:
                return JsonResponse({"error": "Period must be an integer"}, status=400)

            # ✅ 해당 사용자가 UserValue에 존재하면 가져오거나 없으면 생성
            user, created = UserValue.objects.get_or_create(user=user_id)

            # ✅ UserKeyword에서 source_value와 user가 같은 데이터 가져오기
            keywords = UserKeyword.objects.filter(user=user, source_value=source_value)

            # ✅ userKeyword(사용자 취약점) JSON 데이터 구성, 오답률 측정
            user_keyword_data = {
                kw.keyword: f"{(kw.incorrect_count / (kw.correct_count + kw.incorrect_count)) * 100:.2f}%"
                if (kw.correct_count + kw.incorrect_count) > 0 else "0.00%"
                for kw in keywords
            } 


            # ✅ UserChoice 저장 또는 업데이트
            user_choice, created = UserChoice.objects.update_or_create(
                user=user, source_value=source_value,
                defaults={"type_value": type_value, "period": period, "userKeyword": user_keyword_data, "source_type": source_type}
            )

            # ✅ AI에게 데이터 전달
            external_response = send_data_to_external_api(user_choice)
            # ✅ 생성된 문제 수신
            receive_ai_data(external_response)

            # ✅ `get_all_quiz_data()`를 호출하여 문제 데이터 JSON 반환
            return get_all_quiz_data(source_value) 

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)



# FE -> BE
# ✅ 문제 채점
@csrf_exempt
def process_quiz_result(request):

    if request.method == "POST":
        try:
            # ✅ JSON 데이터 받아오기
            data = json.loads(request.body.decode("utf-8"))

            # ✅ 필수 필드 확인
            required_fields = ["user", "quiz_id", "is_correct"]

            if not all(field in data for field in required_fields):
                return JsonResponse({"error": "Missing required fields"}, status=400)
                
            # ✅ UserValue 객체 조회 (없으면 404)
            try:
                user = UserValue.objects.get(user=data["user"])
            except UserValue.DoesNotExist:
                return JsonResponse({"error": f"User '{data['user']}' does not exist"}, status=404)
            
            results = []  # 처리 결과 저장
            _quiz, _correct = data['quiz_id'], data['is_correct']

            for quiz_id, is_correct in zip(_quiz, _correct):

                # ✅ RecentlyData 객체 조회 (없으면 404)
                try:
                    quiz_data = RecentlyData.objects.get(id=quiz_id)
                except RecentlyData.DoesNotExist:
                    return JsonResponse({"error": f"Quiz with ID '{quiz_id}' does not exist"}, status=404)
                
                
                source_value = quiz_data.source_value
                keyword = quiz_data.keyword


                # ✅ UserKeyword에서 user + source_value + keyword 필터링
                # ✅ 채점하는 문제의 유형을 이미 사용자가 풀었던 경험이 있으면 기존 데이터를 가져오고 아니면 새로 생성
                user_keyword, created = UserKeyword.objects.get_or_create(
                    user=user,
                    source_value=source_value,
                    keyword=keyword,
                    defaults={"correct_count": 0, "incorrect_count": 0}
                    
                )

                # ✅ 문제 정답 여부
                correct_result = True if is_correct[0] == "True" else False

                # ✅ 정답 여부에 따라 정답/오답 개수 업데이트
                if correct_result:
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
                    "incorrect_count": user_keyword.incorrect_count
                })

                
            RecentlyData.objects.all().delete()
            return JsonResponse({
                "message": "Quiz results processed successfully",
                "results": results
            }, status=200)


        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)
