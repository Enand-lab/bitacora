# api/log_routes.py

from flask import Blueprint, request, jsonify, render_template
from datetime import datetime, timezone
import json
import sqlite3
import requests

import shutil
from pathlib import Path
import zipfile

import os
import secrets
from werkzeug.utils import secure_filename

from core.database import DB_PATH, init_db
from core.config_manager import load_config, DATA_DIR
from core.config_manager import get_signalk_config
from core.signalk_client import is_signalk_enabled, get_signalk_data, publish_note_to_resources
from core.utils import render_markdown_safe

from core.i18n import get_translation

# Definir UPLOADS_DIR a nivel global (se evalúa al cargar el módulo)
UPLOADS_DIR = DATA_DIR / "uploads"

log_bp = Blueprint('log', __name__)

@log_bp.route("/quick-note", methods=["POST"])
def quick_note():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "El texto es obligatorio"}), 400

    init_db()

    # Timestamp UTC en formato ISO 8601 + "Z"
    timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Valores por defecto
    latitude = None
    longitude = None
    navigation_state = None
    metadata = {}

    # Intentar obtener datos de Signal K
    if is_signalk_enabled():
        try:
            sk_config = get_signalk_config()
            paths = sk_config.get("selected_paths", ["navigation.position", "navigation.state"])
            sk_data = get_signalk_data(paths)
            metadata.update(sk_data)

            # Procesar navigation.position (ahora siempre será [lat, lon] o None)
            pos = sk_data.get("navigation.position")
            if isinstance(pos, list) and len(pos) == 2:
                latitude = pos[0]
                longitude = pos[1]
            else:
                latitude = longitude = None

            # Procesar navigation.state (debe ser string)
            state_val = sk_data.get("navigation.state")
            if isinstance(state_val, str):
                navigation_state = state_val
            # Si no es str, lo ignoramos (queda None)

        except Exception as e:
            print(f"⚠️  Error al consultar Signal K: {e}")

    # --- Asegurar tipos compatibles con SQLite ---
    # (esto evita el "Error binding parameter 3")
    latitude_db = latitude if latitude is not None else None
    longitude_db = longitude if longitude is not None else None
    navigation_state_db = navigation_state if navigation_state is not None else None
    text_db = str(text)
    metadata_db = json.dumps(metadata, ensure_ascii=False) if metadata else None

    # Guardar en base de datos
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO log_entries (
            timestamp_utc, latitude, longitude, navigation_state, text,
            media_path, source, entry_type, signalK_resource_id, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp_utc,
        latitude_db,
        longitude_db,
        navigation_state_db,
        text_db,
        None,  # media_path
        "quick-note",
        "log",
        None,  # signalK_resource_id (se actualiza luego si aplica)
        metadata_db
    ))
    entry_id = c.lastrowid
    conn.commit()
    conn.close()

    # Intentar publicar en Signal K (solo si hay posición)
    signalK_resource_id = None
    
    #__debug__
    print(f"🔍 Signal K habilitado: {is_signalk_enabled()}")
    print(f"🔍 Lat: {latitude}, Lon: {longitude}")
    print(f"🔍 ¿Debería publicar? {is_signalk_enabled() and latitude is not None and longitude is not None}")
    # Nueva lógica: ¿debo publicar?
    should_publish = False
    if is_signalk_enabled() and latitude is not None and longitude is not None:
        config = load_config()
        sk_cfg = config.get("signalk", {})
        sync_enabled = sk_cfg.get("sync_resources", True)
        sync_types = sk_cfg.get("sync_entry_types", ["log", "navigation", "weather"])
        if isinstance(sync_types, list) and sync_enabled and "log" in sync_types:
            should_publish = True
    
    if should_publish:
        try:
            note_data = {
                "timestamp_utc": timestamp_utc,
                "text": text,
                "latitude": latitude,
                "longitude": longitude,
                "navigation_state": navigation_state
            }
            signalK_resource_id = publish_note_to_resources(note_data)

            if signalK_resource_id:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE log_entries SET signalK_resource_id = ? WHERE id = ?", (signalK_resource_id, entry_id))
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"⚠️  Error al publicar en Signal K: {e}")

    return jsonify({"status": "ok", "id": entry_id})

