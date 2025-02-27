# 1. Python 3.13.2 공식 이미지 사용
FROM python:3.13.2

# 2. 컨테이너 내에서 작업 디렉토리 설정
WORKDIR /app

# 3. 시스템 패키지 업데이트 & MySQL 클라이언트 설치
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# 4. 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 프로젝트 코드 전체 복사
COPY . .

# 6. Entrypoint 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 7. 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=be.settings

# 8. Entrypoint 실행
ENTRYPOINT ["/entrypoint.sh"]
