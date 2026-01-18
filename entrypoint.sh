#!/usr/bin/env bash
set -e

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Auto-seed demo data if database is empty (first deployment)
# Check if Workspace table has any data
if ! python manage.py shell -c "from tasks.models import Tenant; exit(0 if Tenant.objects.exists() else 1)" 2>/dev/null; then
    echo "Database is empty. Seeding demo data..."
    python manage.py seed_demo || true
fi

# Start services: Gunicorn for web and optionally start celery if CMD provided
# Default: run gunicorn
if [ "$1" = 'gunicorn' ] || [ -z "$1" ]; then
    exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}
else
    exec "$@"
fi
