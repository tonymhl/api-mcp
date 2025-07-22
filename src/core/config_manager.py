import json
import os
from pathlib import Path

CONFIG_PATH = Path.home() / ".xiaozhi_mcp_config.json"

def load_config():
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "MCP_ENDPOINT": "wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjQwNzY5MCwiYWdlbnRJZCI6NDk0MTg4LCJlbmRwb2ludElkIjoiYWdlbnRfNDk0MTg4IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc1MzE2ODY5Mn0.0iF0jqrMIy4WMQhQePphQLOOZHWmHIowoO3lfHvL2_c3S5y4L5MnYT1vIYY2W1YuX4wiVMf5FN7xMwcthUQIug",
        }

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)