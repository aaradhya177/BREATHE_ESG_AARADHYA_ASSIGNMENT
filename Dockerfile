FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

SHELL ["/bin/sh", "-c"]
CMD python manage.py migrate --noinput && gunicorn breathe.wsgi:application --bind 0.0.0.0:8000