# Aleucos 

Проект реализует функционал по загрузке данных из xlsx-файла. Загрузить данные можно, перейдя в административную панель Django и выбрав раздел Products. Там будет кнопка "Импортировать записи из XLSX".
### 1. Клонирование репозитория 
Клонируйте репозиторий на локальный компьютер:
``` 
git clone https://github.com/PakSerg/Aleucos.git
```
Перейдите в папку с проектом: 
```
cd Aleucos
```

### 2. Запуск PostgreSQL и Redis в Docker

```
docker-compose up -d --build
``` 

### 3. Создание и активация виртуального окружения

```
# Для Windows
python -m venv venv
venv\Scripts\Activate

# Для macOS/Linux
python -m venv venv
source venv/bin/activate

``` 

### 4. Установка зависимостей

```
pip install -r requirements.txt
``` 

### 5. Применение миграций

```
python manage.py migrate
``` 

### 6. Загрузка фикстур

```
python manage.py loaddata fixtures\user.json
``` 
Будет создан суперпользователь для входа в административную панель Django: 
- username = admin 
- password = admin

### 7. Запуск проекта
Запуск Celery: 
```
# Для Windows
start /B celery -A Aleucos worker -l info -P solo
``` 
Запуск Flower (если необходимо): 
``` 
# Для Windows
start /B celery -A Aleucos flower -l info   
```  
Запуск сервера на локальной машине:

```
python manage.py runserver
``` 
Административная панель будет доступна по адресу `127.0.0.1:8000/admin`, а Flower – по адресу `127.0.0.1:5555`. 
