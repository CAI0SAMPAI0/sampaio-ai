import subprocess
import threading
import http.server
import socketserver
import os
import sys

PORT = int(os.environ.get("PORT", 8000))


class HealthCheckHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Worker is Running")


def run_health_check_server():
    handler = HealthCheckHandler
    socketserver.TCPServer.allow_reuse_address = True
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
            print(f"Health check server listening on port {PORT}")
            httpd.serve_forever()
    except Exception as e:
        print(f"Error starting health check server: {e}")


def run_celery_worker():
    # In Windows, we might need event loop policy or -P eventlet/solo,
    # but on Linux (Render) standard pool works fine.
    # We detect OS to adapt pool if running locally in Windows.
    pool_args = []
    if os.name == "nt":
        pool_args = ["-P", "solo"]
    else:
        # Limit concurrency to 1 on Render Free Tier to avoid running out of memory (512MB limit)
        pool_args = ["--concurrency=1"]

    cmd = ["celery", "-A", "core", "worker", "--loglevel=info"] + pool_args
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd)


if __name__ == "__main__":
    # Start the HTTP health check server in a background thread
    t = threading.Thread(target=run_health_check_server, daemon=True)
    t.start()

    # Run the Celery worker in the main thread
    try:
        run_celery_worker()
    except KeyboardInterrupt:
        sys.exit(0)
