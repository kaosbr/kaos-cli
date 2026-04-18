"""Samsung MDM/KG QR Provisioning Generator - Samsung Monster Standalone"""
import json
import base64
import hashlib
import qrcode
import os
import threading
import http.server
import socketserver
import socket
from io import BytesIO
from configs.config import settings

def get_local_ip():
    """Get the local network IP address of the host machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

class LocalDPCServer(threading.Thread):
    """Background HTTP server to host the DPC APK locally (Offline Bypass)"""
    def __init__(self, port=8080):
        super().__init__(daemon=True)
        self.port = port

    def run(self):
        web_dir = os.path.join(os.getcwd(), "SamsungMonster_Standalone", "storage", "payloads")
        os.makedirs(web_dir, exist_ok=True)
        
        class QuietHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=web_dir, **kwargs)
            def log_message(self, format, *args): pass # Keep console clean

        try:
            with socketserver.TCPServer(("", self.port), QuietHandler) as httpd:
                httpd.serve_forever()
        except: pass

# Start the offline server immediately when this module is loaded
_dpc_server = LocalDPCServer(port=8080)
_dpc_server.start()

class MDMQRGenerator:
    """Expert tool for creating Enterprise DPC Provisioning QR Codes"""

    @staticmethod
    def get_dpc_url() -> str:
        """Decide whether to use the Local Offline Server or the Cloud Server"""
        payload_path = os.path.join("SamsungMonster_Standalone", "storage", "payloads", "monster_dpc.apk")
        if os.path.exists(payload_path):
            ip = get_local_ip()
            return f"http://{ip}:8080/monster_dpc.apk"
        return settings.MONSTER_DPC_URL

    @staticmethod
    def generate_provisioning_json(
        package_name: str = settings.MONSTER_DPC_PACKAGE,
        checksum: str = "V7_u6Y_7hY8p_Y8pY8pY8pY8pY8pY8pY8pY8pY8pY8p",
        extras: dict = None
    ) -> str:
        """Generate the standard Android Enterprise Provisioning JSON with One UI 8 Support"""
        download_url = MDMQRGenerator.get_dpc_url()
        
        provisioning_data = {
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_COMPONENT_NAME": f"{package_name}/{settings.MONSTER_DPC_RECEIVER}",
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_DOWNLOAD_LOCATION": download_url,
            "android.app.extra.PROVISIONING_DEVICE_ADMIN_PACKAGE_CHECKSUM": checksum,
            "android.app.extra.PROVISIONING_LEAVE_ALL_SYSTEM_APPS_ENABLED": True,
            "android.app.extra.PROVISIONING_SKIP_ENCRYPTION": True,
            "android.app.extra.PROVISIONING_ALLOW_OFFLINE": True, # One UI 8 Offline Bypass
            "android.app.extra.PROVISIONING_KEEP_SCREEN_ON": True,
            "android.app.extra.PROVISIONING_ADMIN_EXTRAS_BUNDLE": extras or {}
        }
        
        return json.dumps(provisioning_data, separators=(',', ':'))

    @staticmethod
    def generate_qr_pixmap_data() -> bytes:
        """Generate QR Code image data in PNG format"""
        json_data = MDMQRGenerator.generate_monster_bypass_string()
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(json_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def save_qr_image(path: str) -> bool:
        """Generate and save QR Code image to file"""
        try:
            json_data = MDMQRGenerator.generate_monster_bypass_string()
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(json_data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            img.save(path, format="PNG")
            return True
        except: return False

    @staticmethod
    def generate_monster_bypass_string() -> str:
        """Pre-configured bypass string for Samsung MDM/KG Removal (One UI 8 Ready)"""
        return MDMQRGenerator.generate_provisioning_json(
            extras={
                "monster_bypass": True,
                "disable_knox": True,
                "disable_mdm": True,
                "enable_adb": True,
                "hide_dpc": True, # Makes the DPC app invisible
                "skip_wifi": True  # Attempt to skip wifi setup if possible
            }
        )
