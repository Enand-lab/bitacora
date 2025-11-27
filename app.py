# app.py (completo, corregido)

import os
from flask import Flask, redirect, render_template, send_from_directory, request
import sqlite3

from pathlib import Path

import markdown
import bleach

from core.i18n import get_translation
from core.config_manager import load_config, DATA_DIR
from core.database import init_db
from api.setup_routes import setup_bp
from api.log_routes import log_bp
from core.utils import render_markdown_safe

# ✅ Crear la BD al inicio (si no existe)
init_db()

DATA_DIR = Path.home() / ".bitacora"

app = Flask(__name__)
app.register_blueprint(setup_bp)
app.register_blueprint(log_bp, url_prefix='/api')

@app.before_request
def check_setup():
    config = load_config()
    from flask import request
    if not config.get("setup_completed"):
        if request.endpoint != 'setup.setup_page' and not request.endpoint.startswith('setup.'):
            return redirect("/setup")

@app.route("/")
def logbook_view():
    config = load_config()
    if not config.get("setup_completed"):
        return redirect("/setup")

    lang = config.get("language", "es")
    t = get_translation(lang)
    
    # Filtro por entry_type (ya lo tienes)
    entry_type = request.args.get("type", "").strip()
    valid_types = {"log", "maintenance", "weather", "navigation", "fuel", "radio", "provision", "other", "experience"}
    if entry_type not in valid_types:
        entry_type = None

    # Nuevo: filtro por origen (manual/automática)
    source_filter = request.args.get("source", "").strip()
    valid_sources = {"manual", "auto"}  # 'auto' = todo lo que no es manual
    if source_filter not in valid_sources:
        source_filter = None

    db_path = DATA_DIR / "logbook.db"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Construir query dinámica
    where_clauses = []
    params = []

    if entry_type:
        where_clauses.append("entry_type = ?")
        params.append(entry_type)

    if source_filter == "manual":
        where_clauses.append("source IN ('manual', 'quick-note')")
    elif source_filter == "auto":
        where_clauses.append("source NOT IN ('manual', 'quick-note')")

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    query = f"SELECT * FROM log_entries {where} ORDER BY timestamp_utc DESC LIMIT 50"

    c.execute(query, params)
    entries = [dict(row) for row in c.fetchall()]
    conn.close()
    
    for entry in entries:
        entry["text_html"] = render_markdown_safe(entry["text"])
    
    return render_template(
        "logbook.html",
        entries=entries,
        t=t,
        current_entry_type=entry_type,
        current_source=source_filter,
        config=config
    )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(DATA_DIR / "uploads", filename)



if __name__ == "__main__":
    config = load_config()
    app.run(host="0.0.0.0", port=config.get("port", 8384), debug=True)
