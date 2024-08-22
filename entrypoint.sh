#!/bin/sh

echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 0.5
done
sleep 6
echo "PostgreSQL is up!"

python manage.py migrate
python manage.py loaddata fixtures/user.json 
# python manage.py collectstatic --noinput

python manage.py runserver 0.0.0.0:8000

wait