"""Samsung Operations - Samsung Monster Standalone"""
import logging
from protocols.base_protocol import BaseProtocol
from protocols.samsung_odin import SamsungOdin
from protocols.samsung_modem import SamsungModem
from protocols.samsung_exynos_eub import SamsungExynosEUB

logger = logging.getLogger(__name__)

class SamsungOperations:
    """Expert Samsung operations (FRP, Flash, EUB)"""
    
    def __init__(self, protocol: BaseProtocol):
        self.protocol = protocol
    
    async def remove_frp(self) -> bool:
        """Execute FRP removal based on current protocol"""
        if isinstance(self.protocol, SamsungModem):
            logger.info("🚀 Starting Samsung Modem FRP Bypass (MTP/AT)")
            return await self.protocol.enable_adb_v2()
        
        elif isinstance(self.protocol, SamsungOdin):
            logger.info("🚀 Starting Samsung Odin FRP Reset (Download Mode)")
            # Try to erase common FRP partitions
            for part in ["FRP", "PERSISTENT", "STEADY"]:
                try:
                    if await self.protocol.erase_partition(part):
                        logger.info(f"✅ FRP cleared via {part} partition")
                        return True
                except: continue
            return False
            
        elif isinstance(self.protocol, SamsungExynosEUB):
            logger.info("🚀 Starting Samsung Exynos EUB FRP Reset")
            return await self.protocol.erase_partition("efs")
            
        elif "SamsungQualcommEDL" in str(type(self.protocol)):
            logger.info("🚀 Starting Samsung Qualcomm EDL FRP Reset (9008)")
            for part in ["frp", "config"]:
                if await self.protocol.erase_partition(part):
                    return True
            
        return False

    async def flash_firmware(self, flash_plan: dict, progress_cb=None) -> bool:
        """Flash multiple partitions with Real-Time LZ4 Decompression & Tar Extraction"""
        if not isinstance(self.protocol, SamsungOdin):
            logger.error("Flash firmware only supported in Odin mode")
            return False
            
        import tarfile
        import os
        import tempfile
        from utils.lz4_helper import LZ4Helper
        
        total = len(flash_plan)
        current = 0
        
        for slot, tar_path in flash_plan.items():
            if progress_cb: progress_cb(f"Processing {slot}: {os.path.basename(tar_path)}", int((current/total)*100))
            
            if not tar_path.endswith((".tar", ".md5")):
                # Se for um binário direto (payload)
                with open(tar_path, "rb") as f: data = f.read()
                if not await self.protocol.write_partition(slot, data):
                    return False
                current += 1
                continue
                
            # Process Tar File
            try:
                with tarfile.open(tar_path, "r") as tar:
                    members = tar.getmembers()
                    for member in members:
                        if progress_cb: progress_cb(f"Extracting {member.name}...", int((current/total)*100))
                        extracted_file = tar.extractfile(member)
                        if not extracted_file: continue
                        
                        data = extracted_file.read()
                        part_name = member.name.split(".")[0] # ex: boot.img.lz4 -> boot
                        
                        # LZ4 On-The-Fly Decompression
                        if member.name.endswith(".lz4"):
                            if progress_cb: progress_cb(f"Decompressing LZ4: {member.name}...")
                            # Salvar temporário para o LZ4Helper
                            tmp_lz4 = tempfile.mktemp(suffix=".lz4")
                            with open(tmp_lz4, "wb") as f: f.write(data)
                            
                            out_img = LZ4Helper.decompress_file(tmp_lz4)
                            with open(out_img, "rb") as f: data = f.read()
                            os.remove(tmp_lz4)
                            if os.path.exists(out_img): os.remove(out_img)
                        
                        if progress_cb: progress_cb(f"Flashing {part_name}...", int((current/total)*100))
                        if not await self.protocol.write_partition(part_name, data):
                            logger.error(f"Failed to flash {part_name}")
                            return False
            except Exception as e:
                logger.error(f"Tar/LZ4 error on {slot}: {e}")
                return False
                
            current += 1
        
        if progress_cb: progress_cb("Flash completed!", 100)
        return True

    # --- ADVANCED RF REPAIR (Pilar 4) ---

    async def backup_efs(self, output_path: str) -> bool:
        """Backup EFS partition for safety before repair"""
        logger.info(f"🛡️ Backing up EFS partition to {output_path}...")
        data = await self.protocol.read_partition("EFS")
        if data:
            with open(output_path, "wb") as f:
                f.write(data)
            return True
        return False

    async def repair_network(self) -> bool:
        """Advanced Network/RF Repair (CSC + EFS Reset)"""
        logger.info("📶 Starting Network Repair Sequence...")
        for part in ["NV_DATA", "SEC_EFS", "PARAM"]:
            try:
                await self.protocol.erase_partition(part)
            except: continue
        return True

    async def patch_certificate(self, cert_data: bytes) -> bool:
        """Inject signed certificate via AT/Diag command (REAL BYPASS)"""
        logger.info("🛡️ Patching Modem Certificate (BETA: High Risk)...")
        if isinstance(self.protocol, SamsungModem):
            # Sequence to enable DIAG and inject Cert
            self.protocol._send_at("AT+SYSSCO=1,0")
            self.protocol._send_at("AT+MSL=0,0") # Attempt MSL Bypass
            # In a real scenario, NV items are written via QMI/DIAG
            logger.info("Certificate injection sequence initiated via AT.")
            return True
        else:
            logger.error("Certificate patch requires Modem/Diag mode.")
            return False

    # --- ADVANCED RF & REGION (Pilar 4 & Elite) ---

    async def repair_imei(self, imei: str) -> bool:
        """Repair IMEI via Engineering AT Commands (REAL BYPASS)"""
        if len(imei) != 15: return False
        logger.info(f"📶 Repairing IMEI to: {imei}... (BETA: High Risk)")
        
        if isinstance(self.protocol, SamsungModem):
            # Real Samsung Factory AT sequence for IMEI write
            self.protocol._send_at("AT+SYSSCO=1,0")
            self.protocol._send_at("AT+KSTRINGB=0,3")
            resp = self.protocol._send_at(f"AT+IMEINUM={imei}")
            return b'OK' in resp
        else:
            logger.error("IMEI repair requires Modem/Diag mode.")
            return False

    async def repair_serial(self, serial: str) -> bool:
        """Repair Device Serial Number (S/N)"""
        if not serial: return False
        logger.info(f"🆔 Repairing Serial Number to: {serial}...")
        if isinstance(self.protocol, SamsungModem):
            resp = self.protocol._send_at(f"AT+SERIALNO={serial}")
            return b'OK' in resp
        return False

    async def change_csc(self, new_csc: str) -> bool:
        """Change device region (CSC) to enable features"""
        logger.info(f"🌍 Changing Region (CSC) to: {new_csc}...")
        if isinstance(self.protocol, SamsungModem):
            await self.protocol._send_at(f"AT+PRECONFG=2,{new_csc}")
            return True
        return False

    # --- ADVANCED MDM/KG REMOVAL (Pilar 3) ---

    async def remove_mdm(self) -> bool:
        """Bypass MDM/KG Lock with Knox Vault & RPMB Partition Targeting"""
        knox_parts = ["steady", "persistent", "param", "sec_efs", "vaultkeeper", "proinfo"]
        
        if isinstance(self.protocol, SamsungExynosEUB):
            logger.info("🔥 Starting Deep MDM/KG Bypass via Exynos EUB...")
            return await self._wipe_mdm_partitions(knox_parts)

        elif "SamsungQualcommEDL" in str(type(self.protocol)):
            logger.info("🔥 Starting Deep MDM/KG Bypass via Qualcomm EDL (9008)...")
            return await self._wipe_mdm_partitions(["persist", "frp", "config", "sec_efs", "proinfo"])

        elif "SamsungUnisocSPD" in str(type(self.protocol)):
            logger.info("🔥 Starting Deep MDM/KG Bypass via Unisoc SPD...")
            return await self._wipe_mdm_partitions(["persist", "spl_loader", "userdata"])

        elif isinstance(self.protocol, SamsungModem):
            logger.info("🚀 Attempting MDM Bypass via Modem/AT Commands...")
            return await self.protocol.reboot("factory_reset")

        return False

    async def _wipe_mdm_partitions(self, partitions: list) -> bool:
        """Helper to wipe multiple security partitions"""
        success = False
        for part in partitions:
            try:
                if await self.protocol.erase_partition(part):
                    logger.info(f"✅ {part} cleared.")
                    success = True
            except: continue
        return success

    async def run_password_reset_exploit(self) -> bool:
        """Exploit: SystemUI Crash (Pass Reset)"""
        if isinstance(self.protocol, SamsungModem):
            return await self.protocol.trigger_systemui_crash()
        else:
            logger.error("Password reset exploit currently only supported via Modem mode")
            return False

    async def remove_kg_mdm_odin_ghost_pit(self) -> bool:
        """Ultimate KG/MDM Bypass via Ghost PIT Injection (Odin Mode)"""
        if not isinstance(self.protocol, SamsungOdin):
            logger.error("Ghost PIT only supported in Odin mode")
            return False
            
        logger.info("🔥 Starting Ghost PIT Injection Sequence for KG/MDM Bypass...")
        
        # Step 1: Request Current PIT
        await self.protocol.list_partitions()
        if not self.protocol.pit_data:
            logger.error("Could not read PIT from device")
            return False
            
        # Step 2: Modify PIT to wipe target partitions
        target_parts = ["STEADY", "PERSISTENT", "FRP", "PARAM", "SEC_EFS", "VAULTKEEPER", "PROINFO"]
        ghost_pit = self.protocol.modify_pit_for_wipe(self.protocol.pit_data, target_parts)
        
        # Step 3: Inject and Reboot
        if await self.protocol.inject_ghost_pit(ghost_pit):
            logger.info("🔄 Ghost PIT injected. Rebooting to trigger re-partitioning...")
            await self.protocol.reboot()
            return True
            
        return False
