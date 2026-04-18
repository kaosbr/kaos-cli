"""Samsung Odin Protocol - Samsung Monster Standalone"""
import struct
import time
import logging
import asyncio
from typing import List, Optional, Dict
from .base_protocol import BaseProtocol, PartitionInfo

logger = logging.getLogger(__name__)

class SamsungOdin(BaseProtocol):
    """Advanced Samsung Download Mode (Odin/Loke) handler"""
    
    LZ4_MAGIC = 0x184D2204
    PIT_MAGIC = 0x12345678
    
    def __init__(self, handler, progress_callback=None):
        super().__init__(handler, progress_callback)
        self.chipset = "Samsung"
        self.pit_data = None
        self.partitions_cache = {}
    
    async def connect(self) -> bool:
        """Handshake with modern Samsung bootloaders (Robust Linux Handshake)"""
        try:
            # First attempt: Simple connect
            if not await self.handler.async_connect():
                # Second attempt: Reset USB and try again (Handles "Resource busy")
                await asyncio.sleep(0.5)
                if not await self.handler.async_connect(with_reset=True):
                    return False
            
            self._progress("connect", 30, 100, "Initializing Loke Protocol...")
            
            # Retry loop for initial handshake
            for i in range(3):
                await self.handler.async_send(b'ODIN')
                await asyncio.sleep(0.1) # Timing is critical for Loke
                resp = await self.handler.async_recv(4)
                
                if resp == b'LOKE':
                    self.connected = True
                    logger.info(f"✅ Samsung Loke (Odin Mode) Connected on attempt {i+1}")
                    self._progress("connect", 100, 100, "Connected")
                    return True
                
                logger.debug(f"Handshake retry {i+1}/3... Response: {resp}")
                await asyncio.sleep(0.2)
            
            return False
        except Exception as e:
            logger.error(f"Odin connect error: {e}")
            return False

    async def disconnect(self):
        """Close handler safely without forcing reboot on session close"""
        try:
            if self.connected:
                await self.handler.async_disconnect()
            self.connected = False
            logger.info("🔌 Samsung Odin Disconnected")
        except:
            pass

    async def list_partitions(self) -> List[PartitionInfo]:
        """Request and parse PIT (Partition Information Table)"""
        try:
            logger.info("🔍 Requesting PIT (Partition Information Table)...")
            await self.handler.async_send(b'PIT\x00')
            self.pit_data = await self.handler.async_recv(16384)
            
            if not self.pit_data or len(self.pit_data) < 28:
                return self._fallback_partitions()

            magic = struct.unpack("<I", self.pit_data[:4])[0]
            if magic != self.PIT_MAGIC:
                logger.warning(f"⚠️ Invalid PIT magic: 0x{magic:08x}")

            partitions = []
            entry_count = struct.unpack("<I", self.pit_data[8:12])[0]
            offset = 28
            for i in range(min(entry_count, 128)):
                if offset + 132 > len(self.pit_data): break
                entry = self.pit_data[offset:offset+132]
                name = entry[32:64].split(b"\x00")[0].decode("ascii", errors="ignore").strip()
                if not name:
                    offset += 132
                    continue
                blk_count = struct.unpack("<I", entry[108:112])[0]
                p = PartitionInfo(name, 0, blk_count * 512)
                partitions.append(p)
                self.partitions_cache[name] = p
                offset += 132

            return partitions if partitions else self._fallback_partitions()
        except Exception as e:
            logger.error(f"PIT fetch error: {e}")
            return self._fallback_partitions()

    async def read_partition(self, partition: str, size: int = None) -> bytes:
        logger.warning(f"⚠️ Read operation not supported in Odin Mode for {partition}")
        return b''

    async def write_partition(self, partition: str, data: bytes, offset: int = 0) -> bool:
        """Flash firmware with optimized chunk handling"""
        try:
            if offset == 0:
                logger.info(f"✍️ Initiating Flash: {partition} ({len(data)} bytes)...")
                cmd = struct.pack(">4s32sI", b'DATA', partition.encode().ljust(32, b'\x00'), len(data))
                await self.handler.async_send(cmd)
            
            chunk_size = 131072 # 128KB chunks
            
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                await self.handler.async_send(chunk)
            
            resp = await self.handler.async_recv(4)
            return b'ACK' in resp
        except Exception as e:
            logger.error(f"Odin write error: {e}")
            return False

    async def erase_partition(self, partition: str) -> bool:
        """Erase partition by sending ERSE command or blank data"""
        try:
            logger.info(f"🧹 Erasing Partition: {partition}...")
            # Odin protocol uses 'ERSE' command for modern bootloaders
            cmd = struct.pack(">4s32sI", b'ERSE', partition.encode().ljust(32, b'\x00'), 0)
            await self.handler.async_send(cmd)
            resp = await self.handler.async_recv(4)
            return b'ACK' in resp
        except Exception as e:
            logger.warning(f"Odin erase error for {partition}: {e}")
            # Fallback: write empty data if ERSE is not supported (older Loke)
            return await self.write_partition(partition, b'\x00' * 1024)

    async def read_info(self) -> Dict[str, str]:
        return {"mode": "Odin/Loke", "chipset": "Samsung"}

    async def reboot(self, mode: str = "system") -> bool:
        """Trigger device reboot"""
        try:
            await self.handler.async_send(b'REBT')
            return True
        except: return False

    async def inject_ghost_pit(self, pit_data: bytes) -> bool:
        """Inject a modified PIT table to re-partition and wipe security areas"""
        try:
            logger.info("🔥 Injecting Ghost PIT (Loke Re-partition Exploit)...")
            # To flash PIT, we send 'DATA' with partition name 'PIT'
            success = await self.write_partition("PIT", pit_data)
            if success:
                logger.info("✅ Ghost PIT Accepted! Device will re-partition on next boot.")
            return success
        except Exception as e:
            logger.error(f"Ghost PIT injection failed: {e}")
            return False

    def modify_pit_for_wipe(self, pit_data: bytes, partitions: List[str]) -> bytes:
        """Modify PIT binary to set 'Wipe/Clear' flags for target partitions"""
        if not pit_data or len(pit_data) < 28:
            return b''
        
        modified_pit = bytearray(pit_data)
        entry_count = struct.unpack("<I", pit_data[8:12])[0]
        offset = 28
        
        for i in range(min(entry_count, 128)):
            if offset + 132 > len(modified_pit): break
            
            entry = modified_pit[offset:offset+132]
            name = entry[32:64].split(b"\x00")[0].decode("ascii", errors="ignore").strip()
            
            if name in partitions:
                logger.info(f"📍 Modifying PIT entry for {name} to force wipe...")
                # Offset 4 in entry is 'Partition Flags'
                # Bit 0 often triggers a wipe/format during re-partitioning
                flags = struct.unpack("<I", entry[4:8])[0]
                flags |= 0x01 # Set 'Wipe' flag
                struct.pack_into("<I", modified_pit, offset + 4, flags)
                
            offset += 132
            
        return bytes(modified_pit)

    def _fallback_partitions(self) -> List[PartitionInfo]:
        """Samsung common partitions fallback"""
        parts = [PartitionInfo("FRP", 0, 1024*512), PartitionInfo("PERSISTENT", 0, 1024*1024), PartitionInfo("STEADY", 0, 1024*1024)]
        for p in parts: self.partitions_cache[p.name] = p
        return parts