@log_bp.route("/entry/<int:entry_id>", methods=["DELETE"])
def delete_entry(entry_id):
    # 1. Obtener la entrada completa (incluyendo media_path y signalK_resource_id)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("""
        SELECT signalK_resource_id, media_path 
        FROM log_entries 
        WHERE id = ?
    """, (entry_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Entrada no encontrada"}), 404

    signalK_resource_id = row["signalK_resource_id"]
    media_path = row["media_path"]  # ✅ ¡ahora sí está definido!
    conn.close()

    # 2. Si hay media_path, mover la imagen a uploads/deleted/
    if media_path:
        try:
            src_path = DATA_DIR / media_path  # media_path es relativo: "uploads/imagen.jpg"
            if src_path.exists():
                deleted_dir = UPLOADS_DIR / "deleted"
                deleted_dir.mkdir(exist_ok=True)
                dst_path = deleted_dir / src_path.name
                src_path.rename(dst_path)
                print(f"🖼️  Imagen movida a {dst_path}")
        except Exception as e:
            print(f"⚠️  Error al mover imagen: {e}")

    # 3. Borrar en Signal K (si aplica)
    if signalK_resource_id and is_signalk_enabled():
        try:
            sk = get_signalk_config()
            url = f"{sk['url'].rstrip('/')}/signalk/v2/api/resources/notes/{signalK_resource_id}"
            headers = {"Authorization": f"Bearer {sk['token']}"}
            requests.delete(url, headers=headers, timeout=10)
        except Exception as e:
            print(f"⚠️  Error al borrar en Signal K: {e}")

    # 4. Borrar de la base de datos
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM log_entries WHERE id = ?", (entry_id,))
    conn.commit()
    deleted = c.rowcount > 0
    conn.close()

    return (jsonify({"status": "ok"}), 200) if deleted else (jsonify({"error": "No se pudo eliminar"}), 500)

@log_bp.route("/entry/new")
def new_entry_form():
    config = load_config()
    lang = config.get("language", "es")
    t = get_translation(lang)
    # Añadimos la hora actual en UTC para el campo datetime-local (opcional, pero útil)
    from datetime import datetime, timezone
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")
    return render_template("new_entry.html", t=t, now=now_utc)

@log_bp.route("/entry", methods=["POST"])
def create_entry():
    # Asegurar carpeta de uploads
    UPLOADS_DIR.mkdir(exist_ok=True)

    # Obtener campos
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify({"error": "El texto es obligatorio"}), 400

    timestamp_utc = request.form.get("timestamp_utc")
    if not timestamp_utc:
        timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entry_type = request.form.get("entry_type", "log")
    navigation_state = request.form.get("navigation_state") or None
    metadata_str = request.form.get("metadata", "{}")
    try:
        metadata = json.loads(metadata_str)
    except:
        metadata = {}

    # Manejar subida de imagen
    media_path = None
    if 'media_file' in request.files:
        file = request.files['media_file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower()
            if ext in {'jpg', 'jpeg', 'png'}:
                # Nombre único: timestamp + 6 chars aleatorios
                now_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                random_suffix = secrets.token_hex(3)
                new_filename = f"{now_str}_{random_suffix}.{ext}"
                file_path = UPLOADS_DIR / new_filename
                file.save(file_path)
                media_path = f"uploads/{new_filename}"

    # Obtener posición de Signal K (si está activo)
    latitude = longitude = None
    metadata_from_sk = {}
    if is_signalk_enabled():
        try:
            full_config = load_config()
            selected_paths = full_config.get("signalk", {}).get("selected_paths", ["navigation.position", "navigation.state"])
            sk_data = get_signalk_data(selected_paths)

            # Extraer posición
            pos = sk_data.get("navigation.position")
            if isinstance(pos, list) and len(pos) == 2:
                latitude, longitude = pos[0], pos[1]

            # Guardar todo en metadata
            metadata_from_sk.update(sk_data)
        except Exception as e:
            print(f"⚠️  Error al obtener datos de Signal K: {e}")
    
    # Fusionar metadata del formulario + Signal K
    final_metadata = metadata.copy()
    final_metadata.update(metadata_from_sk)
    
    # Guardar en BD
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO log_entries (
            timestamp_utc, latitude, longitude, navigation_state, text,
            media_path, source, entry_type, signalK_resource_id, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        timestamp_utc,
        latitude,
        longitude,
        navigation_state,
        text,
        media_path,
        "manual",
        entry_type,
        None,
        json.dumps(final_metadata, ensure_ascii=False) if final_metadata else None
    ))
    entry_id = c.lastrowid
    conn.commit()
    conn.close()

    # Publicar en Signal K si hay posición
    signalK_resource_id = None
    # Nueva lógica: ¿debo publicar?
    should_publish = False
    if is_signalk_enabled() and latitude is not None and longitude is not None:
        config = load_config()
        sk_cfg = config.get("signalk", {})
        sync_enabled = sk_cfg.get("sync_resources", True)
        sync_types = sk_cfg.get("sync_entry_types", ["log", "navigation", "weather"])
        if isinstance(sync_types, list) and sync_enabled and entry_type in sync_types:
            should_publish = True
    
    if should_publish:
        try:
            note_data = {
                "timestamp_utc": timestamp_utc,
                "text": text,
                "latitude": latitude,
                "longitude": longitude,
                "navigation_state": navigation_state
            }
            signalK_resource_id = publish_note_to_resources(note_data)
            if signalK_resource_id:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("UPDATE log_entries SET signalK_resource_id = ? WHERE id = ?", (signalK_resource_id, entry_id))
                conn.commit()
                conn.close()
        except Exception as e:
            print(f"⚠️  Error al publicar en Signal K: {e}")

    return jsonify({"status": "ok", "id": entry_id})

@log_bp.route("/entry/<int:entry_id>/edit", methods=["GET"])
def edit_entry_form(entry_id):
    config = load_config()
    lang = config.get("language", "es")
    t = get_translation(lang)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM log_entries WHERE id = ?", (entry_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Entrada no encontrada"}), 404

    entry = dict(row)
    metadata = json.loads(entry.get("metadata") or "{}")

    # Preparar valores para plantilla
    cloud_cover = metadata.get("cloud_cover", 1)

    # Formatear timestamp UTC para datetime-local (sin 'Z', sin microsegundos)
    ts = entry["timestamp_utc"]
    if ts.endswith("Z"):
        ts = ts[:-1]
    if "." in ts:
        ts = ts.split(".")[0]
    # ✅ datetime-local espera local time, pero nosotros usamos UTC → el navegador lo interpreta como "hora local", pero la guardamos como UTC de nuevo
    # No hay conversión real: el usuario edita la hora como si fuera local, pero la app sigue tratándola como UTC.
    # Esto es consistente con cómo ya funciona en new_entry.

    return render_template(
        "edit_entry.html",
        t=t,
        entry=entry,
        metadata=metadata,
        cloud_cover=cloud_cover,
        formatted_timestamp=ts
    )

@log_bp.route("/entry/<int:entry_id>", methods=["PUT"])
def update_entry(entry_id):
    UPLOADS_DIR.mkdir(exist_ok=True)

    # Verificar que la entrada existe
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT media_path FROM log_entries WHERE id = ?", (entry_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        return jsonify({"error": "Entrada no encontrada"}), 404
    old_media_path = row[0]
    conn.close()

    # Procesar formulario
    text = request.form.get("text", "").strip()
    if not text:
        return jsonify({"error": "El texto es obligatorio"}), 400

    timestamp_utc = request.form.get("timestamp_utc")
    if not timestamp_utc:
        timestamp_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    entry_type = request.form.get("entry_type", "log")
    navigation_state = request.form.get("navigation_state") or None

    metadata_str = request.form.get("metadata", "{}")
    try:
        metadata = json.loads(metadata_str)
    except:
        metadata = {}

    # Manejo de imagen
    media_path = old_media_path  # por defecto, conservar
    remove_image = request.form.get("remove_image")  # checkbox

    if remove_image:
        # Mover la actual a deleted/
        if old_media_path:
            try:
                src = DATA_DIR / old_media_path
                if src.exists():
                    deleted_dir = UPLOADS_DIR / "deleted"
                    deleted_dir.mkdir(exist_ok=True)
                    dst = deleted_dir / src.name
                    src.rename(dst)
            except Exception as e:
                print(f"⚠️ Error al mover imagen a deleted: {e}")
        media_path = None

    # ¿Subir nueva imagen?
    if 'media_file' in request.files:
        file = request.files['media_file']
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = filename.rsplit('.', 1)[-1].lower()
            if ext in {'jpg', 'jpeg', 'png'}:
                now_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                random_suffix = secrets.token_hex(3)
                new_filename = f"{now_str}_{random_suffix}.{ext}"
                file_path = UPLOADS_DIR / new_filename
                file.save(file_path)
                media_path = f"uploads/{new_filename}"

                # Si había una imagen anterior y NO se marcó "remove", moverla ahora
                if old_media_path and not remove_image and old_media_path != media_path:
                    try:
                        src = DATA_DIR / old_media_path
                        if src.exists():
                            deleted_dir = UPLOADS_DIR / "deleted"
                            deleted_dir.mkdir(exist_ok=True)
                            dst = deleted_dir / src.name
                            src.rename(dst)
                    except Exception as e:
                        print(f"⚠️ Error al mover imagen antigua: {e}")

    # Actualizar DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        UPDATE log_entries SET
            timestamp_utc = ?,
            navigation_state = ?,
            text = ?,
            media_path = ?,
            entry_type = ?,
            metadata = ?
        WHERE id = ?
    """, (
        timestamp_utc,
        navigation_state,
        text,
        media_path,
        entry_type,
        json.dumps(metadata, ensure_ascii=False) if metadata else None,
        entry_id
    ))
    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "id": entry_id})

