# core/signalk_client.py (actualizado)

import requests
import json
import uuid
from .config_manager import get_signalk_config, save_config, load_config

def is_signalk_enabled():
    sk = get_signalk_config()
    return sk["enabled"] and sk["url"]

def request_access(url, description="Diario de a Bordo"):
    client_id = str(uuid.uuid4())
    payload = {"clientId": client_id, "description": description}
    try:
        response = requests.post(
            f"{url.rstrip('/')}/signalk/v1/access/requests",
            json=payload,
            timeout=5
        )
        if response.status_code == 202:
            data = response.json()
            # Guardar temporalmente en config
            config = load_config()
            config["signalk"]["client_id"] = client_id
            config["signalk"]["request_href"] = data["href"]
            save_config(config)
            return {"success": True, "href": data["href"]}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_access_request(url, href):
    try:
        response = requests.get(f"{url.rstrip('/')}{href}", timeout=5)
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}"}
        data = response.json()
        if data.get("state") == "COMPLETED":
            ar = data.get("accessRequest", {})
            if ar.get("permission") == "APPROVED":
                token = ar.get("token")
                if token:
                    config = load_config()
                    config["signalk"]["token"] = token
                    config["signalk"]["enabled"] = True
                    # Limpiar datos temporales
                    config["signalk"].pop("request_href", None)
                    config["signalk"].pop("client_id", None)
                    save_config(config)
                    return {"success": True, "token": token}
                else:
                    return {"success": False, "error": "Token no recibido"}
            else:
                return {"success": False, "error": "Acceso denegado"}
        else:
            return {"success": False, "state": data.get("state")}  # PENDING, etc.
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_signalk_connection(url, token):
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        response = requests.get(
            f"{url.rstrip('/')}/signalk/v1/api/vessels/self/navigation/position",
            headers=headers,
            timeout=5
        )
        if response.status_code == 200:
            return {"success": True}
        elif response.status_code == 401:
            return {"success": False, "error": "Token inválido o sin permisos"}
        else:
            return {"success": False, "error": f"Error {response.status_code}"}
    except Exception as e:
        return {"success": False, "error": f"Sin conexión: {str(e)}"}
    
# core/signalk_client.py — actualiza esta función

def get_signalk_data(paths):
    if not is_signalk_enabled():
        return {}

    sk = get_signalk_config()
    headers = {"Authorization": f"Bearer {sk['token']}"} if sk["token"] else {}
    result = {}

    try:
        for path in paths:
            url_path = path.replace(".", "/")
            url = f"{sk['url']}/signalk/v1/api/vessels/self/{url_path}"
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                raw = response.json()

                if path == "navigation.position":
                    # Extraer desde raw["value"] si existe
                    lat, lon = None, None
                    if isinstance(raw, dict):
                        value = raw.get("value")
                        if isinstance(value, dict):
                            try:
                                lat = float(value.get("latitude"))
                                lon = float(value.get("longitude"))
                            except (TypeError, ValueError):
                                pass
                    if lat is not None and lon is not None:
                        result[path] = [lat, lon]
                    else:
                        result[path] = None

                elif path == "navigation.state":
                    # Para navigation.state, también puede tener "value"
                    if isinstance(raw, dict) and "value" in raw:
                        result[path] = raw["value"]
                    else:
                        result[path] = raw  # en caso de que sea string directo

                else:
                    # Otros paths: devolver tal cual
                    result[path] = raw

    except Exception as e:
        print(f"⚠️  Error al consultar Signal K: {e}")
        return {}

    return result

def publish_note_to_resources(note_data):
    sk = get_signalk_config()
    if not sk.get("enabled") or not sk.get("url") or not sk.get("token"):
        return None

    url = f"{sk['url'].rstrip('/')}/signalk/v2/api/resources/notes"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {sk['token']}"
    }

    # ✅ Sin "type": "note" → ya está en la URL
    resource = {
        "description": note_data.get("text", "")[:200],
        "timestamp": note_data["timestamp_utc"],
        "origin": "logbook"
    }

    # Añadir posición si existe
    if note_data.get("latitude") is not None and note_data.get("longitude") is not None:
        resource["position"] = {
            "latitude": note_data["latitude"],
            "longitude": note_data["longitude"]
        }

    # Añadir navigationState si existe
    if note_data.get("navigation_state"):
        resource["navigationState"] = note_data["navigation_state"]
    
    #Debug
    print(f"📤 Publicando nota en: {url}")
    print(f"   Cuerpo: {json.dumps(resource, indent=2)}")
    print(f"   Cabeceras: Authorization: Bearer {'*' * len(sk['token'])}")
    
    try:
        response = requests.post(
            url,
            data=json.dumps(resource, ensure_ascii=False),
            headers=headers,
            timeout=10
        )
        #Debug
        print(f"   Respuesta: {response.status_code} {response.text}")
        
        if response.status_code in (200, 201):
            result = response.json()
            return result.get("id")
        else:
            print(f"❌ Signal K error {response.status_code}: {response.text}")
            return None
    except Exception as e:
        print(f"⚠️  Excepción en publish_note_to_resources: {e}")
        return None
