#!/bin/sh
set -e

echo "📌 데이터베이스가 준비될 때까지 대기 중..."
until mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SHOW DATABASES;" > /dev/null 2>&1; do
  echo "⏳ MySQL 연결 대기 중..."
  sleep 2
done

echo "✅ 데이터베이스 연결됨!"

echo "📌 Django 마이그레이션 실행..."
python manage.py migrate --noinput

echo "📌 정적 파일 수집..."
python manage.py collectstatic --noinput

echo "🚀 Gunicorn 서버 시작..."
exec gunicorn --bind 0.0.0.0:8000 be.wsgi:application
