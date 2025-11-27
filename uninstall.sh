#!/bin/bash
set -e

APP_NAME="bitacora"
USER_HOME="$HOME"
APP_DIR="$USER_HOME/src/$APP_NAME"
DATA_DIR="$USER_HOME/.bitacora"
SERVICE_NAME="${APP_NAME}.service"
SYSTEMD_PATH="/etc/systemd/system/$SERVICE_NAME"
AVAHI_SERVICE="/etc/avahi/services/bitacora.service"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

log "Iniciando desinstalación de Cuaderno de Bitácora..."

# 1. Detener y eliminar servicio
if systemctl is-active --quiet "$SERVICE_NAME"; then
    sudo systemctl stop "$SERVICE_NAME"
fi
sudo systemctl disable "$SERVICE_NAME" 2>/dev/null || true
sudo rm -f "$SYSTEMD_PATH"
sudo systemctl daemon-reload
log "Servicio systemd eliminado."

# 2. Eliminar servicio Avahi
if [ -f "$AVAHI_SERVICE" ]; then
    sudo rm -f "$AVAHI_SERVICE"
    sudo systemctl restart avahi-daemon
    log "Servicio Avahi eliminado."
fi

# 3. Preguntar antes de borrar datos personales
if [ -d "$DATA_DIR" ]; then
    warn "Se encontró la carpeta de datos en $DATA_DIR"
    read -p "¿Deseas ELIMINAR también tus entradas, imágenes y configuración? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf "$DATA_DIR"
        log "Datos de usuario eliminados."
    else
        warn "Los datos se han conservado en $DATA_DIR"
    fi
else
    log "No se encontraron datos de usuario."
fi

# 4. Eliminar carpeta del proyecto (opcional)
if [ -d "$APP_DIR" ]; then
    read -p "¿Eliminar también la carpeta del proyecto ($APP_DIR)? (s/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf "$APP_DIR"
        log "Carpeta del proyecto eliminada."
    else
        warn "La carpeta del proyecto se ha conservado."
    fi
else
    log "Carpeta del proyecto no encontrada."
fi

log "✅ Desinstalación completada."
