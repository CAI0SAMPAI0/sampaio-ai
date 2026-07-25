#!/bin/sh
set -e

# Run migrations
echo "Running Django database migrations..."
python manage.py migrate --noinput || echo "Database migrations failed or DB is starting up..."

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || echo "Collectstatic failed"

# Start Redis server in background (Optimized for 8GB RAM)
if command -v redis-server >/dev/null 2>&1; then
    echo "Starting local Redis server..."
    # Aumentado maxmemory para 1GB (1024mb) para armazenar milhares de sessões e caches sem expirar prematuramente
    redis-server --port 6379 --dir /app --protected-mode no --daemonize yes --maxmemory 1024mb --maxmemory-policy allkeys-lru >/app/redis.log 2>&1 || true
    sleep 1
else
    echo "Warning: redis-server not found, skipping."
fi

# Start Celery worker in background (Optimized for 8GB RAM)
echo "Starting Celery worker (Parallel processing enabled)..."
# Aumentado para 4 workers simultâneos e limite de memória expandido para 512MB (512000) por worker filho
celery -A core worker --loglevel=info --concurrency=4 --max-tasks-per-child=1000 --max-memory-per-child=512000 >/app/celery_worker.log 2>&1 &
CELERY_PID=$!
echo "Celery worker started with PID: $CELERY_PID"

# Run Django ASGI app with uvicorn (Optimized for 8GB RAM)
echo "Starting Django ASGI application (uvicorn, workers=4)..."
# --workers 4: Agora usamos múltiplos processos para aproveitar a CPU e RAM disponíveis
# --timeout-keep-alive 65: Mantém conexões abertas de forma padrão e eficiente
# --log-level info: Melhor visibilidade de logs em produção sem gargalo de I/O
exec uvicorn core.asgi:application \
    --host 0.0.0.0 \
    --port ${PORT:-7860} \
    --workers 4 \
    --timeout-keep-alive 65 \
    --log-level info
