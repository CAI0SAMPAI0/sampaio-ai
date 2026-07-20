#!/bin/sh
set -e

# Run migrations
echo "Running Django database migrations..."
python manage.py migrate --noinput || echo "Database migrations failed or DB is starting up..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed"

# Start Redis server in background (embedded, saves ~100MB vs separate container)
if command -v redis-server >/dev/null 2>&1; then
    echo "Starting local Redis server..."
    redis-server --port 6379 --dir /app --protected-mode no --daemonize yes >/app/redis.log 2>&1 || true
    sleep 1
else
    echo "Warning: redis-server not found, skipping."
fi

# Start Celery worker in background (concurrency=1 to fit in 512MB RAM)
echo "Starting Celery worker (concurrency=1)..."
celery -A core worker --loglevel=info --concurrency=1 >/app/celery_worker.log 2>&1 &
CELERY_PID=$!
echo "Celery worker started with PID: $CELERY_PID"

# Run Django ASGI app with uvicorn (foreground process)
echo "Starting Django ASGI application..."
exec uvicorn core.asgi:application --host 0.0.0.0 --port ${PORT:-7860}
