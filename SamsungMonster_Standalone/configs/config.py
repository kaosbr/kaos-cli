import os
from typing import Optional

class Settings:
    # Core Metadata
    APP_NAME: str = "Samsung Monster"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Paths
    LOG_DIR: str = "logs"
    BACKUP_DIR: str = "storage/backups"
    PAYLOAD_DIR: str = "storage/payloads"
    FIRMWARE_DIR: str = "storage/firmware"
    
    # Server/Cloud Settings
    SAMFW_BASE: str = "https://samfw.com/firmware"
    MONSTER_DPC_URL: str = "https://monster-tool.com/downloads/monster_dpc.apk"
    MONSTER_DPC_PACKAGE: str = "com.monster.dpc"
    MONSTER_DPC_RECEIVER: str = "com.monster.dpc.MonsterAdminReceiver"
    
    # USB/Serial Timeouts
    USB_TIMEOUT_MS: int = 5000
    SERIAL_BAUDRATE: int = 115200
    
    # API Settings
    SECRET_KEY: str = "SAMSUNG_MONSTER_SECRET_CHANGE_ME"

# Global instance
settings = Settings()

# Ensure directories exist
for path in [settings.LOG_DIR, settings.BACKUP_DIR, settings.PAYLOAD_DIR, settings.FIRMWARE_DIR]:
    os.makedirs(os.path.join("SamsungMonster_Standalone", path), exist_ok=True)
