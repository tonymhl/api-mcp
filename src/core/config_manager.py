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
            "MCP_ENDPOINT": "wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjQwNzY5MCwiYWdlbnRJZCI6NDk0MTg4LCJlbmRwb2ludElkIjoiYWdlbnRfNDk0MTg4IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc1Mzg2NDc3M30.CG1Peq9o0zkX3NZxk1uoKTPq4dd_y0x0bGcwUywQUFavXwHVA6W1IRQ9RkzNPu9IrypwdADUvDuSedWTwltCfA",
        }

def save_config(config):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)