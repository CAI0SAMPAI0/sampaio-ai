#!/bin/sh
set -e

# Run migrations
echo "Running Django database migrations..."
python manage.py migrate --noinput || echo "Database migrations failed or DB is starting up..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed"

# Check if running in Hugging Face Spaces or requested single-container mode
if [ -n "$SPACE_ID" ] || [ "$RUN_CELERY_AND_REDIS" = "true" ]; then
    echo "Hugging Face Space or single-container environment detected."
    
    # Start Redis in background (using /app to ensure permissions are writable)
    if command -v redis-server >/dev/null 2>&1; then
        echo "Starting local Redis server..."
        redis-server --port 6379 --dir /app --protected-mode no >/app/redis.log 2>&1 &
    else
        echo "Warning: redis-server not found, skipping."
    fi
    
    # Start Celery Worker
    echo "Starting Celery worker..."
    celery -A core worker --loglevel=info >/app/celery_worker.log 2>&1 &
    
    # Start Celery Beat
    echo "Starting Celery beat..."
    celery -A core beat --loglevel=info >/app/celery_beat.log 2>&1 &
fi

# Run Django ASGI app with uvicorn
echo "Starting Django ASGI application..."
exec uvicorn core.asgi:application --host 0.0.0.0 --port ${PORT:-8000}

