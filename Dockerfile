FROM python:3.12-alpine

WORKDIR /app

# Устанавливаем системные зависимости для сборки пакетов (компиляторы для SQLAlchemy)
RUN apk add --no-cache gcc musl-dev python3-dev libffi-dev openssl-dev build-base

# Копируем зависимости
COPY requirements.txt .

# Устанавливаем библиотеки Python
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь остальной код проекта
COPY . .

# Команда запуска
CMD ["python", "main.py"]
