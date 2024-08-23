# Aleucos 

Проект реализует функционал по загрузке данных из xlsx-файла (приложение products, файл admin.py).

## Запуск PostgreSQL в docker-compose 

```
docker-compose up --build
``` 

## Создание и активация виртуального окружения

```
python -m venv venv
venv/Scripts/Activate
``` 

## Установка зависимостей

```
pip install -r requirements.txt
``` 

## Запуск проекта

```
python manage.py runserver
``` 