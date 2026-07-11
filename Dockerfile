# Используем легковесный образ Python на базе Alpine Linux
FROM python:3.12-alpine

# Устанавливаем системные зависимости, необходимые для сборки некоторых Python-пакетов
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости прямо в систему контейнера (виртуальное окружение внутри Docker не требуется)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта в контейнер
COPY . .

# Команда для запуска бота при старте контейнера
CMD ["python", "main.py"]
