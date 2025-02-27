FROM python:3.9

# Python이 .pyc 파일을 생성하지 않고 버퍼링 없이 실행되도록 설정
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# MySQL 클라이언트 라이브러리와 기타 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    netcat-openbsd \
    gcc \
    default-libmysqlclient-dev

# 의존성 파일 복사 후 설치 (requirements.txt에 Django==5.1.6 포함)
COPY requirements.txt /app/
#RUN pip install --upgrade pip && pip install --pre -r requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# 프로젝트 전체 복사
COPY . /app/

# entrypoint 스크립트에 실행 권한 부여
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

# 컨테이너 실행 시 entrypoint.sh 실행
ENTRYPOINT ["/app/entrypoint.sh"]
