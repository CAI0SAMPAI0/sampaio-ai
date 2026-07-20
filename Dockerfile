FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install redis-server for embedded broker (saves ~100MB vs separate container)
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-server \
    procps \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x ./entrypoint.sh

EXPOSE 7860
CMD ["sh", "./entrypoint.sh"]
