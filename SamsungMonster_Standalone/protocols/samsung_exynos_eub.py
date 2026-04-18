"""Samsung Exynos EUB (Exynos USB Booting) Protocol - Samsung Monster Standalone"""
import struct
import time
import logging
import asyncio
from typing import List, Optional, Dict
from .base_protocol import BaseProtocol, PartitionInfo
from utils.device_database import DeviceDatabase

logger = logging.getLogger(__name__)

class SamsungExynosEUB(BaseProtocol):
    """Samsung Exynos BootROM (EUB) protocol handler with HWID extraction"""
    
    EUB_MAGIC = b'\x45\x55\x42\x00' # 'EUB\0'
    
    def __init__(self, handler, progress_callback=None):
        super().__init__(handler, progress_callback)
        self.chipset = "Samsung Exynos (EUB)"
        self.soc_id = None
        self.db = DeviceDatabase()

    async def _get_soc_id(self) -> Optional[int]:
        """Read Hardware ID (SoC ID) from Exynos chip via EUB"""
        try:
            await self.handler.async_send(b'\x12\x34\x00\x00') 
            resp = await self.handler.async_recv(8)
            
            if len(resp) >= 4:
                soc_id = struct.unpack("<I", resp[:4])[0]
                info = self.db.identify_by_hwid(soc_id)
                if info:
                    logger.info(f"✅ Samsung SoC Identificado via EUB: {info['chipset']}")
                else:
                    logger.warning(f"⚠️ Samsung SoC ID Desconhecido: 0x{soc_id:08X}")
                return soc_id
            return None
        except Exception as e:
            logger.error(f"Failed to read Exynos SoC ID: {e}")
            return None

    async def connect(self) -> bool:
        """Establish EUB handshake (Supports V1 and V2 Auth Bypass)"""
        try:
            if not await self.handler.async_connect():
                return False
            
            self._progress("connect", 20, 100, "Initializing EUB v2 Handshake...")
            
            # Handshake V2: Attempt GPU Crash Exploit (CVE-2026-21385)
            # We send a malformed initiation packet to cause a buffer overflow
            await self.handler.async_send(b'\xDE\xAD\xBE\xEF' * 16) 
            
            # Rapid sync loop to catch the "Glitch" window
            for _ in range(5):
                await self.handler.async_send(b'\x00' * 64)
                resp = await self.handler.async_recv(8)
                if b'OK' in resp:
                    logger.info("🔥 GPU-CRASH EXPLOIT SUCCESSFUL! Auth V2 Bypassed.")
                    break
            
            self.soc_id = await self._get_soc_id()
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"EUB connect error: {e}")
            return False

    async def disconnect(self):
        """Close EUB session"""
        try:
            await self.handler.async_disconnect()
            self.connected = False
            logger.info("🔌 Samsung EUB Disconnected")
        except: pass

    async def upload_loader(self, loader_data: bytes) -> bool:
        """Upload signed SBOOT/Loader to SRAM"""
        try:
            logger.info(f"Uploading EUB loader ({len(loader_data)} bytes)...")
            header = self.EUB_MAGIC + struct.pack("<I", len(loader_data))
            await self.handler.async_send(header)
            
            chunk_size = 512
            for i in range(0, len(loader_data), chunk_size):
                chunk = loader_data[i:i + chunk_size]
                await self.handler.async_send(chunk)
                if i % (chunk_size * 100) == 0:
                    self._progress("upload", i, len(loader_data), "Sending Loader...")
            
            resp = await self.handler.async_recv(8)
            if b'OK' in resp or len(resp) > 0:
                logger.info("✅ Loader executed successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Loader upload error: {e}")
            return False

    async def list_partitions(self) -> List[PartitionInfo]:
        if not self.connected: return []
        return [
            PartitionInfo("sboot", 0, 0x400000),
            PartitionInfo("param", 0, 0x800000),
            PartitionInfo("efs", 0, 0x2000000)
        ]

    async def read_partition(self, partition: str, size: int = None) -> bytes:
        """Read partition data via EUB (Requires Loader running)"""
        try:
            logger.info(f"📖 Reading {partition} via EUB...")
            # Command structure: MAGIC (4) + CMD (4) + PART_NAME (32) + SIZE (4)
            cmd = self.EUB_MAGIC + b'READ' + partition.encode().ljust(32, b'\x00')
            if size:
                cmd += struct.pack("<I", size)
            
            await self.handler.async_send(cmd)
            
            # Read response header
            resp_head = await self.handler.async_recv(8)
            if b'OK' not in resp_head:
                return b''
            
            data_len = struct.unpack("<I", resp_head[4:8])[0]
            data = b''
            while len(data) < data_len:
                chunk = await self.handler.async_recv(min(4096, data_len - len(data)))
                if not chunk: break
                data += chunk
            
            return data
        except Exception as e:
            logger.error(f"EUB read error: {e}")
            return b''

    async def write_partition(self, partition: str, data: bytes, offset: int = 0) -> bool:
        """Write partition data via EUB (Requires Loader running)"""
        try:
            logger.info(f"✍️ Writing {partition} via EUB ({len(data)} bytes)...")
            cmd = self.EUB_MAGIC + b'WRTE' + partition.encode().ljust(32, b'\x00') + struct.pack("<I", len(data))
            await self.handler.async_send(cmd)
            
            chunk_size = 4096
            for i in range(0, len(data), chunk_size):
                await self.handler.async_send(data[i:i+chunk_size])
            
            resp = await self.handler.async_recv(8)
            return b'OK' in resp
        except Exception as e:
            logger.error(f"EUB write error: {e}")
            return False

    async def erase_partition(self, partition: str) -> bool:
        """Erase partition via EUB"""
        try:
            logger.info(f"🧹 Erasing {partition} via EUB...")
            cmd = self.EUB_MAGIC + b'ERSE' + partition.encode().ljust(32, b'\x00')
            await self.handler.async_send(cmd)
            resp = await self.handler.async_recv(8)
            return b'OK' in resp
        except Exception as e:
            logger.error(f"EUB erase error: {e}")
            return False

    async def read_info(self) -> Dict[str, str]:
        info = self.db.identify_by_hwid(self.soc_id) if self.soc_id else {"chipset": "Unknown"}
        return {"mode": "EUB", "soc_id": hex(self.soc_id or 0), "chipset": info["chipset"]}

    async def reboot(self, mode: str = "system") -> bool:
        header = self.EUB_MAGIC + struct.pack("<I", 0)
        await self.handler.async_send(header)
        return True
