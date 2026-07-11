import os
import sys
import subprocess
import threading
import time
import shutil

# Add the backend directory to Python sys.path so we can import django settings and core
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
threading.Thread(target=run_background_services, daemon=True).start()

# Load Gradio
import gradio as gr
with gr.Blocks() as demo:
    gr.Markdown("# Sampaio AI Backend (Gradio Mode)")
    gr.Markdown("O backend Django está rodando com sucesso em segundo plano e escutando na porta principal 7860.")

if __name__ == "__main__":
    # Launch Gradio on 7861 to satisfy Hugging Face Spaces SDK requirement
    print("Launching dummy Gradio interface on port 7861...")
    demo.launch(prevent_thread_lock=True, server_port=7861)
    
    # Launch Django ASGI on port 7860 using uvicorn
    print("Starting Django ASGI server via Uvicorn on port 7860...")
    import uvicorn
    uvicorn.run("core.asgi:application", host="0.0.0.0", port=7860, log_level="info")
