**Silant** — это электронная сервисная книжка для складской техники.  
Цель проекта — полное погружение в сферу IT и получение реального опыта разработки, как в настоящей компании.


После завершения проекта вы можете включить его в портфолио — это поможет проходить собеседования.
---

Клонируй репозиторий:
   ```bash
   git clone https://github.com/TASIABEG/Silant.git
   cd Silant

Создай и активируй виртуальное окружение:

# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

Установи зависимости:

pip install -r requirements.txt

Примени миграции к базе данных:

python manage.py migrate

(Необязательно) Создай суперпользователя:

python manage.py createsuperuser

Запуск
python manage.py runserver


Проект будет доступен по адресу: http://127.0.0.1:8000/

Структура проекта

silant_core/ — основной код проекта
requirements.txt — список зависимостей
README.md — документация проекта
