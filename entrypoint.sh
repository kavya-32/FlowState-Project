#!/usr/bin/env bash
set -e

# Apply database migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Auto-seed demo data if database is empty (first deployment)
python << 'EOF'
from django.contrib.auth.models import User
from tasks.models import Workspace

# Check if any data exists
if not User.objects.filter(username='admin').exists() and not Workspace.objects.exists():
    print("Database is empty. Seeding demo data...")
    import subprocess
    subprocess.run(['python', 'manage.py', 'seed_demo'], check=True)
else:
    print("Database already has data. Skipping seed.")
EOF

# Start services: Gunicorn for web and optionally start celery if CMD provided
# Default: run gunicorn
if [ "$1" = 'gunicorn' ] || [ -z "$1" ]; then
    exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-3}
else
    exec "$@"
fi