@log_bp.route("/entry/<int:entry_id>/view")
def view_entry(entry_id):
    config = load_config()
    lang = config.get("language", "es")
    t = get_translation(lang)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM log_entries WHERE id = ?", (entry_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return jsonify({"error": "Entrada no encontrada"}), 404

    entry = dict(row)
    entry["text_html"] = render_markdown_safe(entry.get("text"))
    
    metadata = json.loads(entry.get("metadata") or "{}")

    # Formatear fecha para mostrar (ej. 24 Nov 2025, 10:30 UTC)
    try:
        dt = datetime.fromisoformat(entry["timestamp_utc"].rstrip("Z"))
        formatted_date = dt.strftime("%d %b %Y, %H:%M UTC")
    except:
        formatted_date = entry["timestamp_utc"]

    # Preparar valores legibles
    sea_state = metadata.get("sea_state", "")
    visibility = metadata.get("visibility", "")
    cloud_cover = metadata.get("cloud_cover", 1)

    return render_template(
        "view_entry.html",
        t=t,
        entry=entry,
        formatted_date=formatted_date,
        sea_state=sea_state,
        visibility=visibility,
        cloud_cover=cloud_cover
    )

@log_bp.route("/entries")
def api_entries():
    page = request.args.get("page", 1, type=int)
    limit = 20
    offset = (page - 1) * limit

    # Aplicar los mismos filtros que en la vista principal
    entry_type = request.args.get("type", "").strip()
    source_filter = request.args.get("source", "").strip()

    valid_types = {"log", "maintenance", "weather", "navigation", "fuel", "radio", "provision", "other", "experience"}
    valid_sources = {"manual", "auto"}

    where_clauses = []
    params = []

    if entry_type in valid_types:
        where_clauses.append("entry_type = ?")
        params.append(entry_type)

    if source_filter == "manual":
        where_clauses.append("source IN ('manual', 'quick-note')")
    elif source_filter == "auto":
        where_clauses.append("source NOT IN ('manual', 'quick-note')")

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

    query = f"""
        SELECT id, timestamp_utc, latitude, longitude, navigation_state,
               text, media_path, source, entry_type
        FROM log_entries
        {where}
        ORDER BY timestamp_utc DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    conn = sqlite3.connect(DATA_DIR / "logbook.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()

    entries = [dict(row) for row in rows]
    return jsonify(entries)

@log_bp.route("/backup", methods=["POST"])
def create_backup():
    config = load_config()
    if not config.get("backup_enabled"):
        return jsonify({"error": "Backup no habilitado"}), 400
    
    backup_path = Path(config.get("backup_path", "")).expanduser()
    if not backup_path.exists() or not os.access(backup_path, os.W_OK):
        return jsonify({"error": "Ruta de backup no válida o sin permisos"}), 400

    # Crear nombre único
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    zip_name = f"logbook_backup_{timestamp}.zip"
    zip_path = backup_path / zip_name

    try:
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Base de datos
            db_file = DATA_DIR / "logbook.db"
            if db_file.exists():
                zf.write(db_file, "logbook.db")
            
            # 2. Configuración
            config_file = DATA_DIR / "config.json"
            if config_file.exists():
                zf.write(config_file, "config.json")
            
            # 3. Imágenes (solo uploads/, no deleted/)
            uploads_dir = DATA_DIR / "uploads"
            if uploads_dir.exists():
                for img in uploads_dir.iterdir():
                    if img.is_file() and img.name != "deleted":
                        zf.write(img, f"uploads/{img.name}")
        
        return jsonify({"status": "ok", "file": str(zip_path)})
    
    except Exception as e:
        print(f"❌ Error al crear backup: {e}")
        return jsonify({"error": str(e)}), 500
