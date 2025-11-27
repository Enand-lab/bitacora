# REST API — Automation and Programmatic Access

Logbook exposes a lightweight REST API to interact with the journal from external systems (e.g., Node-RED, custom scripts, or plugins).

All endpoints return JSON and use standard HTTP methods. No authentication is required, as the API assumes usage within a trusted local network (e.g., your boat’s LAN).

⚠️ Important: This API is not intended for public internet exposure. Use only in trusted, private networks.

## Available Endpoints

### Create a quick note

POST /api/quick-note  
Body: {"text": "Your message"}  
→ Creates a "log"-type entry. If Signal K is active and position data is available, the note is enriched and published (according to your sync settings).

### List entries

GET /api/entries  
Parameters: ?page=1&type=log&source=auto  
→ Returns paginated entries (20 per page), filterable by type (log, weather, etc.) and source (manual / auto).

### Delete an entry

DELETE /api/entry/<id>  
→ Deletes the entry, moves its image (if any) to uploads/deleted/, and removes the corresponding note from Signal K (if synced).

### Create a full entry

POST /api/entry  
Form fields:

- text (required)
- timestamp_utc (optional, ISO 8601)
- entry_type
- navigation_state
- metadata (JSON string)
- media_file (image upload: JPG/PNG)  
  → Ideal for advanced integrations.

### Update an entry

PUT /api/entry/<id>  
→ Updates text, metadata, or image (upload new or delete current).

### Trigger manual backup

POST /api/backup  
→ Only works if backup is enabled in /setup. Generates a .zip containing:

- logbook.db
- config.json
- All active images in uploads/ (excludes deleted/)

```
curl -X POST http://bitacora.local:5000/api/quick-note \
  -H "Content-Type: application/json" \
  -d '{"text": "Southerly wind, 15 knots, choppy sea."}'
```

Supported entry types: log, navigation, weather, maintenance, fuel, radio, provision, other, experience.  
Signal K sync depends on the sync_resources and sync_entry_types settings in your configuration.
