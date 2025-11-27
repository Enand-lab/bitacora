# core/database.py

from pathlib import Path
import sqlite3

from .config_manager import DATA_DIR

DB_PATH = DATA_DIR / "logbook.db"

def init_db():
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS log_entries (
            id INTEGER PRIMARY KEY,
            timestamp_utc TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            navigation_state TEXT,
            text TEXT,
            media_path TEXT,
            source TEXT DEFAULT 'manual',
            entry_type TEXT DEFAULT 'log',
            signalK_resource_id TEXT,
            metadata TEXT
        )
    """)
    conn.commit()
    conn.close()
