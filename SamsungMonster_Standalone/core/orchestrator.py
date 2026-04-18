"""Task Orchestrator - Samsung Monster Standalone"""
import logging
import asyncio
import re
from typing import Optional, Callable, Dict, Any
from .device_manager import DeviceManager
from .enums import ConnectionMode
from drivers.usb_handler import USBHandler
from protocols.samsung_odin import SamsungOdin
from protocols.samsung_exynos_eub import SamsungExynosEUB
from protocols.samsung_modem import SamsungModem
from protocols.samsung_qualcomm_edl import SamsungQualcommEDL
from protocols.samsung_mediatek_brom import SamsungMediaTekBROM
from protocols.samsung_unisoc_spd import SamsungUnisocSPD

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """Orchestrate Samsung operations"""

    def __init__(self, device_manager: DeviceManager):
        self.device_manager = device_manager
        self._abort_requested = False

    def abort(self):
        self._abort_requested = True

    async def get_protocol(self, device_id: str, progress_cb: Optional[Callable] = None):
        device = self.device_manager.get_device(device_id)
        if not device: return None

        handler = USBHandler(device.vendor_id, device.product_id)
        
        if device.mode == ConnectionMode.ODIN:
            return SamsungOdin(handler, progress_cb)
        elif device.mode == ConnectionMode.EUB:
            return SamsungExynosEUB(handler, progress_cb)
        elif device.mode == ConnectionMode.MODEM:
            return SamsungModem(handler, progress_cb)
        elif device.mode == ConnectionMode.EDL:
            return SamsungQualcommEDL(handler, progress_cb)
        elif device.mode == ConnectionMode.BROM:
            return SamsungMediaTekBROM(handler, progress_cb)
        elif device.mode == ConnectionMode.SPD:
            return SamsungUnisocSPD(handler, progress_cb)
        return None

    async def run_frp_bypass(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        self._abort_requested = False
        device = self.device_manager.get_device(device_id)
        if not device: return False

        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False

        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.remove_frp()

    async def run_mdm_bypass(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        """Run MDM/KG Bypass based on current protocol"""
        self._abort_requested = False
        device = self.device_manager.get_device(device_id)
        if not device: return False

        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False

        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.remove_mdm()

    async def run_flash_firmware(self, device_id: str, flash_plan: dict, progress_cb: Optional[Callable] = None) -> bool:
        self._abort_requested = False
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False

        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.flash_firmware(flash_plan, progress_cb)

    async def get_device_full_info(self, device_id: str) -> Dict[str, Any]:
        """Deep identification of Model, Bit and Region"""
        protocol = await self.get_protocol(device_id)
        if not protocol: return {}
        
        async with protocol:
            info = await protocol.read_info()
            device = self.device_manager.get_device(device_id)
            if device:
                info.setdefault("vendor_id", f"0x{device.vendor_id:04x}")
                info.setdefault("product_id", f"0x{device.product_id:04x}")
                info.setdefault("serial", device.serial)
            
            # Use protocol bit if available, otherwise fallback to version parsing
            if not info.get("bit"):
                # Logic to extract Bit from Version string (e.g. S918BXXU3AWF7 -> Bit 3)
                # The bit is usually the 5th character from the end
                version = info.get("version", "")
                if len(version) > 5:
                    info["bit"] = version[-5]

            # Fallback for modes that do not expose model directly (e.g. Odin)
            if not info.get("model") or str(info.get("model")).upper() in {"UNKNOWN", "---"}:
                usb_strings = []
                try:
                    from utils.usb_utils import usb_core, usb_util
                    if device:
                        dev = usb_core.find(idVendor=device.vendor_id, idProduct=device.product_id)
                        if dev:
                            mfg = usb_util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else ""
                            prod = usb_util.get_string(dev, dev.iProduct) if dev.iProduct else ""
                            usb_strings.extend([mfg or "", prod or ""])
                            if mfg:
                                info.setdefault("manufacturer", mfg)
                            if prod:
                                info.setdefault("product", prod)
                except Exception:
                    pass

                if device:
                    usb_strings.append(device.serial or "")

                detected_model = None
                for text in usb_strings:
                    m = re.search(r"\b(SM-[A-Z0-9]+|GT-[A-Z0-9]+|SCH-[A-Z0-9]+)\b", text.upper())
                    if m:
                        detected_model = m.group(1)
                        break

                if detected_model:
                    info["model"] = detected_model
                elif device:
                    info["model"] = f"USB_{device.vendor_id:04X}_{device.product_id:04X}"

            if not info.get("bit"):
                info["bit"] = "-"
            
            info["mode"] = protocol.__class__.__name__.replace("Samsung", "")
            return info

    async def run_auto_repair(self, device_id: str, progress_cb: Optional[Callable] = None, bridge_mode: bool = False) -> bool:
        """One-Click Auto Repair Flow with Smart Downgrade Logic via SamFW"""
        self._abort_requested = False
        info = await self.get_device_full_info(device_id)
        model = str(info.get("model", "UNKNOWN")).strip().upper()
        bit = str(info.get("bit", "")).strip()
        region = info.get("region", "ZTO") # Default to ZTO if not found

        model_ok = re.match(r"^(SM|GT|SCH)-[A-Z0-9]+$", model) is not None
        if not model_ok:
            if progress_cb: progress_cb(f"❌ Auto-Repair requires real model (SM-*/GT-*/SCH-*). Current: {model}")
            return False
        
        if progress_cb: progress_cb(f"Detected Model: {model} (Bit {bit})")
        
        from utils.firmware_fetcher import FirmwareFetcher
        # Expert Strategy: For Downgrade/Bypass, we look for the oldest version with the SAME Bit
        target_bit = bit if bit.isdigit() else None
        fw_info = FirmwareFetcher.get_samfw_firmware(model, region, target_bit=target_bit, bridge_mode=bridge_mode)
        
        if not fw_info:
            if progress_cb: progress_cb(f"❌ No compatible firmware found for {model} (Bit {bit})")
            return False
            
        if progress_cb: progress_cb(f"Found FW: {fw_info['version']} (Bit {fw_info['bit']}) - Initiating Download...")
        
        path = FirmwareFetcher.download_and_extract(fw_info["download_url"], lambda p: progress_cb(p) if progress_cb else None)
        if not path:
            if progress_cb: progress_cb("❌ Download or Extraction failed.")
            return False
        
        flash_plan = FirmwareFetcher.map_extracted_files(path)
        if not flash_plan:
            if progress_cb: progress_cb("❌ No valid flash files found in firmware package.")
            return False
            
        return await self.run_flash_firmware(device_id, flash_plan, progress_cb)

    async def run_reboot(self, device_id: str, mode: str = "system", progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            return await protocol.reboot(mode)

    async def run_ghost_pit_exploit(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        """Run Ghost PIT Injection Exploit for KG/MDM Bypass (Odin)"""
        self._abort_requested = False
        device = self.device_manager.get_device(device_id)
        if not device: return False

        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        
        from protocols.samsung_odin import SamsungOdin
        if not isinstance(protocol, SamsungOdin):
            if progress_cb: progress_cb("Error: Ghost PIT only works in Odin/Download Mode")
            return False

        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.remove_kg_mdm_odin_ghost_pit()

    async def run_hybrid_engine_create(self, comb_tar: str, stock_tar: str, output_path: str, progress_cb: Optional[Callable] = None) -> bool:
        """Create a Hybrid Firmware (Combination Kernel + Stock System)"""
        from utils.combination_helper import CombinationHelper
        import tempfile
        import shutil
        import os
        
        try:
            if progress_cb: progress_cb("🚀 Initializing Hybrid Engine...")
            temp_comb = tempfile.mkdtemp()
            temp_stock = tempfile.mkdtemp()
            
            if progress_cb: progress_cb(f"📦 Extracting Combination: {os.path.basename(comb_tar)}...")
            CombinationHelper.extract_tar(comb_tar, temp_comb)
            
            if progress_cb: progress_cb(f"📦 Extracting Stock: {os.path.basename(stock_tar)}...")
            CombinationHelper.extract_tar(stock_tar, temp_stock)
            
            # Hybrid Map: Keep Stock everything, but replace BOOT with Combination
            partition_map = {}
            for f in os.listdir(temp_stock):
                partition_map[f] = os.path.join(temp_stock, f)
            
            comb_boot = os.path.join(temp_comb, "boot.img")
            if os.path.exists(comb_boot):
                partition_map["boot.img"] = comb_boot
                if progress_cb: progress_cb("🔥 Injected Combination Kernel (boot.img) into Stock Plan")
            
            res = CombinationHelper.create_hybrid_tar(output_path, partition_map)
            
            # Cleanup
            shutil.rmtree(temp_comb)
            shutil.rmtree(temp_stock)
            
            if res and progress_cb: progress_cb(f"✅ Hybrid Firmware created at: {output_path}")
            return res
        except Exception as e:
            if progress_cb: progress_cb(f"❌ Hybrid Engine Error: {e}")
            return False

    async def run_sysui_crash_exploit(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        """Trigger SystemUI Crash via MTP Packet Overload (Pass Reset Exploit)"""
        self._abort_requested = False
        device = self.device_manager.get_device(device_id)
        if not device: return False

        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False

        if progress_cb: progress_cb("🔥 Initializing SystemUI Overload Exploit...")
        
        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.run_password_reset_exploit()

    async def list_partitions(self, device_id: str, progress_cb: Optional[Callable] = None) -> list:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return []
        async with protocol:
            return await protocol.list_partitions()

    async def backup_efs(self, device_id: str, output_path: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.backup_efs(output_path)

    async def repair_network(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.repair_network()

    async def patch_certificate(self, device_id: str, cert_data: bytes, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.patch_certificate(cert_data)

    async def repair_serial(self, device_id: str, serial: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from operations.samsung_ops import SamsungOperations
            ops = SamsungOperations(protocol)
            return await ops.repair_serial(serial)

    async def erase_partition(self, device_id: str, partition: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            return await protocol.erase_partition(partition)

    async def read_partition(self, device_id: str, partition: str, output_path: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            data = await protocol.read_partition(partition)
            if data:
                with open(output_path, "wb") as f:
                    f.write(data)
                return True
            return False

    async def run_edl_flash(self, device_id: str, loader_path: str, flash_plan: dict, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from protocols.samsung_qualcomm_edl import SamsungQualcommEDL
            if not isinstance(protocol, SamsungQualcommEDL): return False
            
            with open(loader_path, "rb") as f: loader_data = f.read()
            if await protocol.upload_programmer(loader_data):
                from operations.samsung_ops import SamsungOperations
                ops = SamsungOperations(protocol)
                return await ops.flash_firmware(flash_plan, progress_cb)
        return False

    async def run_eub_loader(self, device_id: str, loader_path: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from protocols.samsung_exynos_eub import SamsungExynosEUB
            if not isinstance(protocol, SamsungExynosEUB): return False
            
            with open(loader_path, "rb") as f: loader_data = f.read()
            return await protocol.upload_loader(loader_data)
        return False

    async def run_exynos_gpu_crash(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        """Manually trigger the GPU-CRASH (CVE-2026-21385) exploit for V2 Auth Bypass"""
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        
        from protocols.samsung_exynos_eub import SamsungExynosEUB
        if not isinstance(protocol, SamsungExynosEUB):
            if progress_cb: progress_cb("Error: GPU-CRASH only works in Exynos EUB Mode")
            return False
            
        async with protocol:
            if progress_cb: progress_cb("🔥 Triggering GPU-CRASH Exploit (CVE-2026-21385)...")
            # The exploit logic is already in the connect() method of the protocol
            # Calling connect again after a reset will trigger it
            return await protocol.connect()

    async def run_mtk_brom_boot(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from protocols.samsung_mediatek_brom import SamsungMediaTekBROM
            if not isinstance(protocol, SamsungMediaTekBROM): return False
            # BROM is usually the entry point, just connecting triggers handshake
            return True

    async def run_unisoc_boot(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            from protocols.samsung_unisoc_spd import SamsungUnisocSPD
            if not isinstance(protocol, SamsungUnisocSPD): return False
            return True

    async def run_deep_diagnose(self, device_id: str, progress_cb: Optional[Callable] = None) -> dict:
        """Run standalone deep diagnostic logic integrated into orchestrator"""
        device = self.device_manager.get_device(device_id)
        if not device: return {}
        
        try:
            if progress_cb: progress_cb("🔍 Running Hardware Level Deep Diagnosis...")
            import usb.core
            import usb.util
            dev = usb.core.find(idVendor=device.vendor_id, idProduct=device.product_id)
            if not dev: return {"error": "Device lost during scan"}
            
            info = {
                "vendor_id": f"0x{dev.idVendor:04x}",
                "product_id": f"0x{dev.idProduct:04x}",
                "manufacturer": usb.util.get_string(dev, dev.iManufacturer) if dev.iManufacturer else "Unknown",
                "product": usb.util.get_string(dev, dev.iProduct) if dev.iProduct else "Unknown",
                "serial": dev.serial_number or "N/A"
            }
            if progress_cb: progress_cb(f"✅ Diagnosis Complete: {info['product']}")
            return info
        except Exception as e:
            if progress_cb: progress_cb(f"❌ Diagnostic Error: {e}")
            return {"error": str(e)}

    async def run_brute_handshake(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        """Run brute-force Loke handshake loop for secure USB bypass"""
        device = self.device_manager.get_device(device_id)
        if not device: return False
        
        if progress_cb: progress_cb("🔥 Starting Brute-Force Handshake (Loke/Odin Security Bypass)...")
        
        import usb.core
        import usb.util
        dev = usb.core.find(idVendor=device.vendor_id, idProduct=device.product_id)
        if not dev: return False

        try:
            # Low-level access for brute-force
            if dev.is_kernel_driver_active(0): dev.detach_kernel_driver(0)
            dev.set_configuration()
            cfg = dev.get_active_configuration()
            intf = cfg[(0,0)]
            out_ep = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
            in_ep = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

            for i in range(5000): # Limit to 5000 for Elite Bypass
                if self._abort_requested: break
                try:
                    if progress_cb and i % 100 == 0: progress_cb(f"Attempting Handshake {i}/5000...")
                    out_ep.write(b'ODIN', timeout=50)
                    resp = in_ep.read(4, timeout=50)
                    if resp == b'LOKE':
                        if progress_cb: progress_cb(f"✅ SUCCESS! Handshake accepted on attempt {i}")
                        return True
                except:
                    # Timing Attack: Dynamic delays to bypass USB anti-bruteforce mechanisms
                    await asyncio.sleep(0.01 * (i % 3))
                    continue
            
            if progress_cb: progress_cb("❌ Brute-force failed or timed out.")
            return False
        except Exception as e:
            if progress_cb: progress_cb(f"❌ Low-level USB Error: {e}")
            return False

    async def run_force_reboot(self, device_id: str, progress_cb: Optional[Callable] = None) -> bool:
        """Agressive USB reset and reboot command"""
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        async with protocol:
            if progress_cb: progress_cb("🔄 Sending Aggressive Reset Signal...")
            # Simulando lógica de force_reboot.py
            await protocol.handler.async_send(b'\x00' * 32)
            return await protocol.reboot("system")

    async def identify_variant(self, device_id: str, progress_cb: Optional[Callable] = None) -> str:
        """Identify hardware apparel and variant info (Subsidized logic)"""
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return "Unknown"
        async with protocol:
            info = await protocol.read_info()
            # Simulando lógica de identify_apparel.py
            return info.get("chipset", "Standard Device")

    def list_payloads(self) -> list:
        """List available binary payloads in storage"""
        import os
        path = "SamsungMonster_Standalone/storage/payloads"
        if not os.path.exists(path): return []
        return [f for f in os.listdir(path) if f.endswith(('.bin', '.img'))]

    async def inject_payload(self, device_id: str, payload_name: str, partition: str, progress_cb: Optional[Callable] = None) -> bool:
        """Inject a specific payload file into a device partition"""
        import os
        payload_path = os.path.join("SamsungMonster_Standalone/storage/payloads", payload_name)
        if not os.path.exists(payload_path): return False
        
        protocol = await self.get_protocol(device_id, progress_cb)
        if not protocol: return False
        
        with open(payload_path, "rb") as f: data = f.read()
        async with protocol:
            if progress_cb: progress_cb(f"💉 Injecting Payload: {payload_name} into {partition}...")
            return await protocol.write_partition(partition, data)
