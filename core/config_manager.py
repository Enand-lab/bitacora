# core/config_manager.py (actualizado)

import os
import json
from pathlib import Path

DATA_DIR = Path.home() / ".bitacora"
CONFIG_PATH = DATA_DIR / "config.json"
DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config" / "default_config.json"

def ensure_data_dir():
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "uploads").mkdir(exist_ok=True)

def load_config():
    ensure_data_dir()
    if not CONFIG_PATH.exists():
        with open(DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
            default = json.load(f)
        default["setup_completed"] = False  # clave para redirección
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        print(f"✅ Configuración inicial creada: {CONFIG_PATH}")
        return default
    else:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Asegurar campo por compatibilidad
            if "setup_completed" not in config:
                config["setup_completed"] = False
                save_config(config)
            return config

def save_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def get_signalk_config():
    config = load_config()
    sk = config.get("signalk", {})
    return {
        "enabled": sk.get("enabled", False),
        "url": sk.get("url", "").rstrip("/"),
        "token": sk.get("token", ""),
        "client_id": sk.get("client_id", ""),
        "request_href": sk.get("request_href", "")
    }
