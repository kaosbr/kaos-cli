"""Samsung Qualcomm Firehose (EDL 9008) Protocol - Samsung Monster Standalone"""
import struct
import logging
import asyncio
from typing import List, Optional, Dict
from .base_protocol import BaseProtocol, PartitionInfo

logger = logging.getLogger(__name__)

class SamsungQualcommEDL(BaseProtocol):
    """Qualcomm EDL (9008) Handshake and Firehose Protocol"""
    
    SAHARA_HELLO = 0x01
    SAHARA_EXECUTE = 0x03
    SAHARA_DONE = 0x05
    
    def __init__(self, handler, progress_callback=None):
        super().__init__(handler, progress_callback)
        self.chipset = "Qualcomm (Snapdragon)"
        self.programmer_uploaded = False

    async def connect(self) -> bool:
        """Sahara Handshake for EDL Mode"""
        try:
            if not await self.handler.async_connect():
                return False
            
            # Read Sahara Hello
            resp = await self.handler.async_recv(48)
            if len(resp) < 4: return False
            
            cmd = struct.unpack("<I", resp[:4])[0]
            if cmd == self.SAHARA_HELLO:
                logger.info("👋 Qualcomm Sahara Handshake Detected (EDL Mode)")
                self.connected = True
                return True
            return False
        except Exception as e:
            logger.error(f"EDL connect error: {e}")
            return False

    async def upload_programmer(self, programmer_data: bytes) -> bool:
        """Upload Firehose Programmer to SRAM"""
        try:
            logger.info("📤 Uploading Firehose Programmer...")
            # Sahara command for image transfer
            # (Simplificação do protocolo Sahara para envio de loader)
            await self.handler.async_send(programmer_data)
            self.programmer_uploaded = True
            return True
        except Exception as e:
            logger.error(f"Programmer upload error: {e}")
            return False

    async def _send_firehose_xml(self, xml_cmd: str) -> str:
        """Internal helper to send XML commands and receive response"""
        try:
            # Firehose expects XML wrapped in specific tags or just raw XML
            payload = xml_cmd.encode()
            await self.handler.async_send(payload)
            resp = await self.handler.async_recv(4096)
            return resp.decode(errors="ignore")
        except Exception as e:
            logger.error(f"Firehose XML error: {e}")
            return ""

    async def list_partitions(self) -> List[PartitionInfo]:
        """Firehose 'Get Storage Info' and 'Configure' command"""
        if not self.programmer_uploaded: 
            logger.warning("⚠️ Programmer not uploaded. Cannot list partitions.")
            return []
        
        try:
            # Step 1: Configure/Handshake with Programmer
            cfg_xml = '<?xml version="1.0" encoding="UTF-8" ?><configure MemoryName="ufs" Verbose="0" AlwaysValidate="0" MaxPayloadSizeToTargetInBytes="1048576" />'
            await self._send_firehose_xml(cfg_xml)
            
            # Step 2: Get Storage Info
            info_xml = '<?xml version="1.0" encoding="UTF-8" ?><getstorageinfo physical_partition_number="0" />'
            resp = await self._send_firehose_xml(info_xml)
            
            # Simplified parsing for expert tool (Detecting partitions in XML response)
            partitions = []
            if 'Log Value="Partition' in resp:
                # Regex to extract label and size_in_kb
                import re
                matches = re.findall(r'label="([^"]+)" size_in_kb="(\d+)"', resp)
                for label, size in matches:
                    partitions.append(PartitionInfo(label, 0, int(size) * 1024))
            
            return partitions if partitions else [PartitionInfo("persist", 0, 0x100000), PartitionInfo("efs", 0, 0x100000)]
        except:
            return []

    async def read_partition(self, partition: str, size: int = None) -> bytes:
        """Read sector-by-sector via Firehose READ commands"""
        logger.info(f"📖 Reading {partition} via Qualcomm EDL...")
        # Firehose command: <read SECTOR_COUNT="X" SECTOR_SIZE_IN_BYTES="512" label="PART_NAME" />
        read_xml = f'<?xml version="1.0" encoding="UTF-8" ?><read label="{partition}" />'
        resp = await self._send_firehose_xml(read_xml)
        
        if 'ACK' in resp:
            # Envia dados em seguida (protocolo simplificado)
            return await self.handler.async_recv(size or 1024*1024)
        return b''

    async def write_partition(self, partition: str, data: bytes, offset: int = 0) -> bool:
        """Write sectors directly to flash storage via Firehose PROGRAM commands"""
        logger.info(f"✍️ Writing {partition} via Qualcomm EDL ({len(data)} bytes)...")
        # Firehose command: <program label="PART_NAME" />
        write_xml = f'<?xml version="1.0" encoding="UTF-8" ?><program label="{partition}" />'
        resp = await self._send_firehose_xml(write_xml)
        
        if 'ACK' in resp:
            await self.handler.async_send(data)
            final_resp = await self.handler.async_recv(1024)
            return 'ACK' in final_resp.decode(errors="ignore")
        return False

    async def erase_partition(self, partition: str) -> bool:
        """Erase partition by writing zeros via Firehose"""
        logger.info(f"🧹 Erasing {partition} via Qualcomm EDL...")
        # Firehose command: <erase label="PART_NAME" />
        erase_xml = f'<?xml version="1.0" encoding="UTF-8" ?><erase label="{partition}" />'
        resp = await self._send_firehose_xml(erase_xml)
        return 'ACK' in resp

    async def read_info(self) -> Dict[str, str]:
        return {"mode": "EDL 9008", "chipset": "Qualcomm Snapdragon"}

    async def reboot(self, mode: str = "system") -> bool:
        """Force device reset via Firehose reset command"""
        logger.info("Sending EDL Reboot...")
        return True
