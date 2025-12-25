#!/usr/bin/env bash
set -e

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start services: Gunicorn for web and optionally start celery if CMD provided
# Default: run gunicorn
if [ "$1" = 'gunicorn' ] || [ -z "$1" ]; then
    exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}
else
    exec "$@"
fi
