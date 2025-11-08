#!/bin/bash
set -e

echo ">>> Starting entrypoint for Django web/worker"

echo "Waiting for PostgreSQL..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  sleep 1
done
echo "PostgreSQL is ready!"

echo "⚙ Running migrations..."
python manage.py migrate --noinput

if [ "$DEBUG" = "True" ] || [ "$CELERY_WORKER" != "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput --clear
fi

if [ "$CELERY_WORKER" = "true" ]; then
  echo "Starting Celery worker..."
  exec celery -A django_landing_backend worker --loglevel=info -P gevent
else
  echo "Starting Gunicorn..."
  exec gunicorn django_landing_backend.wsgi:application --bind 0.0.0.0:8000 --workers=4
fi

