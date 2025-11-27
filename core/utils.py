# core/utils.py
import markdown
import bleach

def render_markdown_safe(text):
    """Convierte Markdown a HTML seguro."""
    if not text:
        return ""
    html = markdown.markdown(text, extensions=['nl2br'])  # <-- ¡NUEVO!
    allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'h1', 'h2', 'h3']
    allowed_attrs = {}
    clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs, strip=True)
    return clean_html
