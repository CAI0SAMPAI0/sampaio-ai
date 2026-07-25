import os
import sys
import subprocess
import shutil
import gradio as gr
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from django.core.wsgi import get_wsgi_application

# Ensure local loopback checks bypass any proxy configuration
os.environ["NO_PROXY"] = "localhost,127.0.0.1"


# Add the backend directory to Python sys.path
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
sys.path.insert(0, backend_dir)

# Set Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")


# Try starting Redis and Celery in the background if redis-server is available
def run_background_services():
    if shutil.which("redis-server"):
        print("Starting local Redis server...")
        try:
            subprocess.Popen(
                ["redis-server", "--port", "6379", "--protected-mode", "no"]
            )
            import time

            time.sleep(1)
            print("Starting Celery workers...")
            subprocess.Popen(
                ["celery", "-A", "core", "worker", "--loglevel=info"], cwd=backend_dir
            )
            subprocess.Popen(
                ["celery", "-A", "core", "beat", "--loglevel=info"], cwd=backend_dir
            )
        except Exception as e:
            print(f"Failed to start background services: {e}")
    else:
        print(
            "Warning: redis-server not found in this environment. Background tasks via Celery might be disabled."
        )


# Execute migrations and static collection using manage.py inside backend
print("Running database migrations...")
try:
    subprocess.run(
        [sys.executable, os.path.join(backend_dir, "manage.py"), "migrate", "--noinput"]
    )
except Exception as e:
    print(f"Migration error: {e}")

print("Collecting static files...")
try:
    subprocess.run(
        [
            sys.executable,
            os.path.join(backend_dir, "manage.py"),
            "collectstatic",
            "--noinput",
            "--clear",
        ]
    )
except Exception as e:
    print(f"Collectstatic error: {e}")

# Run background thread for helper services
import threading

threading.Thread(target=run_background_services, daemon=True).start()

# Initialize the standard Django WSGI application
django_app = get_wsgi_application()

# Create a FastAPI wrapper to manage the Django route
fastapi_app = FastAPI()
fastapi_app.mount("/", WSGIMiddleware(django_app))

# Define visual dummy Gradio blocks to satisfy Hugging Face Space requirements
with gr.Blocks() as demo:
    gr.Markdown("# Painel de Controle - Sampaio AI")
    gr.Markdown(
        "A aplicação Django está rodando em segundo plano integrada a este Space."
    )
    gr.Markdown(
        "O painel do Django está disponível na raiz `/` e a interface do Gradio em `/gradio_interface`."
    )

# Mount the FastAPI app (which wraps Django) inside Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/gradio_interface")

if __name__ == "__main__":
    # For local running/testing
    import uvicorn

    uvicorn.run("app:app", host="0.0.0.0", port=7860, log_level="info")
