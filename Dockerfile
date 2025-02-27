# Python 3.13.2 공식 이미지 사용
FROM python:3.13.2

# 컨테이너 내에서 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 & MySQL 클라이언트 설치
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 코드 전체 복사
COPY . .

# 환경 변수 설정 (MySQL 연결 정보 설정 가능)
ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE be.settings  # ⚠️ settings.py 경로 확인 필요!

# Django 마이그레이션 & Gunicorn 실행
CMD ["sh", "-c", "python manage.py migrate && gunicorn --bind 0.0.0.0:8000 be.wsgi:application"]
