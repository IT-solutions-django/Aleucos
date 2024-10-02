#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.5
done
sleep 10
echo "PostgreSQL is up!"

echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 0.5
done
echo "Redis is up!"

echo "Waiting for Elasticsearch..."
while ! nc -z elasticsearch 9200; do
  sleep 0.5
done
echo "Elasticsearch is up!"

python manage.py migrate
python manage.py loaddata products/fixtures/category.json 
python manage.py collectstatic --noinput

python manage.py search_index --rebuild -f

celery -A Aleucos worker -l info -P prefork  &
celery -A Aleucos flower -l info &
gunicorn Aleucos.wsgi:application --bind 0.0.0.0:8000 &

wait