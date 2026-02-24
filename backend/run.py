"""
Entry point for the ResumeIQ server.

Run from the project root:
    python server/run.py

Or from inside the server/ directory:
    python run.py
"""
import sys
import os

# Make sure Python can find the server package regardless of CWD
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
