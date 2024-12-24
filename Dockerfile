FROM python:3.11-slim

# Установить зависимости системы
RUN apt-get update && apt-get install -y gcc curl wget && apt-get clean

# Создать рабочую директорию
WORKDIR /app

# Скопировать файлы проекта
COPY . .

# Установить зависимости Python
RUN pip install --no-cache-dir -r requirements.txt

# Указать команду запуска приложения
CMD ["python", "main.py"]
