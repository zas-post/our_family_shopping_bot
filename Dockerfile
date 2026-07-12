# Используем легковесный образ Python на базе Alpine Linux
FROM python:3.12-alpine

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости (флаг --no-cache-dir экономит место)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все остальные файлы проекта в контейнер
COPY . .

# Команда для запуска бота при старте контейнера
CMD ["python", "main.py"]
