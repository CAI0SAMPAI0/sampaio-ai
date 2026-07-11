FROM python:3.12-slim

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install system dependencies including redis-server
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install python dependencies
COPY backend/requirements.txt ./
RUN python -m pip install --upgrade pip && python -m pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY backend/ .
RUN chmod +x ./entrypoint.sh

# Set up permissions for user with UID 1000 (Hugging Face default user)
RUN useradd -m -u 1000 user && \
    chown -R user:user /app

USER user

EXPOSE 7860
CMD ["sh", "./entrypoint.sh"]
