# Guía de instalación

Cuaderno de Bitácora está diseñado para instalarse en sistemas Linux (Raspberry Pi, NUC, etc.) mediante un script automatizado.

## Requisitos

- Sistema Linux con `systemd` (Raspbian, Ubuntu, Debian…)
- Python 3.8+
- Acceso a terminal y permisos de usuario normal (no root)

## Pasos

### Pasos

1. **Obtén los archivos del proyecto**. Puedes hacerlo de dos formas:

   **Opción A (recomendada si usas Git):**
   ```bash
   git clone https://github.com/Enand-lab/bitacora.git ~/src/bitacora
   ```
   
   **Opción B (sin Git, ideal para sistemas mínimos):**
   ```bash
   # 1. Crea una carpeta para el proyecto
    mkdir -p ~/src/bitacora

    # 2. Entra en la carpeta
    cd ~/src/bitacora

    # 3. Descarga los archivos directamente desde GitHub
    wget https://github.com/Enand-lab/bitacora/archive/refs/heads/main.tar.gz

    # 4. Descomprime
    tar -xzf main.tar.gz --strip-components=1

    # 5. Limpia el archivo comprimido
    rm main.tar.gz
   ```

2. **Ejecuta el script de instalación**:

   ```bash
   # Entra en la carpeta
   cd ~/src/bitacora
   
   # Dale permisos de ejecución
   chmod +x install.sh
   
   # Ejecuta el script
   ./install.sh
   ```

    El script:

    - Instala dependencias del sistema (python3, avahi-daemon, etc.)
	- Crea un entorno virtual (venv)
	- Instala dependencias de Python (Flask, requests, etc.)
	- Prepara el directorio de datos en ~/.bitacora/
	- Configura un servicio systemd (bitacora.service)
	- Activa el nombre local: http://bitacora.local:5000

3. Accede a la app desde cualquier dispositivo en la red local: 
      http://bitacora.local:5000
      http://<IP_DE_TU_PI>:5000

4. Configura por primera vez en /setup: 
      Idioma, puerto
      Conexión a Signal K (opcional)
      Copia de seguridad (opcional)


>    Nota: el puerto por defecto es 5000, pero puedes cambiarlo en /setup. 



### Personalización del script 

El script install.sh asume: 

- Repositorio en ~/src/bitacora
- Datos en ~/.bitacora
- Servicio llamado bitacora.service
     

Puedes editarlo si necesitas rutas distintas. 
 
### ¿Y Docker? 

Aunque la arquitectura está preparada, por ahora no se incluye soporte Docker. Se evaluará en futuras versiones. 
