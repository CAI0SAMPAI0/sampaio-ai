import os
import sys
import subprocess
import shutil
import gradio as gr
from fastapi import FastAPI

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
            subprocess.Popen(["redis-server", "--port", "6379", "--protected-mode", "no"])
            import time
            time.sleep(1)
            print("Starting Celery workers...")
            subprocess.Popen(["celery", "-A", "core", "worker", "--loglevel=info"], cwd=backend_dir)
            subprocess.Popen(["celery", "-A", "core", "beat", "--loglevel=info"], cwd=backend_dir)
        except Exception as e:
            print(f"Failed to start background services: {e}")
    else:
        print("Warning: redis-server not found in this environment. Background tasks via Celery might be disabled.")

# Execute migrations and static collection using manage.py inside backend
print("Running database migrations...")
try:
    subprocess.run([sys.executable, os.path.join(backend_dir, "manage.py"), "migrate", "--noinput"])
except Exception as e:
    print(f"Migration error: {e}")

print("Collecting static files...")
try:
    subprocess.run([sys.executable, os.path.join(backend_dir, "manage.py"), "collectstatic", "--noinput", "--clear"])
except Exception as e:
    print(f"Collectstatic error: {e}")

# Run background thread for helper services
import threading
threading.Thread(target=run_background_services, daemon=True).start()

# Define dummy Gradio blocks to satisfy Hugging Face Space requirements
with gr.Blocks() as demo:
    gr.Markdown("# Sampaio AI (Gradio Mount Mode)")
    gr.Markdown("O backend Django está rodando com sucesso no caminho principal `/`.")
    gr.Markdown("A interface do Gradio está montada em `/gradio`.")

# Import Django ASGI app
from core.asgi import application as django_asgi_app

# Create a unified FastAPI app
app = FastAPI()

# Mount Gradio app onto FastAPI under '/gradio'
# This bypasses demo.launch() completely and avoids the "localhost not accessible" issue
app = gr.mount_gradio_app(app, demo, path="/gradio")

# Mount Django ASGI app at the root '/'
# FastAPI will route '/gradio' to Gradio and all other paths to Django
app.mount("/", django_asgi_app)

if __name__ == "__main__":
    import uvicorn
    # Start the unified application on port 7860
    print("Starting unified FastAPI/Django ASGI server on port 7860...")
    uvicorn.run(app, host="0.0.0.0", port=7860)
