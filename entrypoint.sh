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
    redis-server --port 6379 --dir /app --protected-mode no --daemonize yes --maxmemory 32mb --maxmemory-policy allkeys-lru >/app/redis.log 2>&1 || true
    sleep 1
else
    echo "Warning: redis-server not found, skipping."
fi

# Start Celery worker in background (concurrency=1, low memory)
echo "Starting Celery worker (concurrency=1, limit memory)..."
celery -A core worker --loglevel=warning --concurrency=1 --max-tasks-per-child=100 --max-memory-per-child=80000 >/app/celery_worker.log 2>&1 &
CELERY_PID=$!
echo "Celery worker started with PID: $CELERY_PID"

# Run Django ASGI app with uvicorn (optimized for 512MB RAM)
# --workers 1: single process to save memory (Celery + Redis already use RAM)
# --threads 4: handle I/O concurrently without extra process memory
# --limit-concurrency 100: prevent memory overload from too many connections
# --timeout-keep-alive 30: close idle connections faster
echo "Starting Django ASGI application (uvicorn, workers=1, threads=4)..."
exec uvicorn core.asgi:application \
    --host 0.0.0.0 \
    --port ${PORT:-7860} \
    --workers 1 \
    --threads 4 \
    --timeout-keep-alive 30 \
    --limit-concurrency 100 \
    --log-level warning
