#!/bin/sh
set -e

echo "Waiting for MySQL to be ready..."
# 환경변수(SQL_HOST, SQL_PORT)를 통해 DB 준비 여부를 확인
while ! nc -z $SQL_HOST $SQL_PORT; do
  sleep 1
done
echo "MySQL is up!"

# 마이그레이션과 정적 파일 수집 후 Gunicorn으로 Django 실행
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn be.wsgi:application --bind 0.0.0.0:8000