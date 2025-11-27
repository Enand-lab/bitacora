#  API REST — Automatización y acceso programático

**Derrotero expone una API ligera** para interactuar con el diario desde otros sistemas (como Node-RED, scripts, o plugins).  
Todos los endpoints devuelven JSON y usan métodos HTTP estándar. No requieren autenticación adicional (asume que se usan en entorno local o LAN privada).

> ⚠️ **Importante**: esta API no está pensada para exponerse a internet. Usa siempre en redes de confianza (como la red local del barco).

---

## Endpoints disponibles

### Crear nota rápida
**POST** `/quick-note`  
Cuerpo: `{"text": "Tu mensaje"}`  
→ Crea una entrada de tipo `"log"` desde un sistema automático. Si Signal K está activo y hay posición, se enriquece y se publica (según configuración).

---

### Listar entradas
**GET** `/entries`  
Parámetros: `?page=1&type=log&source=auto`  
→ Devuelve entradas paginadas (20 por página), filtrables por tipo (`log`, `weather`, etc.) y origen (`manual` / `auto`).

---

### Eliminar entrada
**DELETE** `/entry/<id>`  
→ Borra entrada, mueve imagen a `deleted/` y elimina nota en Signal K (si aplica).

---

### Crear entrada completa
**POST** `/entry`  
Campos: `text`, `timestamp_utc` (opcional), `entry_type`, `navigation_state`, `metadata` (JSON), `media_file` (imagen).  
→ Útil para integraciones avanzadas.

---

### Editar entrada
**PUT** `/entry/<id>`  
→ Actualiza texto, metadatos, imagen (subir nueva o eliminar).

---

### Generar copia de seguridad
**POST** `/backup`  
→ Solo si está habilitado en `/setup`. Genera `.zip` con base de datos, configuración e imágenes activas.

---

## Ejemplo con curl

```bash
curl -X POST http://bitacora.local:5000/quick-note \
  -H "Content-Type: application/json" \
  -d '{"text": "Viento sur 15 nudos, mar rizada."}'
```
> Tipos de entrada soportados: log, navigation, weather, maintenance, fuel, radio, provision, other, experience.
Sincronización con Signal K: depende de sync_resources y sync_entry_types en la configuración.


---


