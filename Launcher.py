import threading
import webbrowser
import time
import sys
import os

# Dynamically adjust paths based on PyInstaller or normal run
if hasattr(sys, '_MEIPASS'):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(os.path.abspath(__file__))

# Adjust sys.path to include Back-End so we can import App.py easily
sys.path.insert(0, os.path.join(base_path, "Back-End"))

# Import Flask app
from App import app

def run_flask():
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def main():
    # Start Flask server in a background thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Give Flask a moment to start
    time.sleep(2)

    # Open the Front-End page
    webbrowser.open("http://127.0.0.1:5000")

    # Keep the main thread alive to prevent program from exiting
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()
