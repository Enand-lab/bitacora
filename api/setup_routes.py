# api/setup_routes.py

from flask import Blueprint, request, render_template, jsonify, redirect, url_for
from core.config_manager import load_config, save_config
from core.signalk_client import request_access, check_access_request, test_signalk_connection

from core.i18n import get_translation

setup_bp = Blueprint('setup', __name__, template_folder='../templates')

@setup_bp.route("/setup", methods=["GET"])
def setup_page():
    config = load_config()
    lang = config.get("language", "es")
    t = get_translation(lang)
    return render_template("setup.html", config=config, t=t)

@setup_bp.route("/setup/save", methods=["POST"])
def save_setup():
    data = request.get_json()
    config = load_config()
    
    # print("📡 Datos recibidos:", data)  # ← Esto se verá en journalctl

    # Campos generales
    config["port"] = int(data.get("port", 8384))
    config["language"] = data.get("language", "es")
    config["setup_completed"] = True

    # Sección de Signal K
    sk = config.get("signalk", {})
    sk["enabled"] = data.get("signalk_enabled", False)
    sk["url"] = data.get("signalk_url", "").rstrip("/")
    sk["token"] = data.get("signalk_token", "")

    # ✅ NUEVOS CAMPOS: sincronización con recursos
    sk["sync_resources"] = data.get("signalk_sync_resources", False)
    sk["sync_entry_types"] = data.get("signalk_sync_entry_types", ["log", "navigation", "weather"])
    
    # Campos de backup
    config["backup_enabled"] = data.get("backup_enabled", False)
    config["backup_path"] = data.get("backup_path", "").strip()

    # Mantener selected_paths si ya existía (para no borrarlo)
    # Si quieres permitir editarlo en el futuro, añádelo aquí desde `data`
    # ✅ Nuevos campos: paths seleccionados
    sk["selected_paths"] = data.get("signalk_selected_paths", ["navigation.position", "navigation.state"])

    config["signalk"] = sk

    save_config(config)
    return jsonify({"status": "ok"})

@setup_bp.route("/setup/signalk/request", methods=["POST"])
def signalk_request():
    url = request.json.get("url")
    if not url:
        return jsonify({"success": False, "error": "URL requerida"})
    result = request_access(url)
    return jsonify(result)

@setup_bp.route("/setup/signalk/check", methods=["POST"])
def signalk_check():
    url = request.json.get("url")
    href = request.json.get("href")
    if not url or not href:
        return jsonify({"success": False, "error": "Faltan parámetros"})
    result = check_access_request(url, href)
    return jsonify(result)

@setup_bp.route("/setup/signalk/test", methods=["POST"])
def signalk_test():
    url = request.json.get("url")
    token = request.json.get("token")
    result = test_signalk_connection(url, token)
    return jsonify(result)

@setup_bp.route("/setup/signalk/test-path", methods=["POST"])
def test_signalk_path():
    data = request.get_json()
    test_url = data.get("url")
    token = data.get("token")

    if not test_url or not token:
        return jsonify({"success": False, "error": "Faltan parámetros"})

    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(test_url, headers=headers, timeout=5)
        if response.status_code == 200:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": f"Error {response.status_code}"})
    except Exception as e:
        return jsonify({"success": False, "error": f"Sin conexión o path inválido: {str(e)}"})
