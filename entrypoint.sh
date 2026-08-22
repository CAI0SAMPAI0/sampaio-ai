#!/bin/sh
set -e

# Run migrations
echo "Running Django database migrations..."
python manage.py migrate --noinput || echo "Database migrations failed or DB is starting up..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput || echo "Collectstatic failed"

# Start Redis server in background (for embedded broker/cache)
if command -v redis-server >/dev/null 2>&1; then
    echo "Starting local Redis server..."
    redis-server --port 6379 --dir /app --protected-mode no --daemonize yes --maxmemory 512mb --maxmemory-policy allkeys-lru >/app/redis.log 2>&1 || true
    sleep 1
else
    echo "Warning: redis-server not found, skipping."
fi

# Start Celery worker in background
echo "Starting Celery worker..."
celery -A core worker --loglevel=info --concurrency=2 --max-tasks-per-child=500 >/app/celery_worker.log 2>&1 &
CELERY_PID=$!
echo "Celery worker started with PID: $CELERY_PID"

# Determine port (Railway assigns $PORT, default to 8080 or 7860)
APP_PORT="${PORT:-8080}"
echo "Starting Django WSGI application (gunicorn on port ${APP_PORT})..."

exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:${APP_PORT} \
    --workers 3 \
    --threads 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
