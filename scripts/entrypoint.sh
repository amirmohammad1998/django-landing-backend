#!/bin/sh
set -e

echo "Waiting for database to be ready..."
sleep 5

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

if [ "$CELERY_WORKER" = "true" ]; then
    echo "Starting Celery worker..."
    exec celery -A django_landing_backend worker -l info -P gevent
else
    echo "Starting Gunicorn web server..."
    exec gunicorn django_landing_backend.wsgi:application --bind 0.0.0.0:8000 --workers=4
fi
