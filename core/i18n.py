# core/i18n.py

import json
from pathlib import Path

SUPPORTED_LANGUAGES = {"es", "en", "fr", "zh", "ru", "ja"}

def get_translation(lang="es"):
    """Carga el archivo de traducción para el idioma dado."""
    if lang not in SUPPORTED_LANGUAGES:
        lang = "es"  # fallback seguro
    locale_file = Path(__file__).parent.parent / "locales" / f"{lang}.json"
    if not locale_file.exists():
        locale_file = Path(__file__).parent.parent / "locales" / "es.json"
    with open(locale_file, "r", encoding="utf-8") as f:
        return json.load(f)
