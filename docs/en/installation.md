# 🛠Installation Guide

Logbook is designed to be installed on Linux systems (Raspberry Pi, NUC, etc.) using an automated script.

## Requirements

- Linux system with systemd (Raspbian, Ubuntu, Debian…)
- Python 3.8+
- Terminal access with a regular user account (not root)

## Steps

1. Get the project files. You can do this in two ways: 

    **Option A (recommended if you use Git):**
    ```bash
    git clone https://github.com/Enand-lab/bitacora.git ~/src/bitacora
    ```
    **Option B (without Git, ideal for minimal systems):**
    ```bash
    # 1. Create a folder for the project
    mkdir -p ~/src/bitacora

    # 2. Enter the folder
    cd ~/src/bitacora

    # 3. Download the files directly from GitHub
    wget https://github.com/Enand-lab/bitacora/archive/refs/heads/main.tar.gz

    # 4. Extract the archive
    tar -xzf main.tar.gz --strip-components=1

    # 5. Clean up the downloaded file
    rm main.tar.gz
    ```
    


2. Run the installation script:

```
# Enter the project folder
cd ~/src/bitacora

# Make the script executable
chmod +x install.sh

# Run the installer
./install.sh
```

The script will:

    - Install system dependencies (python3, avahi-daemon, etc.)
    - Create a Python virtual environment (venv)
    - Install Python dependencies (Flask, requests, etc.)
    - Set up the data directory at ~/.bitacora/
    - Configure a systemd service (bitacora.service)
    - Enable local access via: [http://bitacora.local:5000](http://bitacora.local:5000)
3. Access the app from any device on your local network:
    - [http://bitacora.local:5000](http://bitacora.local:5000)
    - or http://<YOUR_PI_IP>:5000
4. Complete initial setup at /setup:
    - Language and port
    - Signal K connection (optional)
    - Backup configuration (optional)

Note: the default port is 5000, but you can change it during or after installation via /setup.

## Customizing the script

The install.sh script assumes:

- Repository in ~/src/bitacora
- Data stored in ~/.bitacora
- Service named bitacora.service

You can edit the script if you need different paths.

## What about Docker?

Although the architecture is Docker-ready, Docker support is not included for now. It may be added in future versions.
