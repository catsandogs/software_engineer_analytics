Вот исправленный README файл с точными командами и правильной структурой:

```markdown
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
# Остановка старых Docker-контейнеров (если были запущены)
docker stop software_engineer_analytics-web-1 software_engineer_analytics-db-1

# Установка Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube && rm minikube-linux-amd64

# Установка kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl && rm kubectl

# Запуск кластера и сборка проекта
cd ~/software_engineer_analytics
minikube start --driver=docker --force
docker build -t analytics-app:latest .
minikube image load analytics-app:latest

# Развертывание в Kubernetes
cd k8s
kubectl apply -f namespace.yaml
kubectl apply -f django-deployment.yaml
kubectl apply -f django-service.yaml

# Применение миграций базы данных (замените имя пода на актуальное)
kubectl get pods -n analytics  # Получить имя пода
kubectl exec -it <имя-пода> -n analytics -- python manage.py migrate

# Создание суперпользователя (опционально)
kubectl exec -it <имя-пода> -n analytics -- python manage.py createsuperuser

# Проброс портов для доступа к сайту
kubectl port-forward -n analytics service/django-service 8000:8000
```

Сайт: http://localhost:8000

### 3. Локально

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Команды

**Docker:** 
```bash
docker-compose up -d    # Запуск
docker-compose down     # Остановка
docker-compose logs -f  # Логи
```

**Kubernetes:** 
```bash
kubectl get pods -n analytics                              # Список подов
kubectl logs -n analytics -l app=django                    # Логи Django
kubectl logs -n analytics <имя-пода>                       # Логи конкретного пода
kubectl exec -it <имя-пода> -n analytics -- python manage.py migrate     # Миграции
kubectl exec -it <имя-пода> -n analytics -- python manage.py createsuperuser  # Админ
kubectl port-forward -n analytics service/django-service 8000:8000       # Доступ
kubectl delete -f k8s/                                     # Удаление всех ресурсов
```

**Minikube:**
```bash
minikube start --driver=docker    # Запуск кластера
minikube stop                     # Остановка кластера
minikube delete                   # Удаление кластера
minikube service django-service -n analytics  # Открыть в браузере
```

## Структура

```
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── k8s/
│   ├── namespace.yaml
│   ├── django-deployment.yaml
│   └── django-service.yaml
├── analytics/
├── software_engineer_analytics/
└── manage.py
```

## Админка

/admin/

## Примечания

- При использовании Kubernetes замените `<имя-пода>` на актуальное, полученное через `kubectl get pods -n analytics`
- Для production-окружения рекомендуется использовать Ingress вместо port-forward
- PostgreSQL в Kubernetes настраивается отдельно через манифесты в `k8s/`
```

Основные исправления:
1. Добавлены реальные URL для скачивания Minikube и kubectl
2. Добавлены команды для проброса портов и создания суперпользователя
3. Расширен раздел команд Kubernetes
4. Добавлены примечания по использованию
5. Актуализирована структура с файлами из k8s/
