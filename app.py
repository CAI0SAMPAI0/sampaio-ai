import os
import sys
import subprocess
import shutil
import gradio as gr

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
    gr.Markdown("# Sampaio AI (Gradio Integrated Mode)")
    gr.Markdown("O backend Django está rodando com sucesso no caminho principal `/`.")
    gr.Markdown("A interface do Gradio está integrada e montada.")

# Import Django ASGI app
from core.asgi import application as django_asgi_app

# Create Gradio's FastAPI application structure
demo.app = gr.routes.App.create_app(demo)

# Mount Django ASGI app at the root '/' of Gradio's FastAPI application.
# This ensures Django receives all traffic not handled by Gradio.
demo.app.mount("/", django_asgi_app)

if __name__ == "__main__":
    # Launch Gradio on port 7860 using server_name="0.0.0.0"
    # This satisfies Hugging Face's wrapper, keeps it running, and avoids loopback check errors
    print("Launching Gradio with integrated Django ASGI on port 7860...")
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
