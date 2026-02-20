import os
import sys
import threading
import webview
from app import app

def start_flask():
    # Use a fixed port for the desktop app
    app.run(port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # Start Flask in a background thread
    t = threading.Thread(target=start_flask)
    t.daemon = True
    t.start()

    # Create a pywebview window
    webview.create_window('ResumeIQ Desktop', 'http://127.0.0.1:5000', 
                          width=1200, height=800, 
                          min_size=(800, 600))
    webview.start()
