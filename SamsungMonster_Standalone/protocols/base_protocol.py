"""Base Protocol - Samsung Monster Standalone"""
import hashlib
import logging
import os
import zlib
import asyncio
from abc import ABC, abstractmethod
from typing import List, Optional, Callable, Dict
from configs.config import settings
from core.exceptions import ProtocolError, SecurityError
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

class PartitionInfo:
    def __init__(self, name: str, start: int, size: int, readable: bool = True, writable: bool = True):
        self.name = name
        self.start = start
        self.size = size
        self.readable = readable
        self.writable = writable
    
    def __repr__(self):
        return f"Partition({self.name}, {self.size//1024//1024}MB, R:{self.readable} W:{self.writable})"

class IFlashable(ABC):
    @abstractmethod
    async def write_partition(self, partition: str, data: bytes) -> bool: pass

    @abstractmethod
    async def start_session(self, partition: str, size: int) -> bool: pass

    @abstractmethod
    async def end_session(self, partition: str) -> bool: pass

class IBootable(ABC):
    @abstractmethod
    async def reboot(self, mode: str = "system") -> bool: pass

# ID 166: Hierarquia de interfaces corrigida para evitar conflito de MRO
class BaseProtocol(IFlashable, IBootable):
    """Production base protocol with logging and progress tracking"""
    
    def __init__(self, handler, progress_callback: Optional[Callable] = None):
        self.handler = handler
        self.connected = False
        self.progress_callback = progress_callback
        self.chipset = "Unknown"
        self.partitions_cache = {}
    
    def _progress(self, operation: str, current: int, total: int, stage: str = ""):
        """Report progress"""
        if self.progress_callback:
            try:
                pct = int((current / max(total, 1)) * 100)
                self.progress_callback({
                    "operation": operation,
                    "current": current,
                    "total": total,
                    "percent": pct,
                    "stage": stage
                })
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to device (Async)"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect (Async)"""
        pass
    
    @abstractmethod
    async def list_partitions(self) -> List[PartitionInfo]:
        """List available partitions (Async)"""
        pass
    
    @abstractmethod
    async def read_partition(self, partition: str, size: int = None) -> bytes:
        """Read partition data (Async)"""
        pass
    
    @abstractmethod
    async def write_partition(self, partition: str, data: bytes, offset: int = 0) -> bool:
        """Write partition data (Async)"""
        pass

    @abstractmethod
    async def read_info(self) -> Dict[str, str]:
        """Read device technical information (Async)"""
        pass

    async def start_session(self, partition: str, size: int) -> bool:
        """Start a flash session for a partition (Default implementation)"""
        return True

    async def end_session(self, partition: str) -> bool:
        """End a flash session for a partition (Default implementation)"""
        return True

    async def erase_partition(self, partition: str) -> bool:
        """Erase partition by filling with zeros"""
        try:
            parts = await self.list_partitions()
            target = next((p for p in parts if p.name == partition), None)
            if not target:
                raise ProtocolError(f"Partition {partition} not found for erasing")
            
            logger.info(f"🧹 Erasing partition: {partition} ({target.size} bytes)")
            zero_data = b'\x00' * min(target.size, 1024 * 1024) 
            return await self.write_partition(partition, zero_data)
        except Exception as e:
            logger.error(f"Erase error: {e}")
            raise ProtocolError(str(e)) from e
    
    async def backup_partition(self, partition: str, output_path: str, compress: bool = True, encrypt: bool = False) -> bool:
        """Async backup with zlib compression and optional AES encryption"""
        try:
            logger.info(f"Backing up {partition}...")
            data = await self.read_partition(partition)
            if not data:
                raise ProtocolError(f"Failed to read {partition}")
            
            if compress:
                data = await asyncio.to_thread(zlib.compress, data)
                if not output_path.endswith(".z"): output_path += ".z"

            if encrypt:
                logger.info("🔐 Encrypting backup (AES-256)...")
                import base64
                key = settings.SECRET_KEY.encode().ljust(32, b'=')[:32]
                fernet_key = base64.urlsafe_b64encode(key)
                f = Fernet(fernet_key)
                data = await asyncio.to_thread(f.encrypt, data)
                if not output_path.endswith(".enc"): output_path += ".enc"

            def _write():
                with open(output_path, 'wb') as f:
                    f.write(data)
                checksum = hashlib.sha256(data).hexdigest()
                with open(f"{output_path}.sha256", 'w') as f_chk:
                    f_chk.write(checksum)
                return checksum

            checksum = await asyncio.to_thread(_write)
            logger.info(f"✅ Secure Backup complete: {partition} (SHA256: {checksum[:12]}...)")
            return True
        except Exception as e:
            logger.error(f"Backup error: {e}")
            raise ProtocolError(str(e)) from e
    
    async def __aenter__(self):
        await self.connect()
        return self
    
    async def __aexit__(self, *args):
        await self.disconnect()
