import PyInstaller.__main__
import os
import shutil

# Get current directory
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define items to include (templates, static, utils, models.py etc.)
params = [
    'desktop_app.py',             # Main script
    '--name=ResumeIQ',            # App name
    '--windowed',                 # Hide terminal
    '--onefile',                  # Single .exe
    '--clean',                    # Clear cache
    f'--add-data=templates;templates', # Include templates
    f'--add-data=static;static',      # Include static files
    f'--add-data=utils;utils',        # Include utils folder
    '--hidden-import=webview.platforms.winforms',  # Ensure webview backend is included
]

print("Starting Build Process...")
PyInstaller.__main__.run(params)
print("Build Completed. Checking 'dist' folder...")
