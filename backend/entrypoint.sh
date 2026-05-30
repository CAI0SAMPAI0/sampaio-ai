#!/bin/sh
set -e

# Apply migrations and collect static files, then run gunicorn
python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3
