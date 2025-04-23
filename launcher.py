import subprocess
import webbrowser
import time
import os

# Get the base path of the launcher
base_path = os.path.dirname(os.path.abspath(__file__))

# Correct paths
backend_path = os.path.join(base_path, "Back-End", "app.py")
frontend_path = os.path.join(base_path, "Front-End", "index.html")

# Start backend
backend = subprocess.Popen(["python", backend_path], creationflags=subprocess.CREATE_NEW_CONSOLE)

# Open frontend
time.sleep(2)
webbrowser.open(f"file:///{frontend_path}")

try:
    backend.wait()
except KeyboardInterrupt:
    backend.terminate()
