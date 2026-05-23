# Software Engineer Analytics Platform

Платформа анализа рынка труда инженеров-программистов. Учебный проект по Docker и Kubernetes.

## Стек

Python 3.11, Django 5.2, PostgreSQL 15, Docker, Docker Compose, Kubernetes, Bootstrap

## Запуск

### 1. Docker Compose

```bash
git clone git@github.com:catsandogs/software_engineer_analytics.git
cd software_engineer_analytics
docker-compose up -d --build
```

Сайт: http://localhost:8000

### 2. Kubernetes

```bash
minikube start --driver=docker
docker build -t analytics-app:latest .
minikube image load analytics-app:latest
kubectl apply -f k8s/
minikube service django-service -n analytics
```

### 3. Локально

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Команды

**Docker:** `docker-compose up -d` | `docker-compose down` | `docker-compose logs -f`

**Kubernetes:** `kubectl get pods -n analytics` | `kubectl logs -n analytics -l app=django`

## Структура

```
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── k8s/
├── analytics/
├── software_engineer_analytics/
└── manage.py
```

## Админка

/admin/
