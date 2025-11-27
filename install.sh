#!/bin/bash
set -e  # Abortar ante errores

APP_NAME="bitacora"
USER_HOME="$HOME"
APP_DIR="$USER_HOME/src/$APP_NAME"
DATA_DIR="$USER_HOME/.bitacora"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="${APP_NAME}.service"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_NAME"

# Colores para salida amigable
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}
warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}
success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

# === Comprobaciones iniciales ===
if [[ $EUID -eq 0 ]]; then
    echo "❌ No ejecutes este script como root. Se instalará en tu usuario actual."
    exit 1
fi

log "Instalando $APP_NAME en $APP_DIR..."

# === 1. Dependencias del sistema ===
log "Instalando dependencias del sistema..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv avahi-daemon libjpeg-dev zlib1g-dev

# === 2. Clonar o actualizar el repositorio ===
if [ -d "$APP_DIR" ]; then
    log "Actualizando repositorio existente..."
    cd "$APP_DIR" || exit 1
    git pull
else
    log "Clonando repositorio..."
    mkdir -p "$USER_HOME/src"
    git clone "https://github.com/Enand-lab/$APP_NAME.git" "$APP_DIR"
    cd "$APP_DIR" || exit 1
fi

# === 3. Preguntar por el puerto ===
DEFAULT_PORT=5000
read -p "¿En qué puerto quieres que escuche el Cuaderno de Bitácora? (por defecto: $DEFAULT_PORT): " USER_PORT
PORT=${USER_PORT:-$DEFAULT_PORT}

# Validar que sea un número y esté en rango válido
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1 ] || [ "$PORT" -gt 65535 ]; then
    warn "Puerto inválido. Usando puerto por defecto: $DEFAULT_PORT"
    PORT=$DEFAULT_PORT
fi

success "Cuaderno de Bitácora usará el puerto: $PORT"

# === 4. Entorno virtual y dependencias Python ===
log "Configurando entorno virtual..."
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip
"$VENV_DIR/bin/pip" install -r requirements.txt
success "Dependencias Python instaladas."

# === 5. Directorio de datos y configuración inicial ===
log "Preparando directorio de datos en $DATA_DIR..."
mkdir -p "$DATA_DIR/uploads/deleted"

CONFIG_FILE="$DATA_DIR/config.json"
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" <<EOF
{
  "port": $PORT,
  "language": "es",
  "setup_completed": false,
  "backup_enabled": false,
  "backup_path": "",
  "signalk": {
    "enabled": false,
    "url": "",
    "token": "",
    "sync_resources": false,
    "sync_entry_types": ["log", "navigation", "weather"],
    "selected_paths": ["navigation.position", "navigation.state"]
  }
}
EOF
    log "Configuración inicial creada en $CONFIG_FILE con puerto $PORT"
fi
success "Directorio de datos y configuración listos."

# === 6. Servicio systemd ===
log "Creando servicio systemd..."
sudo tee "$SYSTEMD_PATH" > /dev/null <<EOF
[Unit]
Description=Diario de a Bordo ($APP_NAME)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"
success "Servicio $SERVICE_NAME activado e iniciado."

# === 7. Nombre local (mDNS / Avahi) ===
log "Configurando nombre local: bitacora.local..."
if systemctl is-active --quiet avahi-daemon; then
    success "Avahi ya está activo."
else
    sudo systemctl enable --now avahi-daemon
    success "Avahi iniciado."
fi

# === 8. Servicio Avahi personalizado ===
AVAHI_SERVICE="/etc/avahi/services/bitacora.service"
sudo tee "$AVAHI_SERVICE" > /dev/null <<EOF
<?xml version="1.0" standalone='no'?><!--*-nxml-*-->
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>Cuaderno de Bitácora</name>
  <service>
    <type>_http._tcp</type>
    <port>$PORT</port>
    <txt-record>path=/</txt-record>
  </service>
</service-group>
EOF
sudo systemctl restart avahi-daemon
success "Servicio Avahi registrado como 'bitacora.local'"

# === 9. Instrucciones finales ===
IP=$(hostname -I | awk '{print $1}')
echo
success "🎉 ¡Instalación completada!"
echo
echo "👉 Accede a Cuaderno de Bitácora en:"
echo "   http://bitacora.local:$PORT"
echo "   http://$IP:$PORT"
echo
echo "🔧 Primera vez: ve a /setup para ajustar idioma, Signal K, backup, etc."
echo
