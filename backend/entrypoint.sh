#!/bin/sh
set -e

# Run migrations
echo "Running Django database migrations..."
python manage.py migrate --noinput || echo "Database migrations failed or DB is starting up..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed"

# Run Django ASGI app with uvicorn
echo "Starting Django ASGI application..."
exec uvicorn core.asgi:application --host 0.0.0.0 --port ${PORT:-8000}

