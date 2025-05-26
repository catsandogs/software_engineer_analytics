# Django Software Engineer Analytics Platform

## Быстрая установка

1. Создайте новый Django проект:
```bash
django-admin startproject software_engineer_analytics
cd software_engineer_analytics
```

2. Установите зависимости:
```bash
pip install django psycopg2-binary requests matplotlib pandas pillow seaborn
```

3. Создайте приложение analytics:
```bash
python manage.py startapp analytics
```

4. Скопируйте все файлы из кода ниже в соответствующие папки

5. Выполните миграции:
```bash
python manage.py makemigrations
python manage.py migrate
```

6. Создайте суперпользователя:
```bash
python manage.py createsuperuser
```

7. Запустите сервер:
```bash
python manage.py runserver
```

## Структура проекта
```
software_engineer_analytics/
├── manage.py
├── software_engineer_analytics/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── analytics/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── migrations/
    └── templates/
        └── analytics/
            ├── base.html
            ├── index.html
            ├── general_stats.html
            ├── demand.html
            ├── geography.html
            ├── skills.html
            └── latest_vacancies.html
```

## Административная панель
- URL: `/admin/`
- Управление контентом страниц
- Загрузка статистических данных
- Обработка CSV файлов с вакансиями
- Настройка сайта

## Функции платформы
- Аналитика по профессии инженер-программист
- Обработка больших CSV файлов (>1GB)
- Интеграция с HeadHunter API
- Красивый дизайн с Bootstrap
- PostgreSQL база данных