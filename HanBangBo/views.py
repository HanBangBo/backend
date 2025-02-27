import json, requests, csv
from django.http import JsonResponse, HttpRequest, HttpResponse
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
            type_value = entry.get("type_value")      # 예: "언론사" or "카테고리"
            source_value = entry.get("source_value")
            keyword = entry.get("keyword")            # 예: "탄핵"
            quiz_content = entry.get("quiz_content")    # 문제 텍스트
            correct_answer = entry.get("correct")       # 정답
            quiz_comment = entry.get("quiz_comment")      # 해설
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

            # 저장한 데이터의 정보를 결과 리스트에 추가
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


# ✅ GET 요청을 생성하는 함수
def create_get_request():
    request = HttpRequest()  # HttpRequest 객체 생성
    request.method = "GET"  # ✅ GET 요청으로 설정
    return request


# BE -> FE API
@csrf_exempt
def get_all_quiz_data(source_value):  # ✅ request 제거
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


def send_data_to_external_api(user_choice):
    url = "http://ec2-52-79-153-90.ap-northeast-2.compute.amazonaws.com:8000/generate_questions/"
    
    # UserChoice 데이터에서 필요한 필드만 추출하여 딕셔너리로 구성
    payload = {
        "type_value": user_choice.type_value,
        "source_value": user_choice.source_value,
        "period": user_choice.period,
        "userKeyword": user_choice.userKeyword,
        "source_type": user_choice.source_type  # 만약 해당 필드가 있다면
    }
    
    headers = {"Content-Type": "application/json"}
    
    try:
        # json 인수를 사용하면 payload가 자동으로 JSON으로 직렬화됨
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        return {"error": str(e)}

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
            if missing_fields:
                return JsonResponse({"error": f"Missing fields: {', '.join(missing_fields)}"}, status=400)

            # ✅ 데이터 변환
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

            # ✅ UserValue 가져오거나 없으면 생성
            user, created = UserValue.objects.get_or_create(user=user_id)

            # ✅ UserKeyword에서 source_value와 user가 같은 데이터 가져오기
            keywords = UserKeyword.objects.filter(user=user, source_value=source_value)

            # ✅ userKeyword JSON 데이터 구성 (키워드 3개 이상일 때만 저장)
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

            external_response = send_data_to_external_api(user_choice)
            print(external_response)
            receive_ai_data(external_response)

            # ✅ `get_all_quiz_data()`를 호출하여 JSON 반환
            return get_all_quiz_data(source_value)  # ✅ 함수 직접 호출

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Only POST method allowed"}, status=405)

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
                print(1)
            except UserValue.DoesNotExist:
                return JsonResponse({"error": f"User '{data['user']}' does not exist"}, status=404)
            results = []  # 처리 결과 저장
            _quiz, _correct = data['quiz_id'], data['is_correct']
            for quiz_id, is_correct in zip(_quiz, _correct):
                # ✅ RecentlyData 객체 조회 (없으면 404)
                try:
                    quiz_data = RecentlyData.objects.get(id=quiz_id)
                    print(2)
                except RecentlyData.DoesNotExist:
                    return JsonResponse({"error": f"Quiz with ID '{quiz_id}' does not exist"}, status=404)
                source_value = quiz_data.source_value
                keyword = quiz_data.keyword

                # ✅ UserKeyword에서 user + source_value + keyword 필터링
                user_keyword, created = UserKeyword.objects.get_or_create(
                    user=user,
                    source_value=source_value,
                    keyword=keyword,
                    defaults={"correct_count": 0, "incorrect_count": 0}
                    
                )
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


# @csrf_exempt
# def download_and_delete_quiz_data():
#     # CSV 파일 응답 생성
#     response = HttpResponse(content_type='text/csv')
#     response['Content-Disposition'] = 'attachment; filename="quiz_data.csv"'
    
#     writer = csv.writer(response)
#     # CSV 헤더 작성 (필요한 필드에 따라 수정)
#     writer.writerow(["id", "type_value", "source_value", "keyword", "quiz_content", "correct", "quiz_comment", "choices"])
    
#     # 데이터베이스에서 모든 RecentlyData 객체 가져오기
#     all_data = RecentlyData.objects.all()
    
#     for data in all_data:
#         # choices 필드가 리스트인 경우, 콤마로 구분하여 문자열로 변환
#         if isinstance(data.choices, list):
#             choices_str = ", ".join(data.choices)
#         else:
#             choices_str = str(data.choices)
        
#         writer.writerow([
#             data.id,
#             data.type_value,
#             data.source_value,
#             data.keyword,
#             data.quiz_content,
#             data.correct,
#             data.quiz_comment,
#             choices_str
#         ])
    
#     # CSV 파일로 데이터를 전달한 후 데이터베이스에서 해당 데이터 삭제
#     RecentlyData.objects.all().delete()
    
#     return response