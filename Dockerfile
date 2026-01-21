FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .
COPY setup.py .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/
COPY run_bot.py .

# Создаем необходимые директории
RUN mkdir -p logs downloads temp

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Открываем порт (если понадобится для health check)
EXPOSE 8080

# Команда запуска
CMD ["python", "run_bot.py"]
