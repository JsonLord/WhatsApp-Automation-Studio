import os
import time
import requests
from huggingface_hub import HfApi

# Configuration
TOKEN = os.environ.get("HF_TOKEN")
if not TOKEN:
    raise ValueError("HF_TOKEN environment variable not set")

REPO_ID = "AUXteam/Plandex_backup"
REPO_TYPE = "space"

# Log URLs
BUILD_LOG_URL = f"https://huggingface.co/api/spaces/{REPO_ID}/logs/build"
RUN_LOG_URL = f"https://huggingface.co/api/spaces/{REPO_ID}/logs/run"

def upload():
    print(f"Uploading codebase to {REPO_ID}...")
    api = HfApi(token=TOKEN)
    api.upload_folder(
        folder_path=".",
        repo_id=REPO_ID,
        repo_type=REPO_TYPE,
        ignore_patterns=[".git/*", ".github/*", "__pycache__/*", "assets/*", "*.ico", "*.png", "CONTRIBUTING.md", "LICENSE", "RELEASES.md", "whatsapp_msg_automation.py", "deploy.py"]
    )
    print("Upload complete!")

def get_logs(url):
    print(f"Fetching logs from {url}...")
    try:
        headers = {"Authorization": f"Bearer {TOKEN}"}
        # Use a streaming request to simulate log monitoring
        with requests.get(url, headers=headers, stream=True) as response:
            if response.status_code == 200:
                # We only want to see the last part of the logs for monitoring
                # Hugging Face logs are often SSE (Server-Sent Events)
                for line in response.iter_lines():
                    if line:
                        print(line.decode('utf-8'))
            else:
                print(f"Failed to get logs. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching logs: {str(e)}")

def monitor():
    print("Monitoring deployment...")
    print("--- Build Logs ---")
    get_logs(BUILD_LOG_URL)
    print("--- Run Logs ---")
    get_logs(RUN_LOG_URL)

if __name__ == "__main__":
    upload()
    # Wait a bit for the build to start
    time.sleep(10)
    monitor()
